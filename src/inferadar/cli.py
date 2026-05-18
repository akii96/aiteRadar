"""Command line interface for InfeRadar."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from inferadar.artifact import build_artifact, write_artifact
from inferadar.classifier import Classifier
from inferadar.github_client import GitHubClient


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    start, end = _resolve_window(args.start, args.end)
    classifier = Classifier.from_yaml_file(args.rules) if args.rules else Classifier.from_package_rules()

    if args.repos_config:
        repos = _load_repos_config(args.repos_config)
        output_paths = []
        for repo_entry in repos:
            repo_name = repo_entry["name"]
            repo_github = repo_entry["github"]
            repo_rules = repo_entry.get("rules")

            repo_classifier = Classifier.from_yaml_file(Path(repo_rules)) if repo_rules else classifier

            artifact = _generate_artifact(
                repo=repo_github,
                start=start,
                end=end,
                classifier=repo_classifier,
            )
            if args.dry_run:
                print(f"=== {repo_name} ({repo_github}) ===")
                json.dump(artifact, sys.stdout, indent=2, sort_keys=True)
                sys.stdout.write("\n\n")
            else:
                output_path = write_artifact(artifact, args.output_dir, repo_name=repo_name)
                output_paths.append(output_path)
                print(output_path)
        return 0
    else:
        artifact = _generate_artifact(
            repo=args.repo,
            start=start,
            end=end,
            classifier=classifier,
        )
        if args.dry_run:
            json.dump(artifact, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0

        output_path = write_artifact(artifact, args.output_dir)
        print(output_path)
        return 0


def _generate_artifact(
    repo: str,
    start: date,
    end: date,
    classifier: Classifier,
) -> dict:
    client = GitHubClient(repo=repo)
    records = client.fetch_weekly_records(start, end)
    classifications = {record.number: classifier.classify_pr(record) for record in records}
    return build_artifact(
        records=records,
        classifications=classifications,
        period_start=start.isoformat(),
        period_end=end.isoformat(),
        source_repo=repo,
        rule_version=classifier.rule_version,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic LLM inference engine changelog JSON.")
    parser.add_argument("--repo", default="ROCm/aiter", help="GitHub repo in owner/name form.")
    parser.add_argument("--repos-config", type=Path, help="YAML file with list of repos to track.")
    parser.add_argument("--start", help="Start date in YYYY-MM-DD form. Defaults to 7 days before --end.")
    parser.add_argument("--end", help="End date in YYYY-MM-DD form. Defaults to today in UTC.")
    parser.add_argument("--output-dir", default="changelogs", type=Path, help="Directory for JSON artifacts.")
    parser.add_argument("--rules", type=Path, help="Optional rules YAML path.")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON instead of writing a file.")
    return parser


def _load_repos_config(config_path: Path) -> list[dict[str, str]]:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config.get("repos", [])


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
