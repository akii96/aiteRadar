"""JSON artifact generation for AiteRadar."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aiteradar.classifier import Classification


FALLBACK_LABELS = {"model:general", "type:misc", "kernel:misc"}
STATE_LABELS = {"merged", "open_pr"}


def build_artifact(
    *,
    records: list[Any],
    classifications: dict[int, Classification],
    period_start: str,
    period_end: str,
    source_repo: str,
    rule_version: int,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated = generated_at or datetime.now(timezone.utc)
    pr_entries = [_pr_entry(record, classifications[record.number]) for record in records]
    label_counts = Counter(label for entry in pr_entries for label in entry["labels"])
    primary_label_counts = Counter(label for entry in pr_entries for label in entry["primary_labels"])
    auxiliary_label_counts = Counter(label for entry in pr_entries for label in entry["auxiliary_labels"])
    total_files = sum(len(entry["changed_files"]) for entry in pr_entries)
    total_commits = sum(len(entry["commit_shas"]) for entry in pr_entries)
    state_counts = Counter(entry["state"] for entry in pr_entries)

    return {
        "generated_at": _iso_z(generated),
        "period_start": period_start,
        "period_end": period_end,
        "source_repo": source_repo,
        "rule_version": rule_version,
        "summary": {
            "total_prs": len(pr_entries),
            "total_commits": total_commits,
            "total_files": total_files,
            "state_counts": dict(sorted(state_counts.items())),
            "label_counts": dict(sorted(label_counts.items())),
            "primary_label_counts": dict(sorted(primary_label_counts.items())),
            "auxiliary_label_counts": dict(sorted(auxiliary_label_counts.items())),
        },
        "prs": pr_entries,
        "unclassified": [
            {
                "number": entry["number"],
                "title": entry["title"],
                "url": entry["url"],
                "labels": entry["labels"],
            }
            for entry in pr_entries
            if (set(entry["labels"]) - STATE_LABELS).issubset(FALLBACK_LABELS)
        ],
    }


def write_artifact(artifact: dict[str, Any], output_dir: str | Path) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    period_start = _filename_date(str(artifact["period_start"]))
    period_end = _filename_date(str(artifact["period_end"]))
    output_path = out_dir / f"aiteradar_{period_start}_to_{period_end}.json"
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def _pr_entry(record: Any, classification: Classification) -> dict[str, Any]:
    return {
        "number": record.number,
        "title": record.title,
        "url": record.html_url,
        "author": record.author,
        "state": record.state,
        "opened_at": record.opened_at,
        "merged_at": record.merged_at,
        "merge_commit_sha": record.merge_commit_sha,
        "changed_files": [_file_entry(file_item) for file_item in record.files],
        "commit_shas": [str(commit.get("sha")) for commit in record.commits if commit.get("sha")],
        "labels": classification.labels,
        "primary_labels": classification.primary_labels,
        "auxiliary_labels": classification.auxiliary_labels,
        "reasons": [reason.to_dict() for reason in classification.reasons],
    }


def _file_entry(file_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "filename": file_item.get("filename"),
        "status": file_item.get("status"),
        "additions": file_item.get("additions", 0),
        "deletions": file_item.get("deletions", 0),
        "changes": file_item.get("changes", 0),
    }


def _iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _filename_date(value: str) -> str:
    return value[:10]
