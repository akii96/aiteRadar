# AiteRadar

AiteRadar tracks merged and newly opened PRs in
[ROCm/AITER](https://github.com/ROCm/aiter) and bins them into deterministic
labels for weekly JSON changelogs.

It does not use an LLM. Labels come from editable path and title rules in
`src/aiteradar/rules.yaml`; PR bodies are intentionally ignored to avoid
over-classifying copied context, checklists, and broad release-note text.

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
changelogs/aiteradar_2026-05-11_to_2026-05-18.json
```

The artifact includes the query window, state counts, primary and auxiliary
label counts, PR metadata, changed files, commit SHAs, labels, and capped rule
reasons. Merged PRs receive the `merged` label; PRs opened during the same
window receive the `open_pr` label.

## Automation

`.github/workflows/weekly-aiteradar.yml` runs every Monday at 05:00 EEST
(`02:00 UTC`) and can also be triggered manually from GitHub Actions.
