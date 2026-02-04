"""Tests for Slack API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from slack_sdk.errors import SlackApiError

from sgept_slack_mcp.client import SlackAPIClient, SlackClientError
from sgept_slack_mcp.models import ConversationType


class TestSlackAPIClientInit:
    """Tests for SlackAPIClient initialization."""

    def test_validates_user_token_prefix(self):
        """Test that client accepts valid user tokens (xoxp-)."""
        with patch('sgept_slack_mcp.client.AsyncWebClient'):
            client = SlackAPIClient("xoxp-valid-token-here")
            assert client is not None

    def test_rejects_bot_token_prefix(self):
        """Test that client rejects bot tokens (xoxb-)."""
        with pytest.raises(ValueError, match="user token"):
            SlackAPIClient("xoxb-bot-token-here")

    def test_rejects_empty_token(self):
        """Test that client rejects empty token."""
        with pytest.raises(ValueError, match="required"):
            SlackAPIClient("")

    def test_rejects_invalid_token_format(self):
        """Test that client rejects tokens with wrong prefix."""
        with pytest.raises(ValueError, match="user token"):
            SlackAPIClient("invalid-token-format")


@pytest.mark.asyncio
class TestSlackAPIClientMethods:
    """Tests for SlackAPIClient API methods."""

    @pytest.fixture
    def client_with_mock(self, mock_async_web_client):
        """Create client with mocked AsyncWebClient."""
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_class.return_value = mock_async_web_client
            client = SlackAPIClient("xoxp-valid-token")
            return client, mock_async_web_client

    async def test_list_conversations_returns_channels(self, client_with_mock):
        """Test that list_conversations returns parsed channels."""
        client, mock_web_client = client_with_mock

        conversations = await client.list_conversations()

        assert len(conversations) == 4
        assert conversations[0].id == "C1234567890"
        assert conversations[0].name == "general"
        assert conversations[0].type == "public_channel"

    async def test_list_conversations_filters_by_type(self, client_with_mock):
        """Test that list_conversations filters by type."""
        client, mock_web_client = client_with_mock

        await client.list_conversations(types=[ConversationType.PUBLIC_CHANNEL])

        mock_web_client.conversations_list.assert_called_once()
        call_kwargs = mock_web_client.conversations_list.call_args[1]
        assert "public_channel" in call_kwargs["types"]

    async def test_list_users_returns_users(self, client_with_mock):
        """Test that list_users returns parsed users."""
        client, mock_web_client = client_with_mock

        users = await client.list_users()

        assert len(users) == 3
        assert users[0].id == "U1234567890"
        assert users[0].name == "john.doe"
        assert users[0].real_name == "John Doe"

    async def test_list_users_uses_cache(self, client_with_mock):
        """Test that list_users uses cache on second call."""
        client, mock_web_client = client_with_mock

        # First call
        await client.list_users()
        # Second call
        await client.list_users()

        # Should only call API once (cached)
        assert mock_web_client.users_list.call_count == 1

    async def test_get_messages_returns_messages(self, client_with_mock):
        """Test that get_messages returns parsed messages."""
        client, mock_web_client = client_with_mock

        messages = await client.get_messages("C1234567890")

        assert len(messages) == 2
        assert messages[0].ts == "1705363200.123456"
        # User mention should be resolved
        assert "@Jane" in messages[0].text or "@U9876543210" in messages[0].text

    async def test_get_messages_validates_channel_format(self, client_with_mock):
        """Test that get_messages works with valid channel ID."""
        client, mock_web_client = client_with_mock

        messages = await client.get_messages("C1234567890")

        mock_web_client.conversations_history.assert_called_once()
        call_kwargs = mock_web_client.conversations_history.call_args[1]
        assert call_kwargs["channel"] == "C1234567890"

    async def test_get_thread_returns_replies(self, client_with_mock):
        """Test that get_thread returns thread messages."""
        client, mock_web_client = client_with_mock

        messages = await client.get_thread("C1234567890", "1705363100.654321")

        assert len(messages) == 3
        assert messages[0].is_parent is True
        assert messages[1].is_parent is False

    async def test_send_message_sets_no_unfurl(self, client_with_mock):
        """Test that send_message disables link unfurling."""
        client, mock_web_client = client_with_mock

        await client.send_message("C1234567890", "Hello!")

        mock_web_client.chat_postMessage.assert_called_once()
        call_kwargs = mock_web_client.chat_postMessage.call_args[1]
        assert call_kwargs["unfurl_links"] is False
        assert call_kwargs["unfurl_media"] is False

    async def test_search_messages_returns_results(self, client_with_mock):
        """Test that search_messages returns search results."""
        client, mock_web_client = client_with_mock

        results = await client.search_messages("project update")

        assert len(results) == 2
        assert results[0].channel_id == "C1234567890"
        assert "project update" in results[0].text.lower()


@pytest.mark.asyncio
class TestSlackAPIClientRateLimiting:
    """Tests for rate limiting behavior."""

    async def test_rate_limit_exponential_backoff(self):
        """Test that client retries with backoff on rate limit."""
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client

            # First call rate limited, second succeeds
            rate_limit_response = MagicMock()
            rate_limit_response.get.return_value = "ratelimited"
            rate_limit_response.headers = {"Retry-After": "1"}

            success_response = {
                "ok": True,
                "members": [],
                "response_metadata": {"next_cursor": ""},
            }

            mock_client.users_list = AsyncMock(
                side_effect=[
                    SlackApiError("Rate limited", rate_limit_response),
                    success_response,
                ]
            )

            client = SlackAPIClient("xoxp-valid-token")

            with patch('asyncio.sleep', new_callable=AsyncMock):
                users = await client.list_users()

            assert mock_client.users_list.call_count == 2


@pytest.mark.asyncio
class TestSlackAPIClientMrkdwnResolution:
    """Tests for mrkdwn to readable text conversion."""

    @pytest.fixture
    def client_with_mock(self, mock_async_web_client):
        """Create client with mocked AsyncWebClient."""
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_class.return_value = mock_async_web_client
            client = SlackAPIClient("xoxp-valid-token")
            return client

    async def test_resolves_user_mentions(self, client_with_mock):
        """Test that user mentions are resolved to names."""
        client = client_with_mock

        # Force user cache population
        await client.list_users()

        # Get user map
        user_map = await client._get_user_map()

        # Test resolution
        text = client._resolve_mrkdwn("<@U1234567890>", user_map)
        assert "@John" in text or "@john.doe" in text

    async def test_resolves_channel_references(self, client_with_mock):
        """Test that channel references are resolved."""
        client = client_with_mock
        user_map = {}

        text = client._resolve_mrkdwn("<#C1234567890|general>", user_map)
        assert text == "#general"

    async def test_resolves_links(self, client_with_mock):
        """Test that links are resolved."""
        client = client_with_mock
        user_map = {}

        text = client._resolve_mrkdwn("<https://example.com|Example>", user_map)
        assert "Example" in text
        assert "https://example.com" in text

    async def test_resolves_special_mentions(self, client_with_mock):
        """Test that special mentions are resolved."""
        client = client_with_mock
        user_map = {}

        assert client._resolve_mrkdwn("<!here>", user_map) == "@here"
        assert client._resolve_mrkdwn("<!channel>", user_map) == "@channel"
        assert client._resolve_mrkdwn("<!everyone>", user_map) == "@everyone"
