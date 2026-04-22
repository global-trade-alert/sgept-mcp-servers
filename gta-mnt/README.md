# GTA-MNT MCP Server

**Version:** 0.2.0
**Status:** Production (internal use)
**Purpose:** Internal MCP server for automated GTA review and entry creation (Sancho Claudino / Sancho Claudito system).

---

## Overview

The GTA-MNT (GTA Monitoring) MCP server powers two internal automation personas against the Global Trade Alert database:

| Persona | User ID | Role | Operations |
|---|---|---|---|
| **Sancho Claudino** | 9900 | REVIEWER | Comments, status changes, framework tags |
| **Sancho Claudito** | 9901 | AUTHOR | State acts, interventions, products, sectors, firms, sources |

**Hard constraint.** These personas must never be mixed. A reviewer must not appear as the author of the entry they might later review. The separation is enforced in `constants.py` and threaded through every DB-writing method.

Unlike the public-facing `sgept-gta-mcp`, this server hits the GTA MySQL database directly, persists a disk-based audit trail for every reviewed measure, and exposes entry-creation tools restricted to internal users.

---

## Tool Summary

23 tools, grouped by persona and purpose.

### Review tools (Sancho Claudino, user_id 9900)
| Tool | Purpose |
|---|---|
| `gta_mnt_list_step1_queue` | List measures awaiting Step 1 review (status 2) |
| `gta_mnt_list_step2_queue` | List measures awaiting Step 2 review (status 19) |
| `gta_mnt_list_queue_by_status` | List measures at any status (1/2/3/6/19) |
| `gta_mnt_get_measure` | Full measure detail + interventions + comments |
| `gta_mnt_get_source` | Fetch official source (S3 priority, URL fallback, PDF/HTML extraction) |
| `gta_mnt_add_comment` | Structured review comment authored by 9900 |
| `gta_mnt_set_status` | Change measure status (creates status-log entry) |
| `gta_mnt_add_framework` | Tag measure with review framework (495 or 500) |
| `gta_mnt_list_templates` | List comment-template library |
| `gta_mnt_log_review` | Save a review-log.md to persistent storage |

### Entry-creation tools (Sancho Claudito, user_id 9901)
| Tool | Purpose |
|---|---|
| `gta_mnt_create_state_act` | Create a new measure (status 1, In progress) |
| `gta_mnt_create_intervention` | Create an intervention under a state act |
| `gta_mnt_add_ij` | Add implementing jurisdiction to intervention |
| `gta_mnt_add_product` | Add affected product (HS code) |
| `gta_mnt_add_sector` | Add affected sector (CPC) |
| `gta_mnt_add_rationale` | Add rationale / motive tag |
| `gta_mnt_add_firm` | Add beneficiary / target firm |
| `gta_mnt_add_source` | Add additional source URL to state act |
| `gta_mnt_queue_recalculation` | Queue AJ/DM population procedure |
| `gta_mnt_add_level` | Add level row (prior/new value + unit) |
| `gta_mnt_add_motive_quote` | Add stated-motive quote (gta_stated_motive_log) |

### Lookup tool
| Tool | Purpose |
|---|---|
| `gta_mnt_lookup` | ID lookup across 16 reference tables (jurisdiction, product, sector, intervention_type, MAST chapters, evaluation, affected_flow, eligible_firm, implementation_level, intervention_area, firm_role, level_type, unit, rationale, firm, subchapter) |
| `gta_mnt_guess_hs_codes` | AI-powered HS code inference via Bastiat API (semantic match, unlike substring-based `gta_mnt_lookup(table='product')`) |

