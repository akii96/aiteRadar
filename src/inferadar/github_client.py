"""Small GitHub REST client for AiteRadar."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.message import Message
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


JsonValue = dict[str, Any] | list[Any]
Transport = Callable[[str, dict[str, str]], tuple[int, Message | dict[str, str], bytes]]


class GitHubClientError(RuntimeError):
    """Raised when GitHub returns an unexpected response."""


@dataclass(frozen=True)
class PullRequestRecord:
    number: int
    title: str
    html_url: str
    author: str
    body: str
    state: str
    opened_at: str
    merged_at: str | None
    merge_commit_sha: str | None
    files: list[dict[str, Any]]
    commits: list[dict[str, Any]]

    @property
    def event_at(self) -> str:
        return self.merged_at if self.state == "merged" and self.merged_at else self.opened_at


def _default_transport(url: str, headers: dict[str, str]) -> tuple[int, Message, bytes]:
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - public GitHub API.
            return response.status, response.headers, response.read()
    except HTTPError as exc:
        raise GitHubClientError(f"GitHub API request failed: {exc.code} {exc.reason}") from exc


class GitHubClient:
    def __init__(
        self,
        repo: str = "ROCm/aiter",
        token: str | None = None,
        transport: Transport = _default_transport,
    ) -> None:
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.transport = transport

    def fetch_weekly_records(self, start: date | datetime | str, end: date | datetime | str) -> list[PullRequestRecord]:
        """Fetch merged and opened PRs, changed files, and commit metadata for a time window."""

        records: list[PullRequestRecord] = []
        for item in self.search_merged_prs(start, end):
            record = self._build_record(item, state="merged")
            if record.merged_at:
                records.append(record)
        for item in self.search_open_prs(start, end):
            records.append(self._build_record(item, state="open_pr"))
        return sorted(records, key=lambda record: (record.event_at, record.number))

    def search_merged_prs(self, start: date | datetime | str, end: date | datetime | str) -> list[dict[str, Any]]:
        start_s = _format_github_date(start)
        end_s = _format_github_date(end)
        query = f"repo:{self.repo} is:pr is:merged merged:{start_s}..{end_s}"
        params = urlencode({"q": query, "sort": "updated", "order": "asc", "per_page": "100"})
        payloads = self._paginate(f"/search/issues?{params}", item_key="items")
        return [item for page in payloads for item in page]

    def search_open_prs(self, start: date | datetime | str, end: date | datetime | str) -> list[dict[str, Any]]:
        start_s = _format_github_date(start)
        end_s = _format_github_date(end)
        query = f"repo:{self.repo} is:pr is:open created:{start_s}..{end_s}"
        params = urlencode({"q": query, "sort": "created", "order": "asc", "per_page": "100"})
        payloads = self._paginate(f"/search/issues?{params}", item_key="items")
        return [item for page in payloads for item in page]

    def get_pull(self, number: int) -> dict[str, Any]:
        return self._get_json(f"/repos/{self.repo}/pulls/{number}")

    def get_pull_files(self, number: int) -> list[dict[str, Any]]:
        pages = self._paginate(f"/repos/{self.repo}/pulls/{number}/files?per_page=100")
        return [item for page in pages for item in page]

    def get_pull_commits(self, number: int) -> list[dict[str, Any]]:
        pages = self._paginate(f"/repos/{self.repo}/pulls/{number}/commits?per_page=100")
        return [item for page in pages for item in page]

    def _build_record(self, item: dict[str, Any], state: str) -> PullRequestRecord:
        number = int(item["number"])
        pull = self.get_pull(number)
        return PullRequestRecord(
            number=number,
            title=str(pull.get("title") or item.get("title") or ""),
            html_url=str(pull.get("html_url") or item.get("html_url") or ""),
            author=str((pull.get("user") or {}).get("login") or ""),
            body=str(pull.get("body") or ""),
            state=state,
            opened_at=str(pull.get("created_at") or item.get("created_at") or ""),
            merged_at=pull.get("merged_at"),
            merge_commit_sha=pull.get("merge_commit_sha") if state == "merged" else None,
            files=self.get_pull_files(number),
            commits=self.get_pull_commits(number),
        )

    def _get_json(self, path_or_url: str) -> JsonValue:
        status, _headers, body = self.transport(self._absolute_url(path_or_url), self._headers())
        if status < 200 or status >= 300:
            raise GitHubClientError(f"GitHub API request failed: HTTP {status}")
        return json.loads(body.decode("utf-8"))

    def _paginate(self, path_or_url: str, item_key: str | None = None) -> list[list[dict[str, Any]]]:
        url = self._absolute_url(path_or_url)
        pages: list[list[dict[str, Any]]] = []
        while url:
            status, headers, body = self.transport(url, self._headers())
            if status < 200 or status >= 300:
                raise GitHubClientError(f"GitHub API request failed: HTTP {status}")
            payload = json.loads(body.decode("utf-8"))
            items = payload[item_key] if item_key else payload
            if not isinstance(items, list):
                raise GitHubClientError("Expected a list response from GitHub pagination")
            pages.append(items)
            url = _next_link(headers)
        return pages

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "inferadar",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _absolute_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("https://"):
            return path_or_url
        return f"{self.base_url}{path_or_url}"


def _format_github_date(value: date | datetime | str) -> str:
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).date().isoformat()
    return value.isoformat()


def _next_link(headers: Message | dict[str, str]) -> str | None:
    link = headers.get("Link") if hasattr(headers, "get") else None
    if not link:
        return None
    for part in link.split(","):
        url_part, _, rel_part = part.partition(";")
        if 'rel="next"' in rel_part:
            return url_part.strip()[1:-1]
    return None
