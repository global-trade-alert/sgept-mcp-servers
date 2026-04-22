# SGEPT MCP Servers

**Purpose:** Model Context Protocol (MCP) servers providing LLM access to GTA and DPA policy databases.
**Status:** Active, production-ready (full source code)
**Tech Stack:** Python 3.10+ | FastMCP | httpx | Pydantic | uv package manager

---

## Quick Reference

| Server | Location | Purpose |
|--------|----------|---------|
| **sgept-gta-mcp** | Nested repo (github.com/global-trade-alert/sgept-gta-mcp) | Global Trade Alert - 75,000+ trade policy interventions |
| **sgept-dpa-mcp** | Nested repo (github.com/global-trade-alert/sgept-dpa-mcp) | Digital Policy Alert - 6,000+ digital policy regulations |

> **Retirement notes.** The in-tree `gta-mcp/` (retired JCC-418, commit e9abab1) and `dpa-mcp/` (retired JCC-497) subfolders have been superseded by the standalone `sgept-gta-mcp` and `sgept-dpa-mcp` repos cloned here as nested git repos. All GTA and DPA MCP development now happens in those upstream repos, not in this tree.

---

## Directory Structure

```
sgept-mcp-servers/
├── sgept-gta-mcp/                    # Global Trade Alert MCP Server (nested repo)
│   └── (upstream: github.com/global-trade-alert/sgept-gta-mcp)
│
├── sgept-dpa-mcp/                    # Digital Policy Alert MCP Server (nested repo)
│   └── (upstream: github.com/global-trade-alert/sgept-dpa-mcp)
│
├── dpa-mnt/                          # DPA monitoring/review tooling (direct MySQL)
├── gta-mnt/                          # GTA monitoring/review tooling (direct MySQL)
├── us-tariff-mcp/                    # US Tariff MCP server
├── metis-mcp/                        # Metis workflow engine MCP
├── sgept-slack-mcp/                  # Slack MCP (multi-identity)
├── apollo-mcp/                       # Apollo lead-gen MCP
│
├── api-documentation/
│   └── sgept-api-documentation.yaml  # OpenAPI spec
│
└── resources/                        # Shared MCP resources
    ├── mcp_best_practices.md
    └── layer1_assessment_tool_descriptions.md
```

---

## MCP Tools (authoritative tool lists in upstream repos)

Tool inventories for GTA and DPA live in their respective repo READMEs:
- GTA: `sgept-gta-mcp/README.md`
- DPA: `sgept-dpa-mcp/README.md`

---

## Development Workflow

### Prerequisites
- Python 3.10+
- `uv` package manager (recommended)
- GTA/DPA API key

### Installation

```bash
# GTA MCP
cd sgept-gta-mcp
uv sync
export SGEPT_GTA_API_KEY="your-api-key"

# DPA MCP
cd sgept-dpa-mcp
uv sync
export DPA_API_KEY="your-api-key"
```

### Running Locally

```bash
# GTA MCP server
cd sgept-gta-mcp
uv run gta-mcp

# DPA MCP server
cd sgept-dpa-mcp
uv run dpa-mcp
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "gta": {
      "command": "uv",
      "args": ["--directory", "/path/to/sgept-gta-mcp", "run", "gta-mcp"],
      "env": { "SGEPT_GTA_API_KEY": "your-key" }
    },
    "dpa": {
      "command": "uv",
      "args": ["--directory", "/path/to/sgept-dpa-mcp", "run", "dpa-mcp"],
      "env": { "DPA_API_KEY": "your-key" }
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
cd sgept-gta-mcp
uv run pytest

cd sgept-dpa-mcp
uv run pytest
```

Each upstream repo carries its own CI workflow.

---

## Integration with jf-private

- **Nested Repo:** This is a nested git repo, gitignored from jf-private
- **API Keys:** Stored in environment variables (not committed)
- **Reference Data:** Markdown files provide jurisdiction lists, intervention types
- **Related:** Works alongside portfolio-bridge MCP server for plan management