Verify the count live:
```bash
grep -c "@mcp.tool" src/gta_mnt/server.py   # -> 23
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internal review agent                     │
│                                 │                                │
│                   MCP protocol  │                                │
│                                 ▼                                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    gta-mnt MCP server                    │   │
│   │                                                          │   │
│   │  • 23 tools, strict Pydantic validation                  │   │
│   │  • Two-role user model (9900 / 9901) — not mixable       │   │
│   │  • Blocking pymysql wrapped in asyncio.to_thread         │   │
│   │  • CHARACTER_LIMIT truncation with pagination hints      │   │
│   │  • ToolError for expected failures                       │   │
│   └───┬────────────────────┬────────────────────┬────────────┘   │
│       │                    │                    │                │
│       ▼                    ▼                    ▼                │
│  ┌─────────┐          ┌─────────┐          ┌─────────┐           │
│  │  MySQL  │          │   S3    │          │ Bastiat │           │
│  │  (GTA)  │          │(sources)│          │  API    │           │
│  └─────────┘          └─────────┘          └─────────┘           │
│                            │                                     │
│                            ▼                                     │
│                ┌─────────────────────────┐                       │
│                │ Review artifact storage │                       │
│                │ (on-disk audit trail)   │                       │
│                └─────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

### Status IDs

| ID | Name | Meaning |
|----|------|---------|
| 1 | In progress | Newly created; draft in progress |
| 2 | Step 1 | Awaiting initial review |
| 3 | Publishable | Passed review |
| 6 | Under revision | Issues found, sent back |
| 19 | Step 2 | Awaiting second-stage review |

### Framework IDs

| ID | Name | Meaning |
|----|------|---------|
| 495 | `sancho claudino review` | Reviewed by Sancho Claudino |
| 500 | `sancho claudito reported` | First-drafted by Sancho Claudito |

---

## Installation

### Prerequisites
- Python 3.10+
- `uv` package manager
- GTA MySQL credentials (write-enabled)
- AWS S3 credentials for archived sources
- Bastiat API key (only for `gta_mnt_guess_hs_codes`)

### Setup
```bash
cd sgept-dev/sgept-mcp-servers/gta-mnt
uv sync
```

### Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GTA_DB_HOST` | yes | `gtaapi.cp7esvs8xwum.eu-west-1.rds.amazonaws.com` | Fails fast in `main()` if unset |
| `GTA_DB_NAME` | no | `gtaapi` | |
| `GTA_DB_PORT` | no | `3306` | |
| `GTA_DB_USER_WRITE` | no | falls back to `GTA_DB_USER`, then `gtaapi` | |
| `GTA_DB_PASSWORD_WRITE` | yes | falls back to `GTA_DB_PASSWORD` | Fails fast in `main()` if unset |
| `GTA_MNT_REVIEW_STORAGE_PATH` | no | `~/.gta-mnt/sc-reviews` | Where audit artifacts go. Set to the persistent-volume path on deploy. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION` | for source fetch | | Needed only by `gta_mnt_get_source` when the source is S3-archived |
| `GTA_API_KEY` | for `gta_mnt_guess_hs_codes` | | Bastiat API key |

---

## Usage

### Running the server
```bash
uv run gta-mnt               # stdio transport (default for MCP)
uv run python -m gta_mnt.server
```

### Claude Desktop / MCP host config
```json
{
  "mcpServers": {
    "gta-mnt": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/gta-mnt", "run", "gta-mnt"],
      "env": {
        "GTA_DB_HOST": "...",
        "GTA_DB_PASSWORD_WRITE": "...",
        "AWS_ACCESS_KEY_ID": "...",
        "AWS_SECRET_ACCESS_KEY": "...",
        "AWS_S3_REGION": "eu-west-1",
        "GTA_MNT_REVIEW_STORAGE_PATH": "/path/to/sc-reviews"
      }
    }
  }
}
```

### Canonical review workflow
```
1. gta_mnt_list_step1_queue(exclude_framework_id=495)
2. gta_mnt_get_measure(state_act_id=X, include_interventions=True)
3. gta_mnt_get_source(state_act_id=X)            # writes source.{pdf|html|txt} to disk
4. (validate fields against source)
5a. Issues:    gta_mnt_add_comment(...) ; gta_mnt_set_status(new_status_id=6, ...)
5b. No issues: gta_mnt_add_framework(state_act_id=X)
6. gta_mnt_log_review(state_act_id=X, decision="APPROVE"|"DISAPPROVE", ...)
```

---

## Persistent artifact storage

Every measure passed to `gta_mnt_get_source`, `gta_mnt_add_comment`, or `gta_mnt_log_review` gets a per-measure folder under `$GTA_MNT_REVIEW_STORAGE_PATH`:

```
$GTA_MNT_REVIEW_STORAGE_PATH/
└── 12345/
    ├── source.{pdf|html|txt}   # Archived source document
    ├── source-url.txt          # Original URL
    ├── comments.md             # Append-only, one block per comment
    └── review-log.md           # Overwritten on each log_review call
