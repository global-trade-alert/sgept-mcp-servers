# QA harness

Lightweight gold-standard regression tests for `dpa-mnt` formatters. No DB, no network.

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

**Covers:** markdown formatter output drift. If someone accidentally changes `format_review_queue`, `format_event_detail`, `format_intervention_context`, `format_source_result`, or one of the comment helpers, this catches it before it ships to the review agent and confuses the human editor.

**Does not cover:** DB correctness, SQL regressions, MCP protocol-level behaviour, end-to-end review quality. Those need an integration harness against a real (or dockerised) MySQL instance — tracked as a follow-up in CHANGELOG v0.2.0.

## Cases

| Case | Fixture | Formatter | What it exercises |
|---|---|---|---|
| `review_queue_empty` | `review_queue_empty.json` | `format_review_queue` | Empty-state markdown |
| `review_queue_small` | `review_queue_small.json` | `format_review_queue` | Two-row table output |
| `event_detail_full` | `event_detail_full.json` | `format_event_detail` | All Phase 2 schema-alignment fields (author, is_current, benchmarks, issues, rationales, agents, sources, comments) |
| `intervention_context_full` | `intervention_context_full.json` | `format_intervention_context` | Published/in-review event timeline + issues + rationales + agents + benchmarks |
| `source_result_pdf` | `source_result_pdf.json` | `format_source_result` | PDF source with extracted content |
| `issue_comment` | `issue_comment.json` | `format_issue_comment` | Canonical issue-comment markdown structure |
