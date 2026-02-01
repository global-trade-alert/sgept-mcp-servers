# SGEPT MCP Servers

**Purpose:** Model Context Protocol (MCP) servers providing LLM access to GTA and DPA policy databases.
**Status:** Active, production-ready (full source code)
**Tech Stack:** Python 3.10+ | FastMCP | httpx | Pydantic | uv package manager

---

## Quick Reference

| Server | Version | Purpose |
|--------|---------|---------|
| **GTA-MCP** | v0.3.0 | Global Trade Alert - 75,000+ trade policy interventions |
| **DPA-MCP** | v0.1.0 | Digital Policy Alert - 6,000+ digital policy regulations |

---

## Current State

**Status: FULL SOURCE CODE PRESENT**

Unlike other personal-dev repos, this repository contains complete Python source files (12 total). No source recovery needed.

| Category | Files | Purpose |
|----------|-------|---------|
| GTA-MCP | 6 | server, api, models, formatters, resources_loader, __init__ |
| DPA-MCP | 6 | server, api, models, formatters, resources_loader, __init__ |

---

## Directory Structure

```
sgept-mcp-servers/
├── gta-mcp/                          # Global Trade Alert MCP Server
│   ├── README.md                     # Comprehensive documentation
│   ├── QUICKSTART.md                 # Installation guide
│   ├── CHANGELOG.md                  # Version history
│   ├── pyproject.toml                # Dependencies (uv)
│   ├── uv.lock                       # Locked dependencies
│   ├── resources/                    # Reference data (markdown)
│   │   ├── GTA handbook.md
│   │   ├── gta_jurisdictions.md
│   │   ├── gta_intervention_type_list.md
│   │   └── guides/                   # Search and parameter guides
│   └── src/gta_mcp/
│       ├── server.py                 # 4 MCP tools
│       ├── api.py                    # GTA API client
│       ├── models.py                 # Pydantic input models
│       └── formatters.py             # Response formatting
│
├── dpa-mcp/                          # Digital Policy Alert MCP Server
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── resources/                    # Reference data
│   │   ├── dpa_activity_tracking_handbook.md
│   │   └── dpa_jurisdictions.md
│   └── src/dpa_mcp/
│       ├── server.py                 # 2 MCP tools
│       ├── api.py                    # DPA API client
│       ├── models.py
│       └── formatters.py
│
├── api-documentation/
│   └── sgept-api-documentation.yaml  # OpenAPI spec
│
└── resources/                        # Shared MCP resources
    ├── mcp_best_practices.md
    └── layer1_assessment_tool_descriptions.md
```

---

## GTA-MCP Tools

| Tool | Purpose |
|------|---------|
| `search_interventions` | Search trade interventions with filters (jurisdiction, type, date, sector) |
| `get_intervention` | Get full details of a specific intervention by ID |
| `list_ticker_updates` | Get recent policy updates (latest changes) |
| `get_impact_chains` | Analyze implementation chains (e.g., retaliation sequences) |

## DPA-MCP Tools

| Tool | Purpose |
|------|---------|
| `search_events` | Search digital policy events with filters |
| `get_event` | Get full details of a specific event by ID |

---

## Development Workflow

### Prerequisites
- Python 3.10+
- `uv` package manager (recommended)
- GTA/DPA API key

### Installation

```bash
# GTA-MCP
cd gta-mcp
uv sync
export SGEPT_GTA_API_KEY="your-api-key"

# DPA-MCP
cd dpa-mcp
uv sync
export SGEPT_DPA_API_KEY="your-api-key"
```

### Running Locally

```bash
# GTA-MCP server
cd gta-mcp
uv run python -m gta_mcp.server

# DPA-MCP server
cd dpa-mcp
uv run python -m dpa_mcp.server
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "gta-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/gta-mcp", "run", "gta-mcp"],
      "env": {
        "SGEPT_GTA_API_KEY": "your-key"
      }
    }
  }
}
```

---

## Architecture Pattern

```
┌────────────────────────────────────────────────────────────┐
│                     MCP Server Pattern                      │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐ │
│  │ Claude/LLM  │◀──▶│ MCP Server  │◀──▶│ SGEPT REST API  │ │
│  │  (Client)   │    │ (FastMCP)   │    │  (External)     │ │
│  └─────────────┘    └─────────────┘    └─────────────────┘ │
│                            │                                │
│                     ┌──────▼──────┐                         │
│                     │  Resources  │  Markdown reference     │
│                     │  (Local)    │  data served via MCP    │
│                     └─────────────┘                         │
└────────────────────────────────────────────────────────────┘
```

**Key features:**
- Async HTTP via httpx
- Pydantic input validation
- Markdown + JSON response formats
- Resource-based reference data (avoids hallucination)
- 25K character truncation for context management

---

## Testing

```bash
cd gta-mcp
uv run pytest
```

Note: CI/CD pipeline exists (`.github/workflows/ci.yml`) but test coverage is basic.

---

## Integration with jf-private

- **Nested Repo:** This is a nested git repo, gitignored from jf-private
- **API Keys:** Stored in environment variables (not committed)
- **Reference Data:** Markdown files provide jurisdiction lists, intervention types
- **Related:** Works alongside portfolio-bridge MCP server for plan management
