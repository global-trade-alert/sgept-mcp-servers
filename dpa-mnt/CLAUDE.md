# Claude Code Configuration — dpa-mnt

Agent-facing context for the `dpa-mnt` MCP server. User-facing docs live in `README.md`.

## Purpose

Internal MCP server driving two automation personas against the Digital Policy Alert `lux_*` schema in MySQL:

- **Buzessa Claudini** (user_id **9902**) — REVIEWER. Authors review comments, sets review status, applies the BC-review issue tag to reviewed interventions. Used by quality-review tools. **NEVER** used for entry creation.
- **Buzetta Claudini** (user_id **9903**) — AUTHOR. Creates new events, interventions, sources, relations, and agents (v0.3+). **NEVER** used for review operations.

**Hard invariant.** These personas must never be mixed. A reviewer must not appear as the author of the entry they might later review — that corrupts the audit trail. The separation is enforced in `constants.py` (`BUZESSA_REVIEWER_ID`, `BUZETTA_AUTHOR_ID`) and the comment / status / tag tools always write with 9902. When reviewing or extending tools: do not change which user ID a tool writes with.

Unlike `sgept-gta-mcp` (public-facing, read-only, REST relay), this server:
- Hits MySQL directly with `pymysql` (blocking) wrapped in `asyncio.to_thread` at the handler boundary.
- Writes to disk on every review touch (audit trail in `$DPA_MNT_REVIEW_STORAGE_PATH`, organised by intervention with per-event file prefixes).
- Exposes write tools restricted to the two internal users.
- Has no OAuth / public auth story — credentials come from env vars.

Unlike the sibling `gta-mnt`, this server:
- Targets DPA's event-centric `lux_*` schema (not GTA's state-act / intervention schema).
- Uses a different valid-status set: `{1, 2, 3, 4, 5, 7}` instead of GTA's `{1, 2, 3, 6, 19}`. The validator rejects cross-wired IDs.
- Uses an issue tag (`BC_REVIEW_ISSUE_ID = 83`) to mark reviewed interventions rather than a framework tag.
- Does not implement S3 via boto3 — all DPA sources are HTTP URLs (whether `source_url` on the public web or `file_url` on an HTTP-accessible S3 archive).
- Does not yet ship entry-creation tools; v0.2.0 is review-only. Author-side tools are tracked for v0.3.

## Project structure

```
dpa-mnt/
├── src/dpa_mnt/
│   ├── server.py            # FastMCP server, 9 tools, strict Pydantic inputs, @mcp.resource() registrations
│   ├── api.py               # DPADatabaseClient (sync, pymysql) — all DB reads/writes
│   ├── formatters.py        # Markdown rendering + CHARACTER_LIMIT truncation helper
│   ├── storage.py           # ReviewStorage — intervention-scoped, event-prefixed disk audit trail
│   ├── source_fetcher.py    # URL primary / file_url fallback, PDF/HTML extraction, auto-saves via storage
│   ├── constants.py         # User IDs, issue ID, valid status set, storage path (env-var'd)
│   ├── models.py            # Output shapes (SourceResult, CommentResult) only
│   └── resources_loader.py  # Loads markdown resources served under dpa-mnt://
├── resources/               # MCP resources (review criteria, status decision tree, etc.)
├── qa/                      # Gold-standard formatter regression harness
├── tests/unit/              # pytest, pytest-asyncio, pytest-cov
├── CHANGELOG.md             # Keep-a-Changelog
├── CLAUDE.md                # this file
├── QUICKSTART.md            # install + first tool call
├── README.md                # user-facing
├── pyproject.toml           # uv, dependency-groups for dev deps
└── pytest.ini
```

## Architecture

```
MCP host (internal DPA review agent)
    |
 MCP stdio
    |
FastMCP Server (server.py)
    ├── 9 tools (review only — author tools are v0.3)
    ├── Strict Pydantic inputs (extra='forbid', str_strip_whitespace, validate_assignment)
    ├── new_status_id validator ({1,2,3,4,5,7})
    ├── ToolError on expected failures (event not found, source OOB, DB failure bubbles)
    ├── CHARACTER_LIMIT (100_000) truncation with pagination hints in formatters
    ├── 5 MCP resources under dpa-mnt:// URI scheme
    └── handlers wrap pymysql calls in asyncio.to_thread
            │                                        │
            ▼                                        ▼
    ┌────────────────────┐               ┌─────────────────────────┐
    │ DPA MySQL (lux_*)  │               │ $DPA_MNT_REVIEW_STORAGE │
    │ (read + write)     │               │ _PATH/<intervention_id>/│
    │                    │               │   evt-<e>-source.{...}  │
    │ lux_event_log      │               │   evt-<e>-source-url.txt│
    │ lux_intervention_  │               │   evt-<e>-comments.md   │
    │ lux_event_source   │               │   evt-<e>-review-log.md │
    │ lux_event_status_  │               └─────────────────────────┘
    │ lux_event_agent    │
    │ lux_intervention_  │
    │   benchmark_log    │
    │ gta_lead_benchmark │
    │ api_comment_log    │
    │ auth_user          │
    └────────────────────┘
```

