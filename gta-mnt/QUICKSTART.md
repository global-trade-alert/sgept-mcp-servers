# GTA-MNT Quickstart Guide

Get the Sancho Claudino automated review system running in 5 minutes.

---

## Prerequisites Checklist

- [ ] Python 3.10+ installed
- [ ] `uv` package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] GTA account credentials (email + password)
- [ ] AWS S3 credentials for GTA archives

---

## Installation (2 minutes)

```bash
# 1. Navigate to project directory
cd /Users/johannesfritz/Documents/GitHub/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/gta-mnt

# 2. Install dependencies
uv sync

# Expected output: "Installed 47 packages"
```

---

## Configuration (1 minute)

Create a `.env` file or export environment variables:

```bash
# Required for authentication
export GTA_AUTH_EMAIL="your-email@globaltradealert.org"
export GTA_AUTH_PASSWORD="your-password"

# Required for S3 source access
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
export AWS_S3_REGION="eu-west-1"
```

---

## Verify Installation (30 seconds)

```bash
# Test imports
uv run python -c "from gta_mnt import server; print('✅ Import successful')"

# Run test suite
uv run pytest -v

# Expected: "35 passed in 0.70s"
```

---

## Claude Desktop Integration (2 minutes)

### Step 1: Edit Config File

Open or create `~/.config/claude/claude_desktop_config.json`

### Step 2: Add Server Config

```json
{
  "mcpServers": {
    "gta-mnt": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/johannesfritz/Documents/GitHub/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/gta-mnt",
        "run",
        "gta-mnt"
      ],
      "env": {
        "GTA_AUTH_EMAIL": "your-email@globaltradealert.org",
        "GTA_AUTH_PASSWORD": "your-password",
        "AWS_ACCESS_KEY_ID": "your-aws-key",
        "AWS_SECRET_ACCESS_KEY": "your-aws-secret",
        "AWS_S3_REGION": "eu-west-1"
      }
    }
  }
}
```

**Important:** Replace placeholder values with your actual credentials.

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop to load the new server.

### Step 4: Verify Connection

In a new conversation, type: "List GTA Step 1 queue"

Claude should use the `gta_mnt_list_step1_queue` tool.

---

## First Review Workflow

Try this example conversation with Claude:

```
You: List the first 5 measures in the Step 1 queue

Claude: [Uses gta_mnt_list_step1_queue]
Returns table with IDs, titles, jurisdictions

You: Get details for measure 12345

Claude: [Uses gta_mnt_get_measure]
Shows full measure with interventions

You: Get the official source for this measure

Claude: [Uses gta_mnt_get_source]
Fetches from S3 or URL, extracts PDF/HTML text

You: Add an issue comment - the intervention type should be "Export tax" not "Subsidy"

Claude: [Uses formatters + gta_mnt_add_comment]
Creates structured markdown comment with source citation

You: Set status to "Under revision"

Claude: [Uses gta_mnt_set_status with status_id=6]
Updates measure status and creates log entry
```

---

## Available Tools (Quick Reference)

| Command | Tool |
|---------|------|
| "List Step 1 queue" | `gta_mnt_list_step1_queue` |
| "Get measure 12345" | `gta_mnt_get_measure` |
| "Get source for 12345" | `gta_mnt_get_source` |
| "Add comment to 12345" | `gta_mnt_add_comment` |
| "Set 12345 to revision" | `gta_mnt_set_status` |
| "Tag 12345 as reviewed" | `gta_mnt_add_framework` |
| "List comment templates" | `gta_mnt_list_templates` |

---

## Troubleshooting

### "Authentication failed"
- Check `GTA_AUTH_EMAIL` and `GTA_AUTH_PASSWORD`
- Verify account has API access
- Try manual login to https://www.globaltradealert.org first

### "S3 access denied"
- Check `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Verify region is `eu-west-1`
- Confirm IAM role has S3 read permissions

### "Tool not found"
- Restart Claude Desktop after editing config
- Verify `claude_desktop_config.json` syntax (use a JSON validator)
- Check server logs at `~/Library/Logs/Claude/mcp-server-gta-mnt.log`

### "PDF extraction returns empty"
- Scanned PDFs cannot be extracted
- Use URL fallback instead
- Tool will return clear error message

---

## Development Testing

### Run Server Locally (Standalone)

```bash
# Terminal mode (for debugging)
uv run gta-mnt

# Python module mode
uv run python -m gta_mnt.server

# Expected output: Server listening on stdio
```

### Run Tests

```bash
# All tests
uv run pytest -v

# Specific test file
uv run pytest tests/unit/test_api.py -v

# With coverage
uv run pytest --cov=gta_mnt --cov-report=term-missing
```

---

## Next Steps

1. **Review the README:** Full documentation in `README.md`
2. **Check UAT Protocol:** `.claude/protocols/uat-gta-mnt-mcp-server.md`
3. **Read Technical Spec:** `inbox/specs/SPEC-gta-mnt-mcp-server.md`
4. **Join team workflow:** Use framework_id=495 to track your reviews

---

## Support

- **Issues:** Create ticket in jf-private repository
- **Questions:** Ask in #gta-tech Slack channel
- **Updates:** Check `CHANGELOG.md` for version history

---

**Setup Time:** ~5 minutes
**First Review:** ~10 minutes
**Production Ready:** ✅ Yes
