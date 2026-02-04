# SGEPT Slack MCP Server

MCP server for Slack workspace integration. Provides read access to Slack messages, channels, and search functionality via the Model Context Protocol.

## Features

- **List Conversations** - Browse public/private channels, DMs, and group DMs
- **List Users** - Get workspace members with cached lookups (5-minute TTL)
- **Get Messages** - Fetch messages from any accessible conversation
- **Get Thread** - Retrieve complete thread with all replies
- **Search Messages** - Full-text search across the workspace
- **Send Messages** - Post messages (disabled by default for safety)

## Security

This server was built as a secure replacement for the deprecated `@anthropic-community/slack-mcp-server`, which was archived due to security vulnerabilities.

Key security features:
- **Message sending disabled by default** - Must explicitly enable with `SLACK_ENABLE_SEND=true`
- **No link unfurling** - Prevents the vulnerability that affected the original server
- **User tokens only** - Bot tokens (xoxb-*) are rejected
- **Token never logged** - Token values are never written to logs or error messages
- **Input validation** - All inputs validated via Pydantic models

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Slack user OAuth token with required scopes

### Install

```bash
cd sgept-slack-mcp
uv sync
```

## OAuth Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name it (e.g., "MCP Slack Access") and select your workspace

### 2. Configure OAuth Scopes

Navigate to **OAuth & Permissions** and add these **User Token Scopes**:

#### Required Scopes (Read-Only Mode)

| Scope | Purpose |
|-------|---------|
| `channels:read` | List public channels |
| `channels:history` | Read public channel messages |
| `groups:read` | List private channels |
| `groups:history` | Read private channel messages |
| `im:read` | List direct messages |
| `im:history` | Read DM messages |
| `mpim:read` | List group DMs |
| `mpim:history` | Read group DM messages |
| `users:read` | List workspace users |
| `search:read` | Search messages |

#### Optional Scope (For Message Sending)

| Scope | Purpose |
|-------|---------|
| `chat:write` | Send messages (requires `SLACK_ENABLE_SEND=true`) |

### 3. Install App to Workspace

1. Click **Install to Workspace** and authorize
2. Copy the **User OAuth Token** (starts with `xoxp-`)

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_USER_TOKEN` | Yes | - | User OAuth token (xoxp-*) |
| `SLACK_ENABLE_SEND` | No | `false` | Enable message sending |

### Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "slack": {
      "command": "uv",
      "args": ["--directory", "/path/to/sgept-slack-mcp", "run", "sgept-slack-mcp"],
      "env": {
        "SLACK_USER_TOKEN": "xoxp-your-token-here",
        "SLACK_ENABLE_SEND": "false"
      }
    }
  }
}
```

### Claude Code Integration

Add to your MCP config (`~/.claude/.mcp.json`):

```json
{
  "mcpServers": {
    "slack": {
      "command": "uv",
      "args": ["--directory", "/path/to/sgept-slack-mcp", "run", "sgept-slack-mcp"],
      "env": {
        "SLACK_USER_TOKEN": "xoxp-your-token-here"
      }
    }
  }
}
```

## Tools Reference

### slack_list_conversations

List accessible channels and DMs.

**Parameters:**
- `types` (optional): Filter by type - `["public_channel", "private_channel", "im", "mpim"]`
- `limit` (optional): Max results (default: 100, max: 1000)
- `response_format` (optional): `"markdown"` or `"json"`

**Example:**
```
List all my Slack channels
```

### slack_list_users

List workspace users (cached for 5 minutes).

**Parameters:**
- `limit` (optional): Max results (default: 200)
- `response_format` (optional): `"markdown"` or `"json"`

**Example:**
```
Who are the users in my Slack workspace?
```

### slack_get_messages

Fetch messages from a conversation.

**Parameters:**
- `channel_id` (required): Channel ID (e.g., `C1234567890`)
- `limit` (optional): Number of messages (default: 20, max: 100)
- `oldest` (optional): Unix timestamp - only messages after this
- `latest` (optional): Unix timestamp - only messages before this
- `include_thread_info` (optional): Include thread reply counts
- `response_format` (optional): `"markdown"` or `"json"`

**Example:**
```
Get the last 20 messages from channel C1234567890
```

### slack_get_thread

Fetch all replies in a thread.

**Parameters:**
- `channel_id` (required): Channel ID
- `thread_ts` (required): Thread parent timestamp
- `limit` (optional): Max replies (default: 50)
- `response_format` (optional): `"markdown"` or `"json"`

**Example:**
```
Get the thread at 1705363100.654321 in channel C1234567890
```

### slack_search_messages

Search messages across the workspace.

**Parameters:**
- `query` (required): Search query (supports Slack search syntax)
- `limit` (optional): Max results (default: 20, max: 100)
- `sort` (optional): `"timestamp"` or `"score"`
- `response_format` (optional): `"markdown"` or `"json"`

**Search Syntax:**
- `from:@username` - Messages from user
- `in:#channel` - Messages in channel
- `after:2024-01-01` - Messages after date
- `has:link` - Messages with links

**Example:**
```
Search for "project update" from @alice in #engineering
```

### slack_send_message

Send a message (requires `SLACK_ENABLE_SEND=true`).

**Parameters:**
- `channel_id` (required): Channel or DM ID
- `text` (required): Message text
- `thread_ts` (optional): Reply in thread

**Example:**
```
Send "Hello team!" to channel C1234567890
```

## Resources

The server also provides MCP resources for reference:

- `slack://help/search-syntax` - Slack search syntax reference
- `slack://help/channel-types` - Channel ID prefixes and types

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=sgept_slack_mcp

# Run specific test file
uv run pytest tests/test_security.py -v
```

## Troubleshooting

### "SLACK_USER_TOKEN environment variable not set"

Set your token in the environment or MCP config:
```bash
export SLACK_USER_TOKEN="xoxp-your-token"
```

### "Invalid token format: must be a user token (xoxp-*)"

This server only supports user tokens. Bot tokens (xoxb-*) are not supported.
Get a user token from your Slack app's OAuth settings.

### "Missing OAuth permission: channels:history"

Your token is missing required scopes. Re-authorize your Slack app with the required scopes listed above.

### "Channel not found"

Either:
- The channel ID is incorrect
- You're not a member of the channel
- The channel is in a different workspace

### "Rate limited by Slack"

The server automatically retries with exponential backoff. If you see this frequently, reduce your request rate.

### "Message sending is DISABLED"

Set `SLACK_ENABLE_SEND=true` in your environment or MCP config to enable sending.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client (Claude)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (FastMCP)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Tools: list_conversations, list_users, get_messages,  │  │
│  │        get_thread, send_message, search_messages      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Slack API Client                           │
│  • Pagination (auto-fetch all pages)                        │
│  • Rate limiting (exponential backoff)                      │
│  • User cache (5-minute TTL)                                │
│  • mrkdwn resolution (@user, #channel, links)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Slack Web API                            │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT
