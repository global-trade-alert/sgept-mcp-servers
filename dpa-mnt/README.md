# dpa-mnt — DPA Monitoring MCP Server

Internal MCP server for Digital Policy Alert (DPA) Activity Tracker review automation. Drives the **Buzessa Claudini** reviewer persona against the `lux_*` MySQL schema shared with `gtaapi`.

**Status:** v0.2.0 (internal release, 2026-04-22)
**Sibling:** [`gta-mnt`](../gta-mnt) — same architecture, different domain (GTA trade measures).
**Public-facing analogue:** [`sgept-gta-mcp`](../sgept-gta-mcp) — REST-relay, read-only, partner-accessible.

---

## What this does

The DPA editorial team publishes hundreds of digital-policy events per month. Each event needs Step-1 review before it goes live on the DPA Activity Tracker dashboard: does the database entry match the official source? This server is the tool surface a reviewer agent uses to do that work without logging into the dashboard UI.

MNT's read paths return exactly the fields the dashboard's `InterventionSerializer` and `EventSerializer` return (with deliberate, documented divergences — see [`CLAUDE.md`](CLAUDE.md)). A reviewer using MNT should never have to tab back to the dashboard for a missing attribute.

## Tools

| Tool | Purpose |
|---|---|
| `dpa_mnt_list_review_queue` | List events in status 2 (Step 1 Review / AT), most recent first |
| `dpa_mnt_get_event` | Full event + intervention + author + sources + benchmarks + comments |
| `dpa_mnt_get_intervention_context` | **Gate 0** — all sibling events on the intervention, published context + in-review |
| `dpa_mnt_get_source` | Fetch official source, extract PDF/HTML text, persist to disk |
| `dpa_mnt_add_comment` | Write a structured review comment to `api_comment_log` |
| `dpa_mnt_set_status` | Write review verdict — AT: Revised / Under Revision / Concern / Archived (6 / 5 / 4 / 14) |
| `dpa_mnt_add_review_tag` | Idempotently apply BC-review issue tag (83) to the intervention |
| `dpa_mnt_list_templates` | List available comment templates from `api_comment_template_list` |
| `dpa_mnt_log_review` | Write a structured review-log artifact to disk |
| `dpa_mnt_lookup_analysts` | Look up which analyst created each of a batch of events |

v0.2.0 is review-only. Entry-creation tools for the Buzetta Claudini author persona are tracked for v0.3.

## Architecture

```
MCP host (internal review agent)
    |
 MCP stdio
    |
FastMCP Server (server.py)
    ├── 10 tools, strict Pydantic inputs, ToolError routing
    ├── CHARACTER_LIMIT (100,000) truncation + pagination hints
    ├── 5 MCP resources under dpa-mnt://
    └── handlers wrap pymysql calls in asyncio.to_thread
            │                                        │
            ▼                                        ▼
    ┌────────────────────┐               ┌─────────────────────────┐
    │ DPA MySQL          │               │ $DPA_MNT_REVIEW_STORAGE │
    │ (lux_* + api_*)    │               │   _PATH/<intervention>/ │
    │ via pymysql        │               │     evt-<e>-*.{pdf,md}  │
    └────────────────────┘               └─────────────────────────┘
```

## Installation

See [`QUICKSTART.md`](QUICKSTART.md) for the full setup walkthrough. TL;DR:

```bash
cd dpa-mnt
uv sync --all-extras --dev
export GTA_DB_HOST=... GTA_DB_PASSWORD_WRITE=...
uv run dpa-mnt
```

## Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GTA_DB_HOST` | yes | — | RDS host for the `gtaapi` DB |
| `GTA_DB_NAME` | no | `gtaapi` | Schema name |
| `GTA_DB_PORT` | no | `3306` | |
| `GTA_DB_USER_WRITE` | no | `GTA_DB_USER` or `gtaapi` | Write-capable user |
| `GTA_DB_PASSWORD_WRITE` | yes | `GTA_DB_PASSWORD` | — |
| `DPA_MNT_REVIEW_STORAGE_PATH` | no | `~/.dpa-mnt/bc-reviews` | Persistent audit trail root |

