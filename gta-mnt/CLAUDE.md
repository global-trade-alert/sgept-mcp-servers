# Claude Code Configuration — gta-mnt

Agent-facing context for the gta-mnt MCP server. User-facing docs live in `README.md`.

## Purpose

Internal MCP server driving two automation personas against the Global Trade Alert MySQL database:

- **Sancho Claudino** (user_id **9900**) — REVIEWER. Authors review comments, sets review status, attaches review framework tags. Used by quality-review tools. **NEVER** used for entry creation.
- **Sancho Claudito** (user_id **9901**) — AUTHOR. Creates new state acts, interventions, and all associated data (implementing jurisdictions, products, sectors, firms, sources, etc.). **NEVER** used for review operations.

**Hard invariant.** These personas must never be mixed. A reviewer must not appear as the author of the entry they might later review — that corrupts the audit trail. The separation is enforced in `constants.py` (`SANCHO_REVIEWER_ID`, `SANCHO_AUTHOR_ID`) and threaded through every DB-writing method in `api.py`. When reviewing or extending tools: do not change which user ID a tool writes with.

Unlike `sgept-gta-mcp` (public-facing, read-only, REST relay), this server:
- Hits MySQL directly with `pymysql` (blocking) wrapped in `asyncio.to_thread` at the handler boundary.
- Writes to disk on every review touch (audit trail in `$GTA_MNT_REVIEW_STORAGE_PATH`).
- Exposes write tools restricted to internal users.
- Has no OAuth / public auth story — credentials come from env vars.

## Project structure

```
gta-mnt/
├── src/gta_mnt/
│   ├── server.py          # FastMCP server, 23 tools, strict Pydantic inputs
│   ├── api.py             # GTADatabaseClient (sync, pymysql) + BastiatAPIClient (async, httpx)
│   ├── formatters.py      # Markdown rendering + CHARACTER_LIMIT truncation helper
│   ├── storage.py         # ReviewStorage — per-measure disk audit trail
│   ├── source_fetcher.py  # S3 → URL → PDF/HTML extraction, auto-saves via storage
│   ├── auth.py            # JWTAuthManager (retained for future API reuse; not used by DB path)
│   ├── constants.py       # User IDs, framework IDs, lookup table map, storage path (env-var'd)
│   ├── models.py          # Legacy Pydantic models (output types still used; input types are dead — see Known drift)
│   └── cli.py             # Thin CLI wrapper
├── resources/             # MCP resources (review criteria, status decision tree, etc.)
├── qa/                    # Lightweight gold-standard eval harness
├── tests/unit/            # pytest, pytest-asyncio
├── CHANGELOG.md           # Keep-a-Changelog
├── CLAUDE.md              # this file
├── README.md              # user-facing
└── pyproject.toml         # uv, dependency-groups for dev deps
```

## Architecture

```
MCP host (internal review agent)
    |
 MCP stdio
    |
FastMCP Server (server.py)
    ├── 23 tools (review + entry creation + lookup + HS-guess)
    ├── Strict Pydantic inputs (extra='forbid', str_strip_whitespace, validate_assignment)
    ├── ToolError on expected failures (unknown framework, source out of range, missing API key, Bastiat timeout)
    ├── CHARACTER_LIMIT (100_000) truncation with pagination hints in formatters
    └── handlers wrap pymysql in asyncio.to_thread
            │                        │                       │
            ▼                        ▼                       ▼
    ┌────────────────┐       ┌──────────────┐        ┌─────────────┐
    │ GTA MySQL      │       │ S3 (sources) │        │ Bastiat API │
    │ (read + write) │       │ (via boto3)  │        │ (httpx)     │
    └────────────────┘       └──────────────┘        └─────────────┘
                                    │
                                    ▼
                       ┌──────────────────────────┐
                       │ $GTA_MNT_REVIEW_STORAGE_ │
                       │ PATH / <state_act_id> /  │
                       │  source.{pdf|html|txt}   │
                       │  source-url.txt          │
                       │  comments.md             │
                       │  review-log.md           │
                       └──────────────────────────┘
```

## Tools (23)

### Review tools (Sancho Claudino, 9900) — 10
`gta_mnt_list_step1_queue`, `gta_mnt_list_step2_queue`, `gta_mnt_list_queue_by_status`, `gta_mnt_get_measure`, `gta_mnt_get_source`, `gta_mnt_add_comment`, `gta_mnt_set_status`, `gta_mnt_add_framework`, `gta_mnt_list_templates`, `gta_mnt_log_review`.

### Entry creation (Sancho Claudito, 9901) — 11
`gta_mnt_create_state_act`, `gta_mnt_create_intervention`, `gta_mnt_add_ij`, `gta_mnt_add_product`, `gta_mnt_add_sector`, `gta_mnt_add_rationale`, `gta_mnt_add_firm`, `gta_mnt_add_source`, `gta_mnt_queue_recalculation`, `gta_mnt_add_level`, `gta_mnt_add_motive_quote`.

