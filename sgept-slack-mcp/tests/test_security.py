"""Security tests for SGEPT Slack MCP Server."""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import logging

from sgept_slack_mcp.client import SlackAPIClient
from sgept_slack_mcp.server import is_send_enabled, slack_send_message
from sgept_slack_mcp.models import SendMessageInput


class TestTokenSecurity:
    """Tests for token security."""

    def test_invalid_token_prefix_rejected(self):
        """Test that bot tokens are rejected."""
        with pytest.raises(ValueError, match="user token"):
            SlackAPIClient("xoxb-bot-token")

    def test_empty_token_rejected(self):
        """Test that empty tokens are rejected."""
        with pytest.raises(ValueError, match="required"):
            SlackAPIClient("")

    def test_token_not_in_error_message(self):
        """Test that token value doesn't appear in error messages."""
        secret_token = "xoxp-secret-12345-67890-abcdef"

        try:
            # Invalid prefix should raise error
            SlackAPIClient("invalid-prefix-token")
        except ValueError as e:
            error_msg = str(e)
            assert "invalid-prefix-token" not in error_msg
            assert "secret" not in error_msg.lower()


class TestSendProtection:
    """Tests for message send protection."""

    def test_send_disabled_by_default(self):
        """Test that sending is disabled when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove SLACK_ENABLE_SEND if present
            os.environ.pop("SLACK_ENABLE_SEND", None)
            assert is_send_enabled() is False

    def test_send_disabled_when_false(self):
        """Test that sending is disabled when env var is 'false'."""
        with patch.dict(os.environ, {"SLACK_ENABLE_SEND": "false"}):
            assert is_send_enabled() is False

    def test_send_enabled_when_true(self):
        """Test that sending is enabled when env var is 'true'."""
        with patch.dict(os.environ, {"SLACK_ENABLE_SEND": "true"}):
            assert is_send_enabled() is True

    def test_send_enabled_case_insensitive(self):
        """Test that env var check is case insensitive."""
        with patch.dict(os.environ, {"SLACK_ENABLE_SEND": "TRUE"}):
            assert is_send_enabled() is True

        with patch.dict(os.environ, {"SLACK_ENABLE_SEND": "True"}):
            assert is_send_enabled() is True

    @pytest.mark.asyncio
    async def test_send_message_blocked_when_disabled(self):
        """Test that send_message returns error when disabled."""
        with patch.dict(os.environ, {"SLACK_ENABLE_SEND": "false"}):
            params = SendMessageInput(
                channel_id="C1234567890",
                text="Test message"
            )

            result = await slack_send_message(params)

            assert "DISABLED" in result
            assert "SLACK_ENABLE_SEND" in result


class TestNoLinkUnfurling:
    """Tests for link unfurling protection."""

    @pytest.mark.asyncio
    async def test_send_message_disables_unfurling(self):
        """Test that send_message sets unfurl flags to False."""
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_client = AsyncMock()
            mock_client.chat_postMessage = AsyncMock(return_value={
                "ok": True,
                "ts": "1234567890.123456",
                "channel": "C1234567890",
            })
            mock_class.return_value = mock_client

            client = SlackAPIClient("xoxp-valid-token")
            await client.send_message("C1234567890", "Hello!")

            mock_client.chat_postMessage.assert_called_once()
            call_kwargs = mock_client.chat_postMessage.call_args[1]

            # CRITICAL: These must be False to prevent unfurling vulnerabilities
            assert call_kwargs["unfurl_links"] is False
            assert call_kwargs["unfurl_media"] is False


class TestInputValidation:
    """Tests for input validation."""

    def test_channel_id_format_validation(self):
        """Test that channel ID format is validated by Pydantic model."""
        from sgept_slack_mcp.models import GetMessagesInput
        from pydantic import ValidationError

        # Valid channel IDs
        GetMessagesInput(channel_id="C1234567890")  # Public channel
        GetMessagesInput(channel_id="D1234567890")  # DM
        GetMessagesInput(channel_id="G1234567890")  # Private/Group

        # Invalid channel IDs should raise validation error
        with pytest.raises(ValidationError):
            GetMessagesInput(channel_id="invalid")

        with pytest.raises(ValidationError):
            GetMessagesInput(channel_id="X1234567890")  # Wrong prefix

    def test_thread_ts_format_validation(self):
        """Test that thread_ts format is validated."""
        from sgept_slack_mcp.models import GetThreadInput
        from pydantic import ValidationError

        # Valid thread_ts
        GetThreadInput(channel_id="C1234567890", thread_ts="1234567890.123456")

        # Invalid thread_ts
        with pytest.raises(ValidationError):
            GetThreadInput(channel_id="C1234567890", thread_ts="invalid")

    def test_message_text_length_validation(self):
        """Test that message text length is validated."""
        from sgept_slack_mcp.models import SendMessageInput
        from pydantic import ValidationError

        # Valid length
        SendMessageInput(channel_id="C1234567890", text="Hello!")

        # Empty text should fail
        with pytest.raises(ValidationError):
            SendMessageInput(channel_id="C1234567890", text="")

        # Text over 40000 chars should fail
        with pytest.raises(ValidationError):
            SendMessageInput(channel_id="C1234567890", text="x" * 40001)

    def test_search_query_sanitization(self):
        """Test that search query is sanitized."""
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_client = AsyncMock()
            mock_client.search_messages = AsyncMock(return_value={
                "ok": True,
                "messages": {"total": 0, "matches": []},
            })
            mock_client.users_list = AsyncMock(return_value={
                "ok": True,
                "members": [],
                "response_metadata": {"next_cursor": ""},
            })
            mock_class.return_value = mock_client

            client = SlackAPIClient("xoxp-valid-token")

            # Query with newlines should be sanitized
            import asyncio
            asyncio.run(client.search_messages("test\ninjection\rquery"))

            mock_client.search_messages.assert_called_once()
            call_kwargs = mock_client.search_messages.call_args[1]

            # Newlines should be replaced with spaces
            assert "\n" not in call_kwargs["query"]
            assert "\r" not in call_kwargs["query"]


class TestLoggingSecurity:
    """Tests for logging security."""

    def test_token_not_logged_on_init(self, caplog):
        """Test that token is not logged during initialization."""
        secret_token = "xoxp-super-secret-token-12345"

        with patch('sgept_slack_mcp.client.AsyncWebClient'):
            with caplog.at_level(logging.DEBUG):
                client = SlackAPIClient(secret_token)

        # Check that token doesn't appear in any log messages
        for record in caplog.records:
            assert secret_token not in record.message
            assert "super-secret" not in record.message
