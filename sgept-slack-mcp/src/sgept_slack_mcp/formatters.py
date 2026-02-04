"""Response formatters for Slack MCP server outputs."""

import json
from typing import Any

from .models import (
    SlackConversation,
    SlackUser,
    SlackMessage,
    SlackSearchResult,
    SendMessageResponse,
)

# Character limit for responses (prevent context overflow)
CHARACTER_LIMIT = 25000


def truncate_response(content: str, limit: int = CHARACTER_LIMIT) -> str:
    """Truncate response if it exceeds character limit."""
    if len(content) <= limit:
        return content

    truncated = content[:limit]
    return f"{truncated}\n\n... (truncated, {len(content) - limit} characters omitted)"


# ============================================================================
# Conversation Formatters
# ============================================================================

def format_conversations_markdown(conversations: list[SlackConversation]) -> str:
    """Format conversations as markdown table."""
    if not conversations:
        return "No conversations found."

    lines = [
        "## Slack Conversations",
        "",
        f"Found {len(conversations)} conversation(s):",
        "",
        "| Type | Name/User | ID | Member |",
        "|------|-----------|----|---------| ",
    ]

    for conv in conversations:
        name = conv.name or conv.user_name or "(DM)"
        member = "Yes" if conv.is_member else "No"
        lines.append(f"| {conv.type} | {name} | `{conv.id}` | {member} |")

    return truncate_response("\n".join(lines))


def format_conversations_json(conversations: list[SlackConversation]) -> str:
    """Format conversations as JSON."""
    data = {
        "count": len(conversations),
        "conversations": [conv.model_dump() for conv in conversations]
    }
    return truncate_response(json.dumps(data, indent=2))


# ============================================================================
# User Formatters
# ============================================================================

def format_users_markdown(users: list[SlackUser]) -> str:
    """Format users as markdown table."""
    if not users:
        return "No users found."

    lines = [
        "## Slack Users",
        "",
        f"Found {len(users)} user(s):",
        "",
        "| Name | Real Name | Display Name | ID | Bot |",
        "|------|-----------|--------------|----|----|",
    ]

    for user in users:
        bot = "Yes" if user.is_bot else "No"
        lines.append(
            f"| {user.name} | {user.real_name or '-'} | {user.display_name or '-'} | `{user.id}` | {bot} |"
        )

    return truncate_response("\n".join(lines))


def format_users_json(users: list[SlackUser]) -> str:
    """Format users as JSON."""
    data = {
        "count": len(users),
        "users": [user.model_dump() for user in users]
    }
    return truncate_response(json.dumps(data, indent=2))


# ============================================================================
# Message Formatters
# ============================================================================

def format_messages_markdown(
    messages: list[SlackMessage],
    channel_id: str,
) -> str:
    """Format messages as markdown."""
    if not messages:
        return f"No messages found in channel `{channel_id}`."

    lines = [
        f"## Messages from `{channel_id}`",
        "",
        f"Showing {len(messages)} message(s):",
        "",
    ]

    for msg in messages:
        user = msg.user_name or msg.user_id or "Unknown"
        thread_info = ""
        if msg.thread_ts and msg.reply_count > 0:
            thread_info = f" [{msg.reply_count} replies]"

        lines.append(f"**{user}** ({msg.timestamp}){thread_info}")
        lines.append(f"> {msg.text}")
        lines.append(f"_ts: `{msg.ts}`_")
        lines.append("")

    return truncate_response("\n".join(lines))


def format_messages_json(
    messages: list[SlackMessage],
    channel_id: str,
) -> str:
    """Format messages as JSON."""
    data = {
        "channel_id": channel_id,
        "count": len(messages),
        "messages": [msg.model_dump() for msg in messages]
    }
    return truncate_response(json.dumps(data, indent=2))


# ============================================================================
# Thread Formatters
# ============================================================================

def format_thread_markdown(
    messages: list[SlackMessage],
    channel_id: str,
    thread_ts: str,
) -> str:
    """Format thread as markdown."""
    if not messages:
        return f"No messages found in thread `{thread_ts}` in channel `{channel_id}`."

    lines = [
        f"## Thread in `{channel_id}`",
        f"Thread: `{thread_ts}`",
        "",
        f"Showing {len(messages)} message(s):",
        "",
    ]

    for msg in messages:
        user = msg.user_name or msg.user_id or "Unknown"
        prefix = "[PARENT] " if msg.is_parent else "  "

        lines.append(f"{prefix}**{user}** ({msg.timestamp})")
        lines.append(f"{prefix}> {msg.text}")
        lines.append(f"{prefix}_ts: `{msg.ts}`_")
        lines.append("")

    return truncate_response("\n".join(lines))


def format_thread_json(
    messages: list[SlackMessage],
    channel_id: str,
    thread_ts: str,
) -> str:
    """Format thread as JSON."""
    data = {
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "count": len(messages),
        "messages": [msg.model_dump() for msg in messages]
    }
    return truncate_response(json.dumps(data, indent=2))


# ============================================================================
# Search Result Formatters
# ============================================================================

def format_search_results_markdown(
    results: list[SlackSearchResult],
    query: str,
) -> str:
    """Format search results as markdown."""
    if not results:
        return f"No messages found matching: `{query}`"

    lines = [
        f"## Search Results",
        f"Query: `{query}`",
        "",
        f"Found {len(results)} result(s):",
        "",
    ]

    for result in results:
        user = result.user_name or result.user_id or "Unknown"
        channel = result.channel_name or result.channel_id

        lines.append(f"**{user}** in #{channel} ({result.timestamp})")
        lines.append(f"> {result.text}")
        if result.permalink:
            lines.append(f"[View in Slack]({result.permalink})")
        lines.append(f"_ts: `{result.ts}`_")
        lines.append("")

    return truncate_response("\n".join(lines))


def format_search_results_json(
    results: list[SlackSearchResult],
    query: str,
) -> str:
    """Format search results as JSON."""
    data = {
        "query": query,
        "count": len(results),
        "results": [result.model_dump() for result in results]
    }
    return truncate_response(json.dumps(data, indent=2))


# ============================================================================
# Send Message Formatters
# ============================================================================

def format_send_response_markdown(response: SendMessageResponse) -> str:
    """Format send message response as markdown."""
    if response.ok:
        return (
            f"## Message Sent Successfully\n\n"
            f"- Channel: `{response.channel_id}`\n"
            f"- Message ID: `{response.ts}`"
        )
    else:
        return f"## Failed to Send Message\n\nError: {response.error}"


def format_send_response_json(response: SendMessageResponse) -> str:
    """Format send message response as JSON."""
    return json.dumps(response.model_dump(), indent=2)
