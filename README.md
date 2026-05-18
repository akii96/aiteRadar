# InfeRadar

InfeRadar tracks merged and newly opened PRs across multiple LLM inference engine repositories
and bins them into deterministic labels for weekly JSON changelogs.

Supported repositories:
- [ROCm/AITER](https://github.com/ROCm/aiter)
- [vllm-project/vllm](https://github.com/vllm-project/vllm)
- [sgl-project/sglang](https://github.com/sgl-project/sglang)
- [ROCm/ATOM](https://github.com/ROCm/ATOM)

It does not use an LLM. Labels come from editable path and title rules in
repository-specific YAML files; PR bodies are intentionally ignored to avoid
over-classifying copied context, checklists, and broad release-note text.

## Usage

Install locally:

```bash
python -m pip install -e ".[test]"
```

Generate changelogs for all configured repos:

```bash
inferadar --repos-config repos.yaml --output-dir changelogs
```

Generate a changelog for a single repo:

```bash
inferadar --repo ROCm/aiter --output-dir changelogs
```

Generate a specific window:

```bash
inferadar --repos-config repos.yaml --start 2026-05-08 --end 2026-05-15 --output-dir changelogs
```

Use `GITHUB_TOKEN` or `GH_TOKEN` to raise GitHub API rate limits.

## Output

Each run writes JSON files organized by time range:

```text
changelogs/
└── 2026-05-11_to_2026-05-18/
    ├── AITER.json
    ├── vllm.json
    ├── sglang.json
    └── ATOM.json
```

Each artifact includes the query window, state counts, primary and auxiliary
label counts, PR metadata, changed files, commit SHAs, labels, and capped rule
reasons. Merged PRs receive the `merged` label; PRs opened during the same
window receive the `open_pr` label.

## Configuration

Repositories are configured in `repos.yaml`:

```yaml
repos:
  - name: AITER
    github: ROCm/AITER
    rules: rules.yaml
  - name: vllm
    github: vllm-project/vllm
    rules: rules-vllm.yaml
```

Each repo can have its own classification rules tailored to its specific patterns.

## Automation

`.github/workflows/weekly-inferadar.yml` runs twice weekly:
- Monday at 06:00 EEST (03:00 UTC)
- Wednesday at 13:00 EEST (10:00 UTC)

Can also be triggered manually from GitHub Actions.
