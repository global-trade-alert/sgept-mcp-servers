# Changelog

All notable changes to `gta-mnt` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Internal use only — no public release surface, so MINOR bumps are used liberally for behaviour changes and PATCH is reserved for pure bug fixes.

---

## [0.2.0] — 2026-04-22

Quality uplift pass, aligning gta-mnt with the internal template (`sgept-gta-mcp`) while preserving the different internal use case (direct MySQL, two-persona write path, on-disk audit trail).

### Added
- **Strict Pydantic input models.** All MCP tool inputs inherit from a shared `_StrictInput` base with `extra='forbid'`, `str_strip_whitespace=True`, and `validate_assignment=True`. Catches LLM field-name drift (`status_id` vs `new_status_id`, `measure_id` vs `state_act_id`) at the validator boundary instead of silently ignoring the wrong field.
  - **Why:** without `extra='forbid'`, Pydantic accepted the tool call and dropped the unrecognised key, leaving the underlying DB call to run with stale / default values — a silent-failure class that produced bad review comments.
- **`new_status_id` validator** on `SetStatusInput` restricting to `{1, 2, 3, 6, 19}` with a message that names each value.
- **`CHARACTER_LIMIT = 100_000`** and `_truncate(...)` helper in `formatters.py`. Applied to `format_step1_queue`, `format_measure_detail`, and `format_source_result`. Truncation appends a pagination hint naming the smaller payload the agent can re-request (`offset=...`, `include_interventions=False`, `fetch_content=False`).
  - **Why:** a measure with 20+ interventions and a long PDF could exceed 400KB — above that, LLM clients silently drop or summarise content and the agent makes decisions on an incomplete view.
- **`ToolError` routing** for expected failure paths: unknown framework name in `add_framework`, `source_index` out of range in `get_source`, missing `GTA_API_KEY` for `guess_hs_codes`, Bastiat HTTP error / timeout. Unexpected failures (DB disconnect, boto3 credential error) continue to surface as stack traces.
  - **Why:** returning a success-shaped `❌ ...` string made the agent treat an error like a normal tool result and format it into a review comment. `ToolError` lands as an MCP error block, which the agent handles as a retry signal.
- **`$GTA_MNT_REVIEW_STORAGE_PATH`** environment variable overrides the review artifact root. Default: `~/.gta-mnt/sc-reviews`.
  - **Why:** previous hardcoded `/home/deploy/jf-private/jf-thought/sgept-monitoring/gta/sc-reviews` broke the server on any non-deploy host (including every dev machine and CI).
- **`CLAUDE.md`** — agent-facing architecture, invariant documentation (Claudino/Claudito two-persona hard rule), tool matrix, env-var table, design-pattern notes.
- **`CHANGELOG.md`** — this file.
- **GitHub Actions `tests.yml`** — runs `uv sync` + `uv run pytest` on push and PR. Python 3.12.
- **MCP resources** (`resources/`) served under the `gta-mnt://` URI scheme: review criteria, status-ID decision tree, comment template catalogue, framework IDs, source-extraction notes. Loader in `src/gta_mnt/resources_loader.py`.
  - **Why:** the review agent previously held this knowledge only in its prompt, which went stale and drifted across sessions. Resources are read at runtime from the repo.
- **`qa/` harness** — lightweight gold-standard regression tests for review formatting and key validators. Standards checked into `qa/standards/`.
- `pytest-cov` added to the dev dependency group.

### Changed
- **Async DB path.** `GTADatabaseClient` methods are now sync (`def`); all blocking `pymysql` calls are wrapped in `asyncio.to_thread` at the handler boundary in `server.py`. Previously the methods were declared `async def` but contained purely blocking code, which stalled the event loop under concurrent tool calls.
  - **Why:** a faithful stopgap until the full `asyncmy` / `aiomysql` migration (see follow-up below). Low diff, no schema change, no new dependency.
- **`pyproject.toml`.** Migrated from deprecated `[tool.uv] dev-dependencies` to PEP 735 `[dependency-groups]`. Version bumped 0.1.0 → 0.2.0.
- **`README.md`** rewritten end-to-end. Corrected tool count (23, not 7 as previously claimed), replaced the stale JWT / REST env-var block with the actual direct-MySQL env vars, removed the hardcoded storage path from the Artifact Storage section, updated the architecture diagram to reflect the current MySQL / S3 / Bastiat topology, and dropped the obsolete "WS" planning artefacts.

