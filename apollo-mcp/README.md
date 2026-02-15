# Apollo MCP Server

MCP server for Apollo.io contact discovery and email enrichment.

## Tools

| Tool | Cost | Purpose |
|------|------|---------|
| `apollo_search_people` | Free | Search contacts by company, title, seniority, location |
| `apollo_search_company` | Free | Look up company org ID, domain, metadata |
| `apollo_enrich_contact` | 1 credit | Get a person's email address |
| `apollo_find_contact_email` | 1 credit | Search + enrich in one step |

## Setup

```bash
cd apollo-mcp
uv sync
export APOLLO_API_KEY="your-key"
uv run apollo-mcp
```

## Claude Desktop / jf-ceo integration

Add to `.mcp.json`:

```json
{
  "apollo": {
    "type": "stdio",
    "command": "uv",
    "args": ["--directory", "/path/to/apollo-mcp", "run", "apollo-mcp"],
    "env": {
      "APOLLO_API_KEY": "your-key"
    }
  }
}
```
