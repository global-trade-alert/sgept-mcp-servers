# DPA MCP Server - Quick Start Guide

Get the DPA (Digital Policy Alert) MCP server running in 5 minutes.

## Prerequisites

Before you begin, ensure you have:
- Python 3.10 or higher installed
- `uv` package manager installed ([get it here](https://github.com/astral-sh/uv))
- DPA API key from SGEPT (same key as GTA)

## Installation Steps

### 1. Navigate to Project Directory

```bash
cd /path/to/dpa-mcp
```

### 2. Install Dependencies

```bash
uv sync
```

This will install:
- `mcp>=1.0.0` - Model Context Protocol SDK
- `httpx>=0.27.0` - Async HTTP client
- `pydantic>=2.0.0` - Data validation

### 3. Set API Key

```bash
export DPA_API_KEY='your-api-key-here'
```

**Note:** You can add this to your `~/.bashrc` or `~/.zshrc` to make it permanent:
```bash
echo 'export DPA_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 4. Test the Server

```bash
# Verify server starts without errors
uv run dpa-mcp --help

# Test Python imports
uv run python -c "from dpa_mcp import server; print('✓ Server module loaded successfully')"
```

## Configure Claude Desktop

### 1. Locate Configuration File

On macOS:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 2. Add DPA Server Configuration

Edit the file and add the DPA server configuration:

```json
{
  "mcpServers": {
    "dpa": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/dpa-mcp",
        "run",
        "dpa-mcp"
      ],
      "env": {
        "DPA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/dpa-mcp` with the actual absolute path to your dpa-mcp directory.

### 3. Restart Claude Desktop

**Completely quit** Claude Desktop (not just close the window):
- Press `Cmd+Q` on macOS
- Or use Menu → Quit

Then reopen Claude Desktop.

## First Test Queries

Once Claude Desktop is running with the DPA server:

### Simple Search

```
Find recent AI regulations from the EU
```

Expected behavior: Claude will use `dpa_search_events` to search for AI-related events from the EU.

### Detailed Event Lookup

```
Get details for DPA event 20442
```

Expected behavior: Claude will use `dpa_get_event` to fetch complete information.

### Advanced Search

```
Search for data governance policies affecting cloud computing from 2024
```

Expected behavior: Claude will filter by policy area and economic activity.

## Verify Server is Working

In Claude Desktop, you should see:
1. **Tools available** when you ask about digital policy
2. **Responses with citations** in format `[ID [12345](url)]`
3. **Reference lists** at the end of responses

## Troubleshooting

### Server doesn't appear in Claude Desktop

**Solution:**
1. Check the absolute path in config is correct
2. Verify `DPA_API_KEY` is set in the env section
3. Completely quit and restart Claude Desktop
4. Check Claude Desktop logs for errors

### Authentication Error

**Solution:**
```bash
# Verify API key is set
echo $DPA_API_KEY

# Test API key manually
uv run python -c "
import os
import httpx
api_key = os.getenv('DPA_API_KEY')
headers = {'Authorization': f'APIKey {api_key}'}
response = httpx.post('https://api.globaltradealert.org/api/v1/dpa/events/',
                     headers=headers,
                     json={'limit': 1, 'offset': 0, 'request_data': {'event_period': ['2024-01-01', '2024-12-31']}},
                     timeout=30.0)
print(f'Status: {response.status_code}')
"
```

### Import Errors

**Solution:**
```bash
# Reinstall dependencies
uv sync --reinstall

# Verify Python version
python --version  # Should be 3.10+
```

### "Response truncated" messages

**Solution:** This is normal for large result sets. Use:
- `offset` parameter for pagination
- More specific filters to reduce results
- Date ranges to limit scope

## Next Steps

1. **Read Examples**: Check [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md) for real-world query patterns
2. **Explore Resources**: Learn about available resources in [README.md](./README.md#available-resources)
3. **Understand Tools**: Review tool parameters in [README.md](./README.md#available-tools)

## Quick Reference

### Environment Variables
```bash
export DPA_API_KEY='your-key-here'
```

### Test Commands
```bash
# Start server
uv run dpa-mcp

# Test imports
uv run python -c "from dpa_mcp import server; print('OK')"

# Reinstall dependencies
uv sync --reinstall
```

### Claude Desktop Config Location
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

---

**You're ready to go!** Try asking Claude about digital policy regulations and watch the DPA MCP server in action.