## Tools (9)

### Review (Buzessa Claudini, 9902)
`dpa_mnt_list_review_queue`, `dpa_mnt_get_event`, `dpa_mnt_get_intervention_context`, `dpa_mnt_get_source`, `dpa_mnt_add_comment`, `dpa_mnt_set_status`, `dpa_mnt_add_review_tag`, `dpa_mnt_list_templates`, `dpa_mnt_log_review`, `dpa_mnt_lookup_analysts`.

The canonical review flow:

1. `dpa_mnt_list_review_queue` → pick an event_id with `status_id = 2`.
2. `dpa_mnt_get_intervention_context(intervention_id)` — **Gate 0**, mandatory lifecycle/consistency check against published siblings.
3. `dpa_mnt_get_event(event_id)` — full event + intervention + sources + author + benchmarks.
4. `dpa_mnt_get_source(event_id, source_index=0)` — primary source text.
5. Per finding: `dpa_mnt_add_comment` (issue / verification / review-complete).
6. `dpa_mnt_set_status(event_id, new_status_id=...)` — 3 Publishable, 4 Concern, 5 Under revision.
7. `dpa_mnt_add_review_tag(event_id)` — applies issue 83 (BC review) to the intervention.
8. `dpa_mnt_log_review(...)` — on-disk audit artifact.

## Status IDs (DPA event state machine)

| ID | Name | Notes |
|----|------|-------|
| 1 | In Progress | Draft; author still working |
| 2 | Step 1 Review (AT) | Handed off; in the review queue |
| 3 | Publishable (PASS) | Reviewer verdict |
| 4 | Concern (CONDITIONAL / ESCALATION) | Reviewer verdict |
| 5 | Under Revision (FAIL) | Reviewer verdict |
| 7 | Published | Editorial step; not written by MNT |

