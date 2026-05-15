# AiteRadar

AiteRadar tracks merged PRs in [ROCm/AITER](https://github.com/ROCm/aiter)
and bins them into deterministic labels for weekly JSON changelogs.

It does not use an LLM. Labels come from editable path, title, and body rules in
`src/aiteradar/rules.yaml`.

## Usage

Install locally:

```bash
python -m pip install -e ".[test]"
```

Generate a changelog for the last seven days:

```bash
aiteradar --output-dir changelogs
```

Generate a specific window:

```bash
aiteradar --start 2026-05-08 --end 2026-05-15 --output-dir changelogs
```

Use `GITHUB_TOKEN` or `GH_TOKEN` to raise GitHub API rate limits.

## Output

Each run writes a timestamped JSON file such as:

```text
changelogs/aiteradar_2026-05-18T02-00-00Z.json
```

The artifact includes the query window, label counts, PR metadata, changed
files, commit SHAs, labels, and rule reasons.

## Automation

`.github/workflows/weekly-aiteradar.yml` runs every Monday at 05:00 EEST
(`02:00 UTC`) and can also be triggered manually from GitHub Actions.
