"""Shared test fixtures for SGEPT Slack MCP Server tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_slack_response_conversations():
    """Sample conversations.list response."""
    return {
        "ok": True,
        "channels": [
            {
                "id": "C1234567890",
                "name": "general",
                "is_channel": True,
                "is_private": False,
                "is_member": True,
            },
            {
                "id": "C9876543210",
                "name": "random",
                "is_channel": True,
                "is_private": False,
                "is_member": True,
            },
            {
                "id": "G1111111111",
                "name": "secret-project",
                "is_channel": True,
                "is_private": True,
                "is_member": True,
            },
            {
                "id": "D2222222222",
                "user": "U1234567890",
                "is_im": True,
                "is_member": True,
            },
        ],
        "response_metadata": {"next_cursor": ""},
    }


@pytest.fixture
def mock_slack_response_users():
    """Sample users.list response."""
    return {
        "ok": True,
        "members": [
            {
                "id": "U1234567890",
                "name": "john.doe",
                "deleted": False,
                "is_bot": False,
                "profile": {
                    "real_name": "John Doe",
                    "display_name": "John",
                },
            },
            {
                "id": "U9876543210",
                "name": "jane.smith",
                "deleted": False,
                "is_bot": False,
                "profile": {
                    "real_name": "Jane Smith",
                    "display_name": "Jane",
                },
            },
            {
                "id": "UBOT1234567",
                "name": "slackbot",
                "deleted": False,
                "is_bot": True,
                "profile": {
                    "real_name": "Slackbot",
                    "display_name": "Slackbot",
                },
            },
        ],
        "response_metadata": {"next_cursor": ""},
    }


@pytest.fixture
def mock_slack_response_messages():
    """Sample conversations.history response."""
    return {
        "ok": True,
        "messages": [
            {
                "ts": "1705363200.123456",
                "user": "U1234567890",
                "text": "Hello <@U9876543210>! Check out <https://example.com|this link>",
            },
            {
                "ts": "1705363100.654321",
                "user": "U9876543210",
                "text": "Thanks <!here>! Meeting in <#C1234567890|general>",
                "thread_ts": "1705363100.654321",
                "reply_count": 3,
            },
        ],
        "response_metadata": {"next_cursor": ""},
    }


@pytest.fixture
def mock_slack_response_thread():
    """Sample conversations.replies response."""
    return {
        "ok": True,
        "messages": [
            {
                "ts": "1705363100.654321",
                "user": "U9876543210",
                "text": "Parent message",
                "thread_ts": "1705363100.654321",
            },
            {
                "ts": "1705363150.111111",
                "user": "U1234567890",
                "text": "First reply",
                "thread_ts": "1705363100.654321",
            },
            {
                "ts": "1705363200.222222",
                "user": "U9876543210",
                "text": "Second reply",
                "thread_ts": "1705363100.654321",
            },
        ],
        "response_metadata": {"next_cursor": ""},
    }


@pytest.fixture
def mock_slack_response_search():
    """Sample search.messages response."""
    return {
        "ok": True,
        "messages": {
            "total": 2,
            "matches": [
                {
                    "ts": "1705363200.123456",
                    "user": "U1234567890",
                    "text": "Found this interesting project update",
                    "channel": {"id": "C1234567890", "name": "general"},
                    "permalink": "https://workspace.slack.com/archives/C1234567890/p1705363200123456",
                    "score": 0.95,
                },
                {
                    "ts": "1705362000.789012",
                    "user": "U9876543210",
                    "text": "Another project update here",
                    "channel": {"id": "C9876543210", "name": "random"},
                    "permalink": "https://workspace.slack.com/archives/C9876543210/p1705362000789012",
                    "score": 0.85,
                },
            ],
        },
    }


@pytest.fixture
def mock_slack_response_send():
    """Sample chat.postMessage response."""
    return {
        "ok": True,
        "ts": "1705363300.111111",
        "channel": "C1234567890",
    }


@pytest.fixture
def mock_async_web_client(
    mock_slack_response_conversations,
    mock_slack_response_users,
    mock_slack_response_messages,
    mock_slack_response_thread,
    mock_slack_response_search,
    mock_slack_response_send,
):
    """Create a mock AsyncWebClient with all responses configured."""
    mock_client = AsyncMock()

    # Configure method responses
    mock_client.conversations_list = AsyncMock(return_value=mock_slack_response_conversations)
    mock_client.users_list = AsyncMock(return_value=mock_slack_response_users)
    mock_client.conversations_history = AsyncMock(return_value=mock_slack_response_messages)
    mock_client.conversations_replies = AsyncMock(return_value=mock_slack_response_thread)
    mock_client.search_messages = AsyncMock(return_value=mock_slack_response_search)
    mock_client.chat_postMessage = AsyncMock(return_value=mock_slack_response_send)

    return mock_client
