# dpa-mnt Quickstart

Internal MCP server for DPA Activity Tracker review automation (Buzessa Claudini). This quickstart gets you from a fresh checkout to a first tool call against a live DB.

## Prerequisites

- Python 3.10+ (3.12 recommended)
- `uv` (install with `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Read/write credentials for the `gtaapi` MySQL DB

## Install

From the repo root:

```bash
cd dpa-mnt
uv sync --all-extras --dev
```

This installs `dpa-mnt` plus the dev group (`pytest`, `pytest-asyncio`, `pytest-cov`).

## Configure environment

```bash
export GTA_DB_HOST="gtaapi.cp7esvs8xwum.eu-west-1.rds.amazonaws.com"
export GTA_DB_NAME="gtaapi"                              # optional, default
export GTA_DB_PORT="3306"                                # optional, default
export GTA_DB_USER_WRITE="gtaapi"                        # optional, default
export GTA_DB_PASSWORD_WRITE="<password>"                # required
export DPA_MNT_REVIEW_STORAGE_PATH="$HOME/.dpa-mnt/bc-reviews"  # optional, default
```

`main()` fails fast if `GTA_DB_HOST` or `GTA_DB_PASSWORD_WRITE` are unset.

## Smoke check

```bash
uv run python -c "from dpa_mnt.server import mcp; print(mcp)"
uv run pytest
```

Expect 68 passing tests.

## Run the server

```bash
uv run dpa-mnt
```

That starts the FastMCP server on stdio. Normal invocation is via an MCP host (Claude Desktop, agent runtime), not directly.

## Claude Desktop integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dpa-mnt": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/sgept-mcp-servers/dpa-mnt",
        "run",
        "dpa-mnt"
      ],
      "env": {
        "GTA_DB_HOST": "gtaapi.cp7esvs8xwum.eu-west-1.rds.amazonaws.com",
        "GTA_DB_PASSWORD_WRITE": "<password>",
        "DPA_MNT_REVIEW_STORAGE_PATH": "/absolute/path/to/bc-reviews"
      }
    }
  }
}
```

Restart Claude Desktop; `dpa-mnt` should appear under the server list.

## First tool call

From a Claude chat (with the server configured):

```
Please call dpa_mnt_list_review_queue with limit=5 and show me what's waiting.
```

Expected: a markdown table of up to 5 events in status 2 (Step 1 Review / AT), most recent first.

Then for any single event:

```
Please call dpa_mnt_get_intervention_context for intervention_id=<N>
and then dpa_mnt_get_event for event_id=<M>.
```

The first call is **Gate 0** — it shows the event's siblings (published context, prior reviews). The second is the full event detail, including the Phase 0.2.0 additions: author, benchmarks, issues, rationales, and all source metadata.

## MCP resources

Once the server is running, the following resources are available under the `dpa-mnt://` URI scheme:

- `dpa-mnt://review-criteria`
- `dpa-mnt://status-id-decision-tree`
- `dpa-mnt://comment-templates`
- `dpa-mnt://issue-ids`
- `dpa-mnt://source-extraction-notes`

The review agent should pull these at the start of any session — they replace knowledge previously held only in the prompt, which tended to drift across runs.

## Next steps

- Read `CLAUDE.md` for the full architecture, tool matrix, and design-pattern notes.
- Read `resources/review_criteria.md` for the field-by-field review minimum set.
- Read `resources/status_id_decision_tree.md` for verdict → tool-call mapping.

## Troubleshooting

**`ERROR: Missing required environment variables: GTA_DB_HOST, GTA_DB_PASSWORD_WRITE`** — you haven't exported the DB credentials. See "Configure environment" above.

**`dpa_mnt_set_status` fails with `new_status_id must be one of {1, 2, 3, 4, 5, 6, 7, 14}`** — you passed an invalid status ID. Common mistakes: `19` (a GTA status, not DPA), or inventing an ID not in `lux_event_status_list`. The four verdict IDs are `4` (FAIL critical), `5` (CONDITIONAL), `6` (PASS), `14` (FAIL out-of-scope).

**`ToolError: Event <N> not found`** — the event_id doesn't exist in `lux_event_log`. Confirm with the dashboard or `dpa_mnt_list_review_queue`.

**`source_index N out of range`** — the event has fewer sources than you requested. Check the `Sources` count in `dpa_mnt_get_event` output; indices are 0-based.

**Storage path errors (`Permission denied` writing to `~/.dpa-mnt/bc-reviews`)** — point `DPA_MNT_REVIEW_STORAGE_PATH` at a writable directory.