## Canonical review flow (Buzessa Claudini, user_id 9902)

1. **`dpa_mnt_list_review_queue`** — pick an `event_id` in status 2.
2. **`dpa_mnt_get_intervention_context(intervention_id)`** — Gate 0 lifecycle / consistency check against published siblings.
3. **`dpa_mnt_get_event(event_id)`** — full event detail, including author, benchmarks, issues, rationales, agents, sources.
4. **`dpa_mnt_get_source(event_id, source_index=0)`** — extract primary source text; writes to disk at `<intervention_id>/evt-<event_id>-source.{pdf|html|txt}`.
5. Field-by-field scan against `resources/review_criteria.md`.
6. Per issue found: **`dpa_mnt_add_comment`** with `format_issue_comment` output.
7. **`dpa_mnt_add_review_tag(event_id)`** — applies issue 83 to the intervention (idempotent).
8. **`dpa_mnt_set_status(event_id, new_status_id=6|5|4|14)`** — PASS / CONDITIONAL / FAIL-critical / FAIL-out-of-scope (AT: Revised / Under Revision / Concern / Archived).
9. **`dpa_mnt_log_review(...)`** — writes `evt-<event_id>-review-log.md` to the storage path.

## Status IDs

| ID | Name | Who sets it | Verdict |
|----|------|-------------|---------|
| 1 | In Progress | Author | — |
| 2 | Step 1 Review (AT) | Author (handoff) | — |
| 3 | Publishable (legacy) | Not written by modern reviews | — |
| 4 | AT: Concern | Reviewer | FAIL (critical) |
| 5 | AT: Under Revision | Reviewer | CONDITIONAL |
| 6 | AT: Revised | Reviewer | PASS |
| 7 | Published | Editorial (not MNT) | — |
| 14 | Archived | Reviewer | FAIL (out of scope) |

`SetStatusInput.new_status_id` is `{1,2,3,4,5,6,7,14}`; anything else is rejected. Note `6` has opposite meaning on GTA (Under revision / FAIL) — the agent must not cross-wire.

## Testing

```bash
uv run pytest                                          # 68 unit tests, ~0.3s
uv run pytest --cov=dpa_mnt --cov-report=term-missing  # coverage
uv run python qa/run_review_format.py                  # formatter gold-standard regression
```

Coverage breakdown:
- `storage.py`: 100%
- `source_fetcher.py`: 93%
- `formatters.py`: 75%
- `api.py`: 10% (DB-bound; integration tests deferred to v0.3)

## Schema alignment with the DPA Dashboard

Authoritative surface: `gtaapi/lux/serializers.py` on the `development` branch, specifically:
- `InterventionSerializer` (line 1649)
- `EventSerializer` (line 4030)

MNT returns every field these serializers expose, flattened for LLM consumption. Intentional divergences are documented in [`CLAUDE.md`](CLAUDE.md) § "Schema alignment with the DPA Dashboard".

## File layout

```
dpa-mnt/
├── src/dpa_mnt/
│   ├── server.py, api.py, formatters.py, storage.py,
│   ├── source_fetcher.py, constants.py, models.py, resources_loader.py
├── resources/               # 5 markdown files served under dpa-mnt://
├── qa/                      # gold-standard formatter regression harness
├── tests/unit/              # 68 unit tests
├── CLAUDE.md, CHANGELOG.md, QUICKSTART.md, README.md
├── pyproject.toml, pytest.ini, uv.lock
```

## Contributing

This is an internal tool. Changes follow the Keep-a-Changelog convention in [`CHANGELOG.md`](CHANGELOG.md). Any behavior change needs:

1. A unit test exercising the new behavior (and a QA standard if it's a formatter change).
2. A `CHANGELOG.md` entry under `## [Unreleased]`.
3. `uv run pytest` green on CI (`.github/workflows/dpa-mnt-tests.yml`).

## Troubleshooting

See [`QUICKSTART.md`](QUICKSTART.md) § Troubleshooting for common failures (missing env vars, invalid status IDs, source index out of range, storage permissions).

## License

Internal use only. Not published to PyPI. Not for external distribution.
