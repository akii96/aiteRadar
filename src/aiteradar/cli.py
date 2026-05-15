"""Command line interface for AiteRadar."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from aiteradar.artifact import build_artifact, write_artifact
from aiteradar.classifier import Classifier
from aiteradar.github_client import GitHubClient


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    start, end = _resolve_window(args.start, args.end)
    classifier = Classifier.from_yaml_file(args.rules) if args.rules else Classifier.from_package_rules()
    client = GitHubClient(repo=args.repo)

    records = client.fetch_weekly_records(start, end)
    classifications = {record.number: classifier.classify_pr(record) for record in records}
    artifact = build_artifact(
        records=records,
        classifications=classifications,
        period_start=start.isoformat(),
        period_end=end.isoformat(),
        source_repo=args.repo,
        rule_version=classifier.rule_version,
    )

    if args.dry_run:
        json.dump(artifact, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    output_path = write_artifact(artifact, args.output_dir)
    print(output_path)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic AITER weekly changelog JSON.")
    parser.add_argument("--repo", default="ROCm/aiter", help="GitHub repo in owner/name form.")
    parser.add_argument("--start", help="Start date in YYYY-MM-DD form. Defaults to 7 days before --end.")
    parser.add_argument("--end", help="End date in YYYY-MM-DD form. Defaults to today in UTC.")
    parser.add_argument("--output-dir", default="changelogs", type=Path, help="Directory for JSON artifacts.")
    parser.add_argument("--rules", type=Path, help="Optional rules YAML path.")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON instead of writing a file.")
    return parser


def _resolve_window(start_arg: str | None, end_arg: str | None) -> tuple[date, date]:
    end = _parse_date(end_arg) if end_arg else datetime.now(timezone.utc).date()
    start = _parse_date(start_arg) if start_arg else end - timedelta(days=7)
    if start > end:
        raise SystemExit("--start must be on or before --end")
    return start, end


def _parse_date(value: str) -> date:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise SystemExit(f"Invalid date {value!r}; use YYYY-MM-DD") from exc


if __name__ == "__main__":
    raise SystemExit(main())
