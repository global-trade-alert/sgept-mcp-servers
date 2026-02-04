"""Tests for MCP tool implementations."""

import os
import pytest
from unittest.mock import patch, AsyncMock

from sgept_slack_mcp.server import (
    slack_list_conversations,
    slack_list_users,
    slack_get_messages,
    slack_get_thread,
    slack_send_message,
    slack_search_messages,
    get_slack_client,
)
from sgept_slack_mcp.models import (
    ListConversationsInput,
    ListUsersInput,
    GetMessagesInput,
    GetThreadInput,
    SendMessageInput,
    SearchMessagesInput,
    ConversationType,
    SortOrder,
    ResponseFormat,
)


@pytest.fixture
def mock_slack_client(mock_async_web_client):
    """Patch get_slack_client to return mocked client."""
    with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
        mock_class.return_value = mock_async_web_client

        # Reset the global client
        import sgept_slack_mcp.server as server_module
        server_module._slack_client = None

        with patch.dict(os.environ, {"SLACK_USER_TOKEN": "xoxp-test-token"}):
            yield mock_async_web_client


@pytest.mark.asyncio
class TestSlackListConversations:
    """Tests for slack_list_conversations tool."""

    async def test_returns_conversations(self, mock_slack_client):
        """Test that tool returns formatted conversations."""
        params = ListConversationsInput()

        result = await slack_list_conversations(params)

        assert "general" in result
        assert "C1234567890" in result

    async def test_filters_by_type(self, mock_slack_client):
        """Test that tool filters by conversation type."""
        params = ListConversationsInput(types=[ConversationType.PUBLIC_CHANNEL])

        result = await slack_list_conversations(params)

        mock_slack_client.conversations_list.assert_called()

    async def test_json_format(self, mock_slack_client):
        """Test that tool returns JSON when requested."""
        params = ListConversationsInput(response_format=ResponseFormat.JSON)

        result = await slack_list_conversations(params)

        assert '"conversations"' in result
        assert '"id"' in result

    async def test_handles_missing_token(self):
        """Test that tool handles missing token gracefully."""
        import sgept_slack_mcp.server as server_module
        server_module._slack_client = None

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SLACK_USER_TOKEN", None)

            params = ListConversationsInput()
            result = await slack_list_conversations(params)

            assert "Error" in result
            assert "SLACK_USER_TOKEN" in result


@pytest.mark.asyncio
class TestSlackListUsers:
    """Tests for slack_list_users tool."""

    async def test_returns_users(self, mock_slack_client):
        """Test that tool returns formatted users."""
        params = ListUsersInput()

        result = await slack_list_users(params)

        assert "john.doe" in result
        assert "U1234567890" in result

    async def test_json_format(self, mock_slack_client):
        """Test that tool returns JSON when requested."""
        params = ListUsersInput(response_format=ResponseFormat.JSON)

        result = await slack_list_users(params)

        assert '"users"' in result
        assert '"id"' in result


@pytest.mark.asyncio
class TestSlackGetMessages:
    """Tests for slack_get_messages tool."""

    async def test_returns_messages(self, mock_slack_client):
        """Test that tool returns formatted messages."""
        params = GetMessagesInput(channel_id="C1234567890")

        result = await slack_get_messages(params)

        assert "1705363200.123456" in result
        assert "Messages" in result

    async def test_with_oldest_filter(self, mock_slack_client):
        """Test that tool passes oldest parameter."""
        params = GetMessagesInput(
            channel_id="C1234567890",
            oldest="1705363000.000000"
        )

        await slack_get_messages(params)

        mock_slack_client.conversations_history.assert_called()
        call_kwargs = mock_slack_client.conversations_history.call_args[1]
        assert call_kwargs["oldest"] == "1705363000.000000"

    async def test_json_format(self, mock_slack_client):
        """Test that tool returns JSON when requested."""
        params = GetMessagesInput(
            channel_id="C1234567890",
            response_format=ResponseFormat.JSON
        )

        result = await slack_get_messages(params)

        assert '"messages"' in result
        assert '"channel_id"' in result


