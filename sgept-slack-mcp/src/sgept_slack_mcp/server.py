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
from .identities import IdentityConfig, IdentityRegistry, load_identities
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

# Identity registry and per-identity client instances (lazy initialization)
_registry: IdentityRegistry | None = None
_clients: dict[str, SlackAPIClient] = {}


def get_registry() -> IdentityRegistry:
    """Get the identity registry, loading on first call."""
    global _registry
    if _registry is None:
        _registry = load_identities()
    return _registry


def get_client(identity_name: str | None = None) -> tuple[SlackAPIClient, IdentityConfig]:
    """Get a Slack client for the specified identity (or default).

    Returns:
        Tuple of (client, identity_config) for the resolved identity.

    Raises:
        ValueError: If the identity doesn't exist or has no valid token.
    """
    registry = get_registry()
    identity = registry.resolve(identity_name)

    if identity.name not in _clients:
        _clients[identity.name] = SlackAPIClient(identity.token)

    return _clients[identity.name], identity


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
        client, _ = get_client(params.identity)
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
        client, _ = get_client(params.identity)
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
        client, _ = get_client(params.identity)
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
        client, _ = get_client(params.identity)
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
    try:
        client, identity = get_client(params.identity)

        # Security check: sending must be explicitly enabled for this identity
        if not identity.send_enabled:
            return (
                f"Error: Message sending is DISABLED for identity '{identity.name}'.\n\n"
                "This identity does not have send_enabled=true in identities.json.\n"
                "This is a security feature to prevent accidental messages."
            )

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
        client, _ = get_client(params.identity)
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
    try:
        registry = load_identities()
        # Pre-populate the global registry so tools don't need to reload
        global _registry
        _registry = registry
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Log startup (without revealing tokens)
    logger.info("Starting SGEPT Slack MCP Server (multi-identity)")
    logger.info(f"Identities loaded: {', '.join(registry.names)}")
    logger.info(f"Default identity: {registry.default_name}")
    for name in registry.names:
        identity = registry.resolve(name)
        send = "send=ON" if identity.send_enabled else "send=OFF"
        logger.info(f"  {name}: {identity.description} ({send})")

    # Run MCP server
    mcp.run()


if __name__ == "__main__":
    main()
