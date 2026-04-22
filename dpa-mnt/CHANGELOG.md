# Changelog

All notable changes to `dpa-mnt` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Internal use only — no public release surface, so MINOR bumps are used liberally for behaviour changes and PATCH is reserved for pure bug fixes.

---

## [0.2.0] — 2026-04-22

Quality uplift pass, aligning `dpa-mnt` with the sibling `gta-mnt` v0.2.0 bar while adding schema-alignment work specific to the DPA Activity Tracker dashboard's manual-input surface. The authoritative schema lives in the `gtaapi/lux/` app (`InterventionSerializer`, `EventSerializer`); MNT's read paths now match what the dashboard exposes, so a reviewer using MNT does not have to tab back to the dashboard for a missing attribute.

### Added
- **Strict Pydantic input models.** All MCP tool inputs inherit from a shared `_StrictInput` base with `extra='forbid'`, `str_strip_whitespace=True`, and `validate_assignment=True`. Catches LLM field-name drift (e.g. `status_id` vs `new_status_id`, `measure_id` vs `event_id`) at the validator boundary instead of silently ignoring the wrong field.
  - **Why:** without `extra='forbid'`, Pydantic accepted the tool call and dropped the unrecognised key, leaving the DB call to run with stale / default values — a silent-failure class that produced bad review comments. Particularly acute here because the sibling `gta-mnt` uses `measure_id` and `state_act_id` as its ID keys, which a cross-wired LLM could emit on DPA calls.
- **`new_status_id` validator** on `SetStatusInput` restricting to `{1, 2, 3, 4, 5, 7}` with a message that names each id=name pair. DPA's valid set is distinct from GTA's `{1, 2, 3, 6, 19}` — `6` in DPA is not a defined status, so cross-server drift now fails loudly.
- **`CHARACTER_LIMIT = 100_000`** and `_truncate(...)` helper in `formatters.py`. Applied to `format_review_queue`, `format_event_detail`, `format_intervention_context`, and `format_source_result`. Truncation appends a pagination hint naming the smaller payload the agent can re-request (`offset=...`, `include_intervention=False`, `fetch_content=False`).
  - **Why:** a fully-expanded intervention context with many published siblings and long event descriptions could exceed 400KB. Above that, LLM clients silently drop or summarise content and the agent makes decisions on an incomplete view.
- **`ToolError` routing** for expected failure paths: event not found, source index out of range, event has no sources, `add_comment` / `set_status` / `add_review_tag` DB failures. Unexpected failures (DB disconnect, httpx network error on S3 fallback) continue to surface as stack traces.
  - **Why:** returning a success-shaped error string made the agent treat the error like a normal tool result and format it into a review comment. `ToolError` lands as an MCP error block, which the agent handles as a retry signal.
- **`$DPA_MNT_REVIEW_STORAGE_PATH`** environment variable overrides the review artifact root. Default: `~/.dpa-mnt/bc-reviews`.
  - **Why:** previous hardcoded `/Users/johannesfritz/...` path broke the server on every host except the machine it was written on (including every dev machine and CI).
- **`event.author`** extracted in `get_event` via a join on `lux_event_status_log` + `auth_user` (first user to touch the event, ordered by `date_added` ASC). Rendered in `format_event_detail` under a dedicated `**Author:**` line. Matches the authoritative `EventSerializer.get_author` definition.
- **`intervention.benchmarks`** extracted in `get_event` and `get_intervention_context` via joins on `lux_intervention_benchmark_log`, `gta_lead_benchmark_log`, `lux_benchmark_overlap_list`, `lux_benchmark_substance_list`. Rendered in the corresponding formatters as a list of `**name** (DPA/external) | Overlap: ... | Substance: ...`. Matches `InterventionBenchmarkThroughSerializer` from `gtaapi/lux/serializers.py`.
- **`get_intervention_context` parity.** The tool now returns `issues`, `rationales`, `agents`, and `benchmarks` alongside the existing intervention metadata and events timeline — bringing it to parity with `get_event` so a reviewer's Gate 0 call surfaces the full intervention state.
- **`CLAUDE.md`** — agent-facing architecture, invariant documentation (Buzessa/Buzetta two-persona hard rule), tool matrix, env-var table, design-pattern notes, schema-alignment divergences from the dashboard serializer.
- **`CHANGELOG.md`** — this file.
- **`QUICKSTART.md`** — setup, environment variables, first tool call, Claude Desktop integration.
- **`README.md`** — full rewrite (previous version was a 156-byte stub).
- **GitHub Actions `dpa-mnt-tests.yml`** — runs `uv sync` + `uv run pytest` on push and PR touching `dpa-mnt/**`. Python 3.12.
- **MCP resources** (`resources/`) served under the `dpa-mnt://` URI scheme: review criteria, status-ID decision tree, comment template catalogue, issue IDs (BC review tag), source-extraction notes. Loader in `src/dpa_mnt/resources_loader.py`.
  - **Why:** the review agent previously held this knowledge only in its prompt, which went stale and drifted across sessions. Resources are read at runtime from the repo.