@pytest.mark.asyncio
class TestSlackGetThread:
    """Tests for slack_get_thread tool."""

    async def test_returns_thread(self, mock_slack_client):
        """Test that tool returns formatted thread."""
        params = GetThreadInput(
            channel_id="C1234567890",
            thread_ts="1705363100.654321"
        )

        result = await slack_get_thread(params)

        assert "Thread" in result
        assert "1705363100.654321" in result

    async def test_json_format(self, mock_slack_client):
        """Test that tool returns JSON when requested."""
        params = GetThreadInput(
            channel_id="C1234567890",
            thread_ts="1705363100.654321",
            response_format=ResponseFormat.JSON
        )

        result = await slack_get_thread(params)

        assert '"thread_ts"' in result
        assert '"messages"' in result


@pytest.mark.asyncio
class TestSlackSendMessage:
    """Tests for slack_send_message tool."""

    async def test_blocked_when_disabled(self, mock_slack_client):
        """Test that sending is blocked when disabled."""
        with patch.dict(os.environ, {"SLACK_ENABLE_SEND": "false"}):
            params = SendMessageInput(
                channel_id="C1234567890",
                text="Hello!"
            )

            result = await slack_send_message(params)

            assert "DISABLED" in result
            # Should not call API
            mock_slack_client.chat_postMessage.assert_not_called()

    async def test_works_when_enabled(self, mock_slack_client):
        """Test that sending works when enabled."""
        with patch.dict(os.environ, {
            "SLACK_USER_TOKEN": "xoxp-test-token",
            "SLACK_ENABLE_SEND": "true"
        }):
            # Reset client to pick up new env
            import sgept_slack_mcp.server as server_module
            server_module._slack_client = None

            params = SendMessageInput(
                channel_id="C1234567890",
                text="Hello!"
            )

            result = await slack_send_message(params)

            assert "Successfully" in result or "ok" in result.lower()
            mock_slack_client.chat_postMessage.assert_called()

    async def test_thread_reply(self, mock_slack_client):
        """Test sending a thread reply."""
        with patch.dict(os.environ, {
            "SLACK_USER_TOKEN": "xoxp-test-token",
            "SLACK_ENABLE_SEND": "true"
        }):
            import sgept_slack_mcp.server as server_module
            server_module._slack_client = None

            params = SendMessageInput(
                channel_id="C1234567890",
                text="Thread reply!",
                thread_ts="1705363100.654321"
            )

            await slack_send_message(params)

            mock_slack_client.chat_postMessage.assert_called()
            call_kwargs = mock_slack_client.chat_postMessage.call_args[1]
            assert call_kwargs["thread_ts"] == "1705363100.654321"


@pytest.mark.asyncio
class TestSlackSearchMessages:
    """Tests for slack_search_messages tool."""

    async def test_returns_results(self, mock_slack_client):
        """Test that tool returns formatted search results."""
        params = SearchMessagesInput(query="project update")

        result = await slack_search_messages(params)

        assert "Search Results" in result or "results" in result.lower()
        assert "project" in result.lower()

    async def test_sort_by_score(self, mock_slack_client):
        """Test searching with sort by score."""
        params = SearchMessagesInput(
            query="project",
            sort=SortOrder.SCORE
        )

        await slack_search_messages(params)

        mock_slack_client.search_messages.assert_called()
        call_kwargs = mock_slack_client.search_messages.call_args[1]
        assert call_kwargs["sort"] == "score"

    async def test_json_format(self, mock_slack_client):
        """Test that tool returns JSON when requested."""
        params = SearchMessagesInput(
            query="project",
            response_format=ResponseFormat.JSON
        )

        result = await slack_search_messages(params)

        assert '"query"' in result
        assert '"results"' in result