### Deprecated
- `src/gta_mnt/models.py` input models (`Step1QueueInput`, `GetMeasureInput`, etc.) are dead code — `server.py` defines its own inline input models and nothing imports the `models.py` versions any more. Kept for this release to keep the diff small; safe to delete in a future cleanup. Output models (`SourceResult`, `CommentResult`, etc.) are still imported by `source_fetcher.py` and tests — leave those alone.
- `src/gta_mnt/auth.py` (`JWTAuthManager`) is unused on the direct-MySQL path. Kept for any future REST-API tool.

### Removed
- `tests/unit/test_api.py`. Tested an obsolete `GTAAPIClient` REST-relay class that no longer exists in the codebase (the client migrated to direct MySQL in an earlier release and the tests were never rewritten). The 9 tests listed as "passing" in the old README were in fact collecting-with-errors against a missing import. A replacement integration test suite hitting a real MySQL schema is tracked as a follow-up.

### Fixed
- Two formatter unit tests (`test_format_step1_queue_with_measures`, `test_format_measure_detail`) had assertions that referenced columns (`USA` jurisdiction, `Implementing Jurisdiction` header) that the current formatters no longer render. Updated to match current behaviour.

### Follow-ups (Linear)
- Full async MySQL driver migration (`asyncmy` / `aiomysql`). Removes the `asyncio.to_thread` wrapper and unblocks multi-caller workloads. Also covers `source_fetcher.py` which has the same blocking-boto3-inside-async pattern.
- Delete `src/gta_mnt/models.py` input-model stubs; lift output types to a new `schemas.py`.
- Integration tests with a dockerised MySQL matching the gta schema.

---

## [0.1.0] — 2026-01 through 2026-04

Initial internal release. Reconstructed from git history; no formal release was cut.

### Added
- Review tool set (Sancho Claudino, user_id 9900): `gta_mnt_list_step1_queue`, `gta_mnt_list_step2_queue`, `gta_mnt_list_queue_by_status`, `gta_mnt_get_measure`, `gta_mnt_get_source`, `gta_mnt_add_comment`, `gta_mnt_set_status`, `gta_mnt_add_framework`, `gta_mnt_list_templates`, `gta_mnt_log_review`.
- Entry-creation tool set (Sancho Claudito, user_id 9901): `gta_mnt_create_state_act`, `gta_mnt_create_intervention`, `gta_mnt_add_ij`, `gta_mnt_add_product`, `gta_mnt_add_sector`, `gta_mnt_add_rationale`, `gta_mnt_add_firm`, `gta_mnt_add_source`, `gta_mnt_queue_recalculation`, `gta_mnt_add_level`, `gta_mnt_add_motive_quote`.
- Reference lookup: `gta_mnt_lookup` (16 tables) and `gta_mnt_guess_hs_codes` (Bastiat API semantic match).
- Two-persona user-ID enforcement (9900 reviewer / 9901 author) with the "never mix" invariant documented in `constants.py`.
- Framework ID 495 (`sancho claudino review`) and 500 (`sancho claudito reported`) for audit tagging.
- Status IDs 1/2/3/6/19 for the review state machine.
- Status-time ordering via `api_state_act_status_log` for accurate queue ordering.
- On-disk review artifact storage: `source.{pdf|html|txt}`, `source-url.txt`, `comments.md`, `review-log.md` per state-act ID.
- S3-first, URL-fallback source fetcher with `pypdf` + BeautifulSoup text extraction.
- `motive_quotes` field on measure detail and dedicated `gta_mnt_add_motive_quote` tool backed by `gta_stated_motive_log`.
- `is_horizontal`, `author_id` fields in `get_measure` response.
- JWT auth scaffolding (`auth.py`) — retained for future REST tools, not used by the direct-MySQL path.
- 53 unit tests across `test_formatters.py`, `test_source_fetcher.py`, `test_storage.py` (+ 9 rotted tests in `test_api.py` retired in 0.2.0).

### Fixed
- Source retrieval and display in `get_measure` and `get_source`.
- `add_framework` to write into `api_framework_log` (not `gta_framework`); also auto-creates the framework row if missing.
- Source citation bug: now uses the authoritative `api_state_act_source` table instead of the stale snapshot field.
- Removed hard-coded limits from the Sancho review queue; added `exclude_framework_id` filter for already-reviewed measures.