### Lookup — 2
`gta_mnt_lookup` (16 reference tables, substring match), `gta_mnt_guess_hs_codes` (Bastiat semantic AI match).

## Status IDs (review state machine)

| ID | Name | Meaning |
|----|------|---------|
| 1 | In progress | Newly created by author; draft in progress |
| 2 | Step 1 | Awaiting initial review |
| 3 | Publishable | Passed review |
| 6 | Under revision | Issues found, sent back |
| 19 | Step 2 | Awaiting second-stage review |

`SetStatusInput.new_status_id` is validated against this exact set. Any other integer raises a `ValidationError` with a message listing the four valid values.

## Framework IDs

| ID | Name | Meaning |
|----|------|---------|
| 495 | `sancho claudino review` | Reviewed by Sancho Claudino |
| 500 | `sancho claudito reported` | First-drafted by Sancho Claudito |

`add_framework` rejects unknown framework names with `ToolError` before hitting the DB.

## Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GTA_DB_HOST` | yes | AWS RDS host | `main()` exits if unset |
| `GTA_DB_NAME` | no | `gtaapi` | |
| `GTA_DB_PORT` | no | `3306` | |
| `GTA_DB_USER_WRITE` | no | `GTA_DB_USER` → `gtaapi` | |
| `GTA_DB_PASSWORD_WRITE` | yes | `GTA_DB_PASSWORD` | `main()` exits if unset |
| `GTA_MNT_REVIEW_STORAGE_PATH` | no | `~/.gta-mnt/sc-reviews` | Point at persistent volume in deploy |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION` | for `gta_mnt_get_source` on S3 sources | | |
| `GTA_API_KEY` | for `gta_mnt_guess_hs_codes` only | | Bastiat API key |

## Response formatting rules

1. All tool outputs are markdown-native; no bespoke JSON envelope.
2. Every response-building formatter (`format_step1_queue`, `format_measure_detail`, `format_source_result`) passes through `formatters._truncate(...)`. Responses over `CHARACTER_LIMIT = 100_000` get a tail marker that names the specific smaller payload the agent can re-request (`offset=...`, `include_interventions=False`, etc.).
3. When you see `*None recorded*` in a measure detail, that means the DB was queried and returned nothing. Do not claim data exists. (The constraint is in the measure-detail formatter and should be read as a hard rule.)
4. Dataset links and source URLs should be preserved verbatim in any downstream summary — they are the agent's single route back to ground truth.

## Key design patterns

- **Lazy singletons.** `get_db_client()` and `get_source_fetcher()` create a single instance per process on first call. Do not replace this with constructor injection per-tool — the DB connection reuse matters for warm-path latency.
- **Dependency injection into storage.** `GTADatabaseClient.__init__` and `SourceFetcher.__init__` accept a `ReviewStorage` instance so tests can redirect disk writes to `tmp_path`.
- **Two-role user model.** Enforced in `api.py` — do not plumb a user_id parameter through MCP tools. The persona is determined by the tool, not by caller input.
- **Blocking DB wrapped, not refactored.** Every `async def` handler in `server.py` wraps `db_client.<method>` in `asyncio.to_thread`. DB client methods are sync (`def`) and must stay sync until the full asyncmy migration (tracked in CHANGELOG v0.2.0 follow-up).
- **Input strictness.** All MCP input models inherit from `_StrictInput` (in `server.py`) which sets `extra='forbid'` — this catches LLM field-name drift (`status_id` vs `new_status_id`, `measure_id` vs `state_act_id`) with a clear ValidationError instead of silently ignoring the bad field.
- **ToolError for expected failures.** Missing API key, unknown framework name, source_index out of range, Bastiat timeout. Unexpected failures (DB connection lost, boto3 credential error) surface as stack traces — do not catch them.

## Testing

```bash
uv run pytest                                  # unit tests
uv run pytest --cov=gta_mnt --cov-report=term-missing
```

The legacy `tests/unit/test_api.py` was retired in v0.2.0 — it tested an old `GTAAPIClient` REST relay that no longer exists. Integration tests hitting a real MySQL instance are tracked as a Linear follow-up.

## Known drift

- `src/gta_mnt/models.py` contains a set of input models (`Step1QueueInput`, `GetMeasureInput`, etc.) that predate the server.py inline models. Nothing imports the input models from `models.py` anymore; only the output types (`SourceResult`, `CommentResult`, etc.) are still referenced. Safe to delete the input-model classes in `models.py` during a future cleanup; kept for now to minimise diff.
- `auth.py` (`JWTAuthManager`) is unused by the direct-MySQL path. It is retained for any future REST-API tool that needs it. Do not remove without checking `source_fetcher.py` and any new tools added since v0.2.0.

## Entry point

```toml
[project.scripts]
gta-mnt = "gta_mnt.server:main"
```

`main()` fails fast if `GTA_DB_HOST` or `GTA_DB_PASSWORD_WRITE` are unset, then calls `mcp.run()` on the FastMCP stdio transport.
