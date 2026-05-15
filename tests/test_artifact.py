from __future__ import annotations

import json
from datetime import datetime, timezone

from aiteradar.artifact import build_artifact, write_artifact
from aiteradar.classifier import Classifier
from aiteradar.github_client import PullRequestRecord


def test_artifact_contains_summary_and_unclassified(tmp_path) -> None:
    classifier = Classifier.from_package_rules()
    record = PullRequestRecord(
        number=1,
        title="chore",
        html_url="https://github.com/ROCm/aiter/pull/1",
        author="octocat",
        body="",
        state="open_pr",
        opened_at="2026-05-14T00:00:00Z",
        merged_at=None,
        merge_commit_sha=None,
        files=[{"filename": "misc/file.txt", "status": "modified", "additions": 1, "deletions": 0, "changes": 1}],
        commits=[{"sha": "sha1"}],
    )
    classification = classifier.classify_pr(record)

    artifact = build_artifact(
        records=[record],
        classifications={1: classification},
        period_start="2026-05-08",
        period_end="2026-05-15",
        source_repo="ROCm/aiter",
        rule_version=classifier.rule_version,
        generated_at=datetime(2026, 5, 15, 2, 0, tzinfo=timezone.utc),
    )

    assert artifact["summary"]["total_prs"] == 1
    assert artifact["summary"]["total_commits"] == 1
    assert artifact["summary"]["state_counts"]["open_pr"] == 1
    assert artifact["summary"]["label_counts"]["type:misc"] == 1
    assert artifact["summary"]["label_counts"]["open_pr"] == 1
    assert artifact["prs"][0]["state"] == "open_pr"
    assert artifact["prs"][0]["opened_at"] == "2026-05-14T00:00:00Z"
    assert artifact["unclassified"][0]["number"] == 1

    path = write_artifact(artifact, tmp_path)
    assert path.name == "aiteradar_2026-05-08_to_2026-05-15.json"
    assert json.loads(path.read_text(encoding="utf-8"))["generated_at"] == "2026-05-15T02:00:00Z"
