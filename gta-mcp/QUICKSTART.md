# GTA MCP Server - Quick Start Guide

## What You Have

A complete, production-ready MCP server that exposes the Global Trade Alert database to LLMs like Claude. The server follows all MCP best practices and is optimized for agent usage.

## Immediate Next Steps

### 1. Test the Server Locally (5 minutes)

```bash
# Navigate to the project
cd gta_mcp

# Install dependencies
uv sync

# Set your API key
export GTA_API_KEY='your-sgept-api-key-here'

# Test it works
uv run gta-mcp --help
```

If you see help output, the server is ready!

### 2. Connect to Claude Desktop (10 minutes)

**On macOS:**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

**On Windows:**
Edit `%APPDATA%/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "gta": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/gta_mcp",
        "run",
        "gta-mcp"
      ],
      "env": {
        "GTA_API_KEY": "your-actual-api-key"
      }
    }
  }
}
```

**Important:** 
- Use the **absolute path** to your gta_mcp directory
- Replace `your-actual-api-key` with your real GTA API key
- **Completely quit** Claude Desktop (not just close the window) and restart

### 3. Test in Claude

Once Claude Desktop restarts, try:

> "Using the GTA tool, find all US import tariffs on Chinese products announced in 2024"

> "Search for EU subsidies that GTA evaluates as harmful"

> "Get full details for GTA intervention 138295"

## What the Server Does

### Four Main Tools

1. **`gta_search_interventions`**: Comprehensive search with ~15 filter parameters
   - Countries (implementing/affected)
   - Products (HS codes)
   - Intervention types
   - Dates, status, GTA evaluation
   - Pagination up to 1000 results

2. **`gta_get_intervention`**: Full details for specific intervention ID
   - Complete description and sources
   - All jurisdictions and products
   - Implementation timeline

3. **`gta_list_ticker_updates`**: Recent changes to existing interventions
   - Monitor policy evolution
   - Track amendments

4. **`gta_get_impact_chains`**: Granular bilateral relationships
   - Product or sector level
   - Jurisdiction-product-jurisdiction tuples

### Key Features

- **Always includes** title, description, sources as you requested
- **Smart formatting**: Markdown for humans, JSON for machines
- **Character limits**: Auto-truncates with clear guidance (25K limit)
- **Pagination**: Handles large datasets efficiently
- **Error handling**: Clear, actionable messages

## Architecture

```
gta_mcp/
├── pyproject.toml          # Dependencies (mcp, httpx, pydantic)
└── src/gta_mcp/
    ├── server.py           # 4 MCP tools with full docstrings
    ├── api.py              # GTA API client with auth
    ├── models.py           # Pydantic input validation
    └── formatters.py       # Markdown/JSON formatters
```

**Design highlights:**
- No code duplication (shared API client, formatters)
- Comprehensive input validation via Pydantic
- Type hints throughout
- Async/await for all I/O
- Tool annotations per MCP spec

## Common Use Cases

### Rapid Response Analysis
```
"Find all Chinese rare earth export controls announced in the last 3 months"
```

### Section 232 Context
```
"Search for US Section 232 investigations and list all intervention IDs, 
then get full details for each including sources"
```

### Cross-Government Comparisons
```
"Compare subsidies implemented by US vs EU in 2024, filtering for semiconductor 
products. Show evaluation and implementation dates."
```

### Bilateral Analysis
```
"Get impact chains at product level for US implementing jurisdictions 
affecting China"
```

## Testing Checklist

- [ ] Server starts: `uv run gta-mcp`
- [ ] Appears in Claude Desktop MCP servers list
- [ ] Can search interventions with simple query
- [ ] Can filter by country codes
- [ ] Can get detailed intervention
- [ ] Pagination works with offset parameter
- [ ] Both markdown and JSON formats work
- [ ] Error messages are clear when API key is wrong

## Troubleshooting

**"Module not found"**
- Run `uv sync` in the gta_mcp directory

**Server doesn't appear in Claude**
- Check absolute path in config.json
- Verify API key is in the `env` section
- Quit Claude completely (from system tray) and restart

**Authentication errors**
- Verify your API key: `echo $GTA_API_KEY`
- Test manually: `curl -H "Authorization: APIKey YOUR_KEY" https://api.globaltradealert.org/api/v2/gta/data/`

**Response truncated messages**
- This is intentional! Use `offset` parameter to paginate
- Or add more specific filters to reduce result set

## Next Steps

1. **Test with real queries** matching your rapid response use cases
2. **Integrate into workflows** - the server is ready for production
3. **Build DPA server** (separate project, similar structure)

## Notes on DPA Server

When ready for DPA, I'll build it as a completely separate server following the same pattern:
- `dpa_mcp` package name
- Similar tool structure
- Independent deployment
- Can run both servers simultaneously

## Support

Any issues or questions, let me know. The implementation follows MCP best practices and should work reliably with Claude and other MCP clients.

---

**Bottom line**: You have a production-ready GTA MCP server. Install dependencies, set your API key, add to Claude Desktop config, restart Claude, and start querying.