- **Unit test suite** (68 tests) across `tests/unit/test_inputs.py`, `test_formatters.py`, `test_storage.py`, `test_source_fetcher.py`. Coverage: storage 100%, source_fetcher 93%, formatters 75%.
- **`qa/` harness** — lightweight gold-standard regression tests for the four customer-visible formatters (`format_review_queue`, `format_event_detail`, `format_intervention_context`, `format_source_result`). Standards checked into `qa/standards/`.
- `pytest-cov` added to the dev dependency group.

### Changed
- **Async DB path.** `DPADatabaseClient` methods are now sync (`def`); all blocking `pymysql` calls are wrapped in `asyncio.to_thread` at the handler boundary in `server.py`. Previously the methods were declared `async def` but contained purely blocking code, which stalled the event loop under concurrent tool calls.
  - **Why:** a faithful stopgap until the full `asyncmy` / `aiomysql` migration (see follow-up below). Low diff, no schema change, no new dependency.
- **`pyproject.toml`.** Migrated from deprecated `[tool.uv] dev-dependencies` to PEP 735 `[dependency-groups]`. Added `[tool.hatch.build.targets.wheel.force-include]` so `resources/` ships with the wheel. Version bumped 0.1.0 → 0.2.0.
- **`get_source` handler.** Fixed a latent bug where `intervention_id` was looked up at the top level of the `get_event` return dict instead of on its nested `event` key — fetch would work, but the disk-save prefix would have been wrong for any intervention.
- **Source result truncation.** Removed the internal 50KB content cap inside `format_source_result`; `CHARACTER_LIMIT` at the formatter boundary is now the single source of truth for response size.

### Deprecated
- `src/dpa_mnt/constants.py:DPA_FRAMEWORK_ID = 496` — the framework-tag mechanism has been replaced by the issue tag (`BC_REVIEW_ISSUE_ID = 83`). Kept only for reading legacy records; do not write framework 496 from new code.

### Removed
- Hardcoded per-developer `REVIEW_STORAGE_PATH` in `constants.py`.
- Return-string error handling inside handlers where expected failures now `raise ToolError`.

### Follow-ups (Linear)
- Full async MySQL driver migration (`asyncmy` / `aiomysql`). Removes the `asyncio.to_thread` wrapper and unblocks multi-caller workloads. Same follow-up tracked on the sibling `gta-mnt`.
- Integration tests hitting a dockerised MySQL matching the `lux` schema, to exercise the SQL paths that unit tests do not cover (api.py coverage is 10% today by design).
- Write-path tools (`create_event`, `create_intervention`, source/relation/agent adders) mirroring `EventSerializer` / `InterventionSerializer` validation. Deferred to v0.3.

---

## [0.1.0] — 2026-02 through 2026-04

Initial internal release. Reconstructed from git history; no formal release was cut.

### Added
- Review tool set (Buzessa Claudini, user_id 9902): `dpa_mnt_list_review_queue`, `dpa_mnt_get_event`, `dpa_mnt_get_intervention_context`, `dpa_mnt_get_source`, `dpa_mnt_add_comment`, `dpa_mnt_set_status`, `dpa_mnt_add_review_tag`, `dpa_mnt_list_templates`, `dpa_mnt_log_review`, `dpa_mnt_lookup_analysts`.
- Buzessa/Buzetta two-persona user-ID scheme (9902 reviewer / 9903 author) with the "never mix" invariant documented in `constants.py` — mirrors the `gta-mnt` Claudino/Claudito pattern.
- BC-review issue tag (`issue_id = 83`) applied to interventions via `dpa_mnt_add_review_tag`, idempotent.
- Auto-creation of the two automated user rows in `auth_user` on first DB connection (`_ensure_automated_users`).
- Comment writes into `api_comment_log` (read by the DPA Activity Tracker dashboard).
- Status writes into `lux_event_log.status_id` plus a log row in `lux_event_status_log`.
- Gate 0 intervention-context view (`get_intervention_context`) to inspect all sibling events before reviewing any single one.
- Source fetcher with `source_url` primary and `file_url` S3 HTTP fallback, PDF/HTML extraction.
- Per-intervention on-disk review artifact storage with event-prefixed files: `evt-<event_id>-source.{pdf|html|txt}`, `evt-<event_id>-source-url.txt`, `evt-<event_id>-comments.md`, `evt-<event_id>-review-log.md`.
