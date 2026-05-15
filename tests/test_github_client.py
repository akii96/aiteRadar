from __future__ import annotations

import json

from aiteradar.github_client import GitHubClient


def test_search_merged_prs_follows_pagination() -> None:
    calls: list[str] = []

    def transport(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        calls.append(url)
        if "page=2" in url:
            return 200, {}, json.dumps({"items": [{"number": 2, "title": "second"}]}).encode()
        return (
            200,
            {"Link": '<https://api.github.com/search/issues?page=2>; rel="next"'},
            json.dumps({"items": [{"number": 1, "title": "first"}]}).encode(),
        )

    client = GitHubClient(transport=transport)

    items = client.search_merged_prs("2026-05-08", "2026-05-15")

    assert [item["number"] for item in items] == [1, 2]
    assert len(calls) == 2


def test_fetch_weekly_records_includes_files_and_commits() -> None:
    def transport(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        if "/search/issues" in url:
            payload = {"items": [{"number": 10, "title": "Add Kimi GEMM"}]}
        elif url.endswith("/pulls/10"):
            payload = {
                "number": 10,
                "title": "Add Kimi GEMM",
                "html_url": "https://github.com/ROCm/aiter/pull/10",
                "user": {"login": "author"},
                "body": "new kernel",
                "merged_at": "2026-05-14T00:00:00Z",
                "merge_commit_sha": "merge-sha",
            }
        elif url.endswith("/pulls/10/files?per_page=100"):
            payload = [{"filename": "aiter/configs/model_configs/kimik2_bf16_tuned_gemm.csv"}]
        elif url.endswith("/pulls/10/commits?per_page=100"):
            payload = [{"sha": "commit-sha"}]
        else:
            raise AssertionError(f"unexpected URL {url}")
        return 200, {}, json.dumps(payload).encode()

    client = GitHubClient(transport=transport)

    records = client.fetch_weekly_records("2026-05-08", "2026-05-15")

    assert len(records) == 1
    assert records[0].number == 10
    assert records[0].files[0]["filename"].endswith("kimik2_bf16_tuned_gemm.csv")
    assert records[0].commits[0]["sha"] == "commit-sha"