`SetStatusInput.new_status_id` is validated against this exact set. Any other integer (including GTA's `6` or `19`) raises a `ValidationError` with a message listing every valid id=name pair.

## Issue IDs

| ID | Name | Purpose |
|----|------|---------|
| 83 | BC review | Applied to the intervention after any completed review (PASS, CONDITIONAL, or FAIL). Idempotent. |

Framework ID `496` (`dpa review`) is deprecated — do not write new rows. See `issue_ids.md`.

## Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GTA_DB_HOST` | yes | RDS host | `main()` exits if unset |
| `GTA_DB_NAME` | no | `gtaapi` | DPA schema lives in the same DB |
| `GTA_DB_PORT` | no | `3306` | |
| `GTA_DB_USER_WRITE` | no | `GTA_DB_USER` → `gtaapi` | |
| `GTA_DB_PASSWORD_WRITE` | yes | `GTA_DB_PASSWORD` | `main()` exits if unset |
| `DPA_MNT_REVIEW_STORAGE_PATH` | no | `~/.dpa-mnt/bc-reviews` | Point at persistent volume in deploy |

## MCP resources

Served under the `dpa-mnt://` URI scheme:

| URI | Markdown file | Purpose |
|---|---|---|
| `dpa-mnt://review-criteria` | `review_criteria.md` | Minimum field surface + criticality rubric + verdict mapping |
| `dpa-mnt://status-id-decision-tree` | `status_id_decision_tree.md` | When to use each of the six valid status IDs |
| `dpa-mnt://comment-templates` | `comment_templates.md` | Issue / verification / review-complete structures |
| `dpa-mnt://issue-ids` | `issue_ids.md` | BC review tag (83) + thematic tag vocabulary |
| `dpa-mnt://source-extraction-notes` | `source_extraction_notes.md` | PDF / HTML / S3 gotchas for `dpa_mnt_get_source` |

## Response formatting rules

1. All tool outputs are markdown-native; no bespoke JSON envelope.
2. Every response-building formatter (`format_review_queue`, `format_event_detail`, `format_intervention_context`, `format_source_result`) passes through `formatters._truncate(...)`. Responses over `CHARACTER_LIMIT = 100_000` get a tail marker that names the specific smaller payload the agent can re-request (`offset=...`, `include_intervention=False`, `fetch_content=False`).
3. `is_current: No` on an event is meaningful — that status row is historical, not the current state on the event. Don't quote a historical event's status as the event's live status.
4. Source URLs should be preserved verbatim in any downstream summary — they are the agent's single route back to ground truth.

## Schema alignment with the DPA Dashboard

The dashboard manual-input surface is driven by `gtaapi/lux/serializers.py`:
- `InterventionSerializer` (line 1649) — intervention shape
- `EventSerializer` (line 4030) — event shape

MNT's read paths render the same fields the dashboard serializer produces, with deliberate divergences documented here:

- **Flat, not nested.** The serializer returns nested objects (e.g. `event_type: {event_type_id, event_type_name}`); MNT flattens to adjacent `event_type_id` + `event_type_name` keys. Flat markdown is cheaper for LLM consumption and the id+name pair is semantically identical.
- **Sources carry file metadata.** `lux_event_source_serializer` returns only source + institution + source_type + display_on_flag. MNT additionally surfaces `file_url`, `file_name` via joins to `lux_source_file` / `lux_file_log` so the source_fetcher tool can use the S3 HTTP fallback without a second round trip.
- **Agents always included.** The main `EventSerializer` does not include the agent list (the `EventAgentSerializer` is a separate endpoint). MNT surfaces agents inline in `get_event` output for OP-005 compliance — a reviewer needs firm / regulator linkages without an extra call.
- **`author` semantics match serializer.** MNT's `get_event` returns `author` as the first user to touch the event ordered by `date_added ASC` — identical to `EventSerializer.get_author`. No filter on `status_id`.
- **Policy areas intentionally duplicated.** Both the intervention's single `policy_area_id` and the M2M `policies[]` are rendered, clearly labelled. The dashboard exposes both; reviewers need both.
- **`amelia_creation_duration_minutes` skipped.** This is a write-only UI telemetry field; MNT is read-only for this dimension.

## Key design patterns

- **Lazy singletons.** `get_db_client()` and `get_source_fetcher()` create a single instance per process on first call. DB connection reuse matters for warm-path latency.
- **Dependency injection into storage.** `DPADatabaseClient.__init__` and `SourceFetcher.__init__` accept a `ReviewStorage` instance so tests can redirect disk writes to `tmp_path`.
- **Two-role user model.** Enforced in `api.py` — do not plumb a user_id parameter through MCP tools. The persona is determined by the tool, not caller input.
- **Blocking DB wrapped, not refactored.** Every `async def` handler in `server.py` wraps `db_client.<method>` in `asyncio.to_thread`. DB client methods are sync (`def`) and must stay sync until the full asyncmy migration (tracked in CHANGELOG v0.2.0 follow-up).
- **Input strictness.** All MCP input models inherit from `_StrictInput` (in `server.py`) which sets `extra='forbid'` — catches LLM field-name drift (`status_id` vs `new_status_id`, `measure_id` vs `event_id`) with a clear `ValidationError` instead of silently ignoring the bad field.
- **ToolError for expected failures.** Event not found, source index out of range, `add_comment` / `set_status` DB failure. Unexpected failures (DB disconnect, network error) surface as stack traces — do not catch them.
- **Auto-user creation.** `_ensure_automated_users` runs once per process on first connection, INSERT IGNORE-ing the Buzessa / Buzetta rows into `auth_user`. This is safe (idempotent) and makes fresh dev DB setups one step shorter.

## Testing

```bash
uv run pytest                                          # 68 unit tests
uv run pytest --cov=dpa_mnt --cov-report=term-missing  # coverage
uv run python qa/run_review_format.py                  # formatter regression vs standards
uv run python qa/run_review_format.py --write-standards  # seed new standards
```

The unit suite covers formatters (truncation, author/is_current/benchmarks rendering, error shapes), strict-input validation (including cross-server ID name drift), storage (intervention-scoped, event-prefixed), and source fetching (mocked httpx). Integration tests against a real MySQL schema are tracked as a v0.3 follow-up.

## Known drift / retained-for-compat

- `DPA_FRAMEWORK_ID = 496` in `constants.py` is deprecated but kept — used only to read old legacy rows that pre-date the issue-tag mechanism.
- `SANCHO_USER_ID` alias in `constants.py` is backwards-compat for existing review tools that expect that name; it resolves to `BUZESSA_REVIEWER_ID`.

## Entry point

```toml
[project.scripts]
dpa-mnt = "dpa_mnt.server:main"
```

`main()` fails fast if `GTA_DB_HOST` or `GTA_DB_PASSWORD_WRITE` are unset, then calls `mcp.run()` on the FastMCP stdio transport.
