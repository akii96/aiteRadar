from __future__ import annotations

import json

from aiteradar import cli
from aiteradar.github_client import PullRequestRecord


def test_cli_dry_run_outputs_json(monkeypatch, capsys) -> None:
    class FakeClient:
        def __init__(self, repo: str) -> None:
            self.repo = repo

        def fetch_weekly_records(self, start, end):
            return [
                PullRequestRecord(
                    number=42,
                    title="Add MiniMax cache kernel",
                    html_url="https://github.com/ROCm/aiter/pull/42",
                    author="dev",
                    body="new kernel",
                    merged_at="2026-05-14T00:00:00Z",
                    merge_commit_sha="merge",
                    files=[{"filename": "csrc/kernels/cache_kernels.cu"}],
                    commits=[{"sha": "sha"}],
                )
            ]

    monkeypatch.setattr(cli, "GitHubClient", FakeClient)

    exit_code = cli.main(["--start", "2026-05-08", "--end", "2026-05-15", "--dry-run"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["period_start"] == "2026-05-08"
    assert payload["period_end"] == "2026-05-15"
    assert payload["prs"][0]["number"] == 42
    assert "model:minimax" in payload["prs"][0]["labels"]
