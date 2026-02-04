"""SGEPT Slack MCP Server - Exposes Slack workspace via MCP protocol."""

import os
import sys
import logging
from mcp.server.fastmcp import FastMCP

from .models import (
    ListConversationsInput,
    ListUsersInput,
    GetMessagesInput,
    GetThreadInput,
    SendMessageInput,
    SearchMessagesInput,
    ResponseFormat,
)
from .client import SlackAPIClient, SlackClientError
from .formatters import (
    format_conversations_markdown,
    format_conversations_json,
    format_users_markdown,
    format_users_json,
    format_messages_markdown,
    format_messages_json,
    format_thread_markdown,
    format_thread_json,
    format_search_results_markdown,
    format_search_results_json,
    format_send_response_markdown,
    format_send_response_json,
)

# Configure logging - never log token values
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("sgept_slack_mcp")

# Global client instance (lazy initialization)
_slack_client: SlackAPIClient | None = None


def get_slack_client() -> SlackAPIClient:
    """
    Get initialized Slack client with token from environment.

    Raises:
        ValueError: If SLACK_USER_TOKEN is not set
    """
    global _slack_client

    if _slack_client is not None:
        return _slack_client

    token = os.getenv("SLACK_USER_TOKEN")
    if not token:
        raise ValueError(
            "SLACK_USER_TOKEN environment variable not set. "
            "Please set your Slack user token: export SLACK_USER_TOKEN='xoxp-...'"
        )

    _slack_client = SlackAPIClient(token)
    return _slack_client