```

File lifecycle:

| File | Written by | Update mode |
|---|---|---|
| `source.{ext}` | `gta_mnt_get_source` | Overwrite |
| `source-url.txt` | `gta_mnt_get_source` | Overwrite |
| `comments.md` | `gta_mnt_add_comment` | Append |
| `review-log.md` | `gta_mnt_log_review` | Overwrite |

---

## Comment formatters (Python helpers)

Callable from application code (not as MCP tools — these produce the `comment_text` string the agent then passes to `gta_mnt_add_comment`).

```python
from gta_mnt.formatters import (
    format_issue_comment,
    format_verification_comment,
    format_review_complete_comment,
    format_guessed_hs_codes,
)
```

All formatter outputs are capped at `CHARACTER_LIMIT = 100_000` with a pagination hint appended when truncated (see `formatters.py`).

---

## Development

### Tests
```bash
uv run pytest                                    # all tests
uv run pytest tests/unit/ -v                     # unit only
uv run pytest --cov=gta_mnt --cov-report=term-missing
```

Current suite: `tests/unit/test_formatters.py`, `tests/unit/test_source_fetcher.py`, `tests/unit/test_storage.py`. See `CHANGELOG.md` v0.2.0 — the old `tests/unit/test_api.py` was retired when the client migrated from REST relay to direct MySQL; a new integration-test layer is planned.

### Linting / formatting
No in-repo config yet. If you add ruff / black, put the config in `pyproject.toml` under `[tool.ruff]` / `[tool.black]`.

### File layout
```
gta-mnt/
├── src/gta_mnt/
│   ├── __init__.py
│   ├── server.py           # MCP tool registrations (23 tools), strict input models
│   ├── api.py              # GTADatabaseClient (pymysql), BastiatAPIClient (httpx)
│   ├── auth.py             # JWTAuthManager (unused by DB client, retained for future API reuse)
│   ├── models.py           # Legacy Pydantic models (output types still used; input types are dead)
│   ├── formatters.py       # Markdown formatting + CHARACTER_LIMIT truncation
│   ├── source_fetcher.py   # S3/URL/PDF/HTML retrieval + auto-save to storage
│   ├── storage.py          # ReviewStorage: on-disk audit artifacts
│   ├── constants.py        # User IDs, framework IDs, lookup-table map, storage path
│   └── cli.py              # Thin CLI wrapper
├── tests/unit/             # pytest, pytest-asyncio
├── CHANGELOG.md            # Keep-a-Changelog
├── CLAUDE.md               # Agent-facing architecture + invariants
├── README.md
├── pyproject.toml          # uv-managed, dependency-groups for dev deps
└── pytest.ini
```

---

## Troubleshooting

### "GTA_DB_PASSWORD_WRITE environment variable missing"
Set DB creds (see env-var table above). The server refuses to start without them.

### Storage path errors on Linux / Docker
Set `GTA_MNT_REVIEW_STORAGE_PATH` explicitly to your mounted volume. The default (`~/.gta-mnt/sc-reviews`) expands against the runtime user's home directory, which varies between dev and deploy.

### Scanned-PDF extraction returns no text
`pypdf` cannot OCR. The tool emits a warning and references the source URL; fall back to the archived HTML or a downstream OCR pass.

### Concurrent tool calls feel slow
DB operations are wrapped in `asyncio.to_thread`. That's fine for one agent at a time but serialises multi-caller workloads. Full `asyncmy` / `aiomysql` migration is tracked in the Linear follow-up referenced in `CHANGELOG.md` v0.2.0.

---

## License

Internal SGEPT tool. Not for public distribution.
