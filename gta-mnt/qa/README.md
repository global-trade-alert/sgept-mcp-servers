# QA harness

Lightweight gold-standard regression tests for gta-mnt formatters. No DB or network.

## Running

```bash
# Diff current output against checked-in standards; exits 1 on drift
uv run python qa/run_review_format.py

# Overwrite standards (after an intentional format change)
uv run python qa/run_review_format.py --write-standards
```

## Adding a case

1. Drop a JSON fixture into `qa/fixtures/`.
2. Add a `(case, fixture, formatter_fn)` tuple to `CASES` in `run_review_format.py`.
3. Run with `--write-standards` once to seed the standard.
4. Commit both the fixture and the standard.

## What this does and does not cover

**Covers:** markdown formatter output drift. If someone accidentally changes `format_step1_queue` / `format_issue_comment` / `format_measure_detail`, this catches it in CI before it ships to the review agent and confuses the human referee.

**Does not cover:** DB correctness, SQL regressions, MCP protocol-level behaviour, end-to-end review quality. Those need an integration harness against a real (or dockerised) MySQL instance — tracked as a follow-up in CHANGELOG v0.2.0.