def is_send_enabled() -> bool:
    """Check if send functionality is enabled (disabled by default for safety)."""
    return os.getenv("SLACK_ENABLE_SEND", "false").lower() == "true"


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool(
    name="slack_list_conversations",
    annotations={
        "title": "List Slack Conversations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def slack_list_conversations(params: ListConversationsInput) -> str:
    """List accessible Slack channels and DMs.

    Returns channels and direct messages the authenticated user can access.
    Use this to discover conversation IDs before fetching messages.

    Examples:
        - List all conversations: types=["public_channel","private_channel","im","mpim"]
        - List only channels: types=["public_channel","private_channel"]
        - List only DMs: types=["im","mpim"]
    """
    try:
        client = get_slack_client()
        conversations = await client.list_conversations(
            types=params.types,
            limit=params.limit,
        )

        if params.response_format == ResponseFormat.JSON:
            return format_conversations_json(conversations)
        return format_conversations_markdown(conversations)

    except (SlackClientError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool(
    name="slack_list_users",
    annotations={
        "title": "List Slack Users",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def slack_list_users(params: ListUsersInput) -> str:
    """List workspace users for name resolution.

    Returns users in the workspace. Results are cached for 5 minutes
    to reduce API calls.

    Use this to:
        - Find user IDs for mentions
        - Resolve user names from IDs
        - Identify bot vs human users
    """
    try:
        client = get_slack_client()
        users = await client.list_users(limit=params.limit)

        if params.response_format == ResponseFormat.JSON:
            return format_users_json(users)
        return format_users_markdown(users)

    except (SlackClientError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool(
    name="slack_get_messages",
    annotations={
        "title": "Get Slack Messages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def slack_get_messages(params: GetMessagesInput) -> str:
    """Fetch recent messages from a Slack conversation.

    Returns messages from a channel or DM, with user mentions resolved
    to readable names. Messages are returned newest first.

    Args:
        channel_id: Channel ID (C...), DM ID (D...), or Group DM ID (G...)
        limit: Number of messages (default: 20, max: 100)
        oldest: Only messages after this Unix timestamp
        latest: Only messages before this Unix timestamp
        include_thread_info: Include thread reply counts

    Examples:
        - Recent messages: channel_id="C1234567890", limit=20
        - Messages since yesterday: channel_id="C1234567890", oldest="1705363200.000000"
    """
    try:
        client = get_slack_client()
        messages = await client.get_messages(
            channel_id=params.channel_id,
            limit=params.limit,
            oldest=params.oldest,
            latest=params.latest,
            include_thread_info=params.include_thread_info,
        )

        if params.response_format == ResponseFormat.JSON:
            return format_messages_json(messages, params.channel_id)
        return format_messages_markdown(messages, params.channel_id)

    except (SlackClientError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool(
    name="slack_get_thread",
    annotations={
        "title": "Get Slack Thread",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def slack_get_thread(params: GetThreadInput) -> str:
    """Fetch all replies in a Slack thread.

    Returns the parent message and all replies in chronological order.
    The parent message is marked with [PARENT] in the output.

    Args:
        channel_id: Channel ID where the thread exists
        thread_ts: Thread parent timestamp (from message ts field)
        limit: Maximum replies to return (default: 50)

    Example:
        channel_id="C1234567890", thread_ts="1705363200.123456"
    """
    try:
        client = get_slack_client()
        messages = await client.get_thread(
            channel_id=params.channel_id,
            thread_ts=params.thread_ts,
            limit=params.limit,
        )

        if params.response_format == ResponseFormat.JSON:
            return format_thread_json(messages, params.channel_id, params.thread_ts)
        return format_thread_markdown(messages, params.channel_id, params.thread_ts)

    except (SlackClientError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool(
    name="slack_send_message",
    annotations={
        "title": "Send Slack Message",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def slack_send_message(params: SendMessageInput) -> str:
    """Send a message to a Slack channel or DM.

    WARNING: This tool is DISABLED by default for safety.
    Enable with environment variable: SLACK_ENABLE_SEND=true

    Security features:
        - Link unfurling is disabled (prevents preview vulnerabilities)
        - Media unfurling is disabled

    Args:
        channel_id: Channel or DM ID to send to
        text: Message text (supports Slack markdown)
        thread_ts: Reply in thread if provided (thread parent timestamp)

    Example:
        channel_id="C1234567890", text="Hello team!"
    """
    # Security check: sending must be explicitly enabled
    if not is_send_enabled():
        return (
            "Error: Message sending is DISABLED for safety.\n\n"
            "To enable, set the environment variable:\n"
            "  SLACK_ENABLE_SEND=true\n\n"
            "This is a security feature to prevent accidental messages."
        )

    try:
        client = get_slack_client()
        response = await client.send_message(
            channel_id=params.channel_id,
            text=params.text,
            thread_ts=params.thread_ts,
        )

        return format_send_response_markdown(response)

    except (SlackClientError, ValueError) as e:
        return f"Error: {e}"


@mcp.tool(
    name="slack_search_messages",
    annotations={
        "title": "Search Slack Messages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def slack_search_messages(params: SearchMessagesInput) -> str:
    """Search messages across the Slack workspace.

    Supports Slack's search syntax for filtering results.

    Args:
        query: Search query (supports Slack search syntax)
        limit: Maximum results (default: 20, max: 100)
        sort: Sort by 'timestamp' (newest first) or 'score' (most relevant)

    Search syntax examples:
        - Basic search: "project update"
        - From user: "from:@john project"
        - In channel: "in:#general meeting"
        - Date range: "after:2024-01-01 before:2024-02-01"
        - Has link: "has:link announcement"
        - Combined: "from:@alice in:#engineering bug fix"
    """
    try:
        client = get_slack_client()
        results = await client.search_messages(
            query=params.query,
            limit=params.limit,
            sort=params.sort.value,
        )

        if params.response_format == ResponseFormat.JSON:
            return format_search_results_json(results, params.query)
        return format_search_results_markdown(results, params.query)

    except (SlackClientError, ValueError) as e:
        return f"Error: {e}"


# ============================================================================
# MCP Resources (Optional reference data)
# ============================================================================

@mcp.resource("slack://help/search-syntax")
def get_search_syntax_help() -> str:
    """Slack search syntax reference."""
    return """# Slack Search Syntax

## Basic Operators
- `"exact phrase"` - Match exact phrase
- `word1 word2` - Match both words (AND)
- `word1 OR word2` - Match either word

## Filters
- `from:@username` - Messages from user
- `from:me` - Messages from yourself
- `in:#channel` - Messages in channel
- `in:@username` - Messages in DM with user
- `to:@username` - Messages mentioning user

## Date Filters
- `after:YYYY-MM-DD` - Messages after date
- `before:YYYY-MM-DD` - Messages before date
- `on:YYYY-MM-DD` - Messages on date
- `during:month` - Messages during month (e.g., during:january)

## Content Filters
- `has:link` - Messages with links
- `has:reaction` - Messages with reactions
- `has::emoji:` - Messages with specific emoji reaction
- `has:pin` - Pinned messages
- `has:star` - Starred messages

## Examples
- `from:@alice in:#engineering bug` - Alice's bug mentions in #engineering
- `has:link after:2024-01-01` - Links shared this year
- `"quarterly report" in:#leadership` - Exact phrase in #leadership
"""


@mcp.resource("slack://help/channel-types")
def get_channel_types_help() -> str:
    """Slack channel types reference."""
    return """# Slack Channel Types

## Channel ID Prefixes
- `C` - Public channel (e.g., C1234567890)
- `G` - Private channel or Group DM (e.g., G1234567890)
- `D` - Direct Message (e.g., D1234567890)
- `W` - Enterprise Grid workspace channel

## Conversation Types
- `public_channel` - Open to all workspace members
- `private_channel` - Invite-only channel
- `im` - Direct message (1:1)
- `mpim` - Multi-person direct message (group DM)

## Notes
- Private channels and DMs require membership to access
- Archived channels are excluded by default
- Bot users have limited access to some channel types
"""


def main() -> None:
    """Run the MCP server."""
    # Validate token is present at startup
    token = os.getenv("SLACK_USER_TOKEN")
    if not token:
        print(
            "ERROR: SLACK_USER_TOKEN environment variable not set.\n"
            "Please set your Slack user token:\n"
            "  export SLACK_USER_TOKEN='xoxp-...'\n",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate token format
    if not token.startswith("xoxp-"):
        print(
            "ERROR: Invalid token format.\n"
            "SLACK_USER_TOKEN must be a user token (starts with 'xoxp-').\n"
            "Bot tokens (xoxb-) are not supported.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    # Log startup (without revealing token)
    send_status = "ENABLED" if is_send_enabled() else "DISABLED (default)"
    logger.info(f"Starting SGEPT Slack MCP Server")
    logger.info(f"Message sending: {send_status}")

    # Run MCP server
    mcp.run()


if __name__ == "__main__":
    main()
