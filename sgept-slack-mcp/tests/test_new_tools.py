"""Tests for the 5 new Slack MCP tools: reactions, presence, block kit, create channel,
schedule message, delete scheduled message."""

import json
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from sgept_slack_mcp.models import (
    AddReactionInput,
    GetReactionsInput,
    GetUserPresenceInput,
    SendBlockKitInput,
    CreateChannelInput,
    ScheduleMessageInput,
    DeleteScheduledMessageInput,
    ReactionInfo,
    GetReactionsResponse,
    UserPresenceResponse,
    CreateChannelResponse,
    SendMessageResponse,
    SendMessageInput,
    ScheduleMessageResponse,
    DeleteScheduledMessageResponse,
    ResponseFormat,
)
from sgept_slack_mcp.client import SlackAPIClient, SlackClientError
from sgept_slack_mcp.formatters import (
    format_reactions_markdown,
    format_reactions_json,
    format_user_presence_markdown,
    format_user_presence_json,
    format_create_channel_markdown,
    format_create_channel_json,
    format_scheduled_message_markdown,
    format_scheduled_message_json,
    format_delete_scheduled_message_markdown,
    format_delete_scheduled_message_json,
)


# ============================================================================
# Model Tests
# ============================================================================

class TestNewModels:
    """Tests for new Pydantic input/response models."""

    def test_add_reaction_input_valid(self):
        inp = AddReactionInput(
            channel="C1234567890",
            timestamp="1705363200.123456",
            emoji="thumbsup",
        )
        assert inp.emoji == "thumbsup"
        assert inp.identity is None

    def test_add_reaction_input_rejects_bad_channel(self):
        with pytest.raises(Exception):
            AddReactionInput(
                channel="invalid",
                timestamp="1705363200.123456",
                emoji="thumbsup",
            )

    def test_get_reactions_input_valid(self):
        inp = GetReactionsInput(
            channel="C1234567890",
            timestamp="1705363200.123456",
        )
        assert inp.response_format == ResponseFormat.MARKDOWN

    def test_get_user_presence_input_valid(self):
        inp = GetUserPresenceInput(user_id="U1234567890")
        assert inp.user_id == "U1234567890"

    def test_get_user_presence_input_rejects_bad_id(self):
        with pytest.raises(Exception):
            GetUserPresenceInput(user_id="C1234567890")

    def test_send_block_kit_input_valid(self):
        inp = SendBlockKitInput(
            channel="C1234567890",
            blocks='[{"type":"section"}]',
            text="Fallback",
        )
        assert inp.force is False
        assert inp.thread_ts is None

    def test_create_channel_input_valid(self):
        inp = CreateChannelInput(name="my-channel")
        assert inp.is_private is False

    def test_reaction_info_model(self):
        r = ReactionInfo(emoji="thumbsup", count=3, users=["U1", "U2", "U3"])
        assert r.count == 3
        assert len(r.users) == 3

    def test_get_reactions_response_model(self):
        resp = GetReactionsResponse(
            ok=True,
            reactions=[ReactionInfo(emoji="heart", count=1, users=["U1"])],
        )
        assert resp.ok
        assert len(resp.reactions) == 1

    def test_user_presence_response_model(self):
        resp = UserPresenceResponse(ok=True, presence="active", dnd_enabled=False)
        assert resp.presence == "active"

    def test_create_channel_response_model(self):
        resp = CreateChannelResponse(ok=True, channel_id="C999", channel_name="test")
        assert resp.channel_id == "C999"

    def test_send_message_input_has_force(self):
        inp = SendMessageInput(
            channel_id="C1234567890",
            text="Hello",
            force=True,
        )
        assert inp.force is True

    def test_send_message_input_force_default_false(self):
        inp = SendMessageInput(
            channel_id="C1234567890",
            text="Hello",
        )
        assert inp.force is False


# ============================================================================
# Client Method Tests (mocked Slack API)
# ============================================================================

@pytest.mark.asyncio
class TestClientAddReaction:
    """Tests for SlackAPIClient.add_reaction."""

    @pytest.fixture
    def client_with_mock(self):
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_web = AsyncMock()
            mock_class.return_value = mock_web
            mock_web.reactions_add = AsyncMock(return_value={"ok": True})
            client = SlackAPIClient("xoxb-test-token")
            return client, mock_web

    async def test_add_reaction_success(self, client_with_mock):
        client, mock_web = client_with_mock
        resp = await client.add_reaction("C123456789A", "1705363200.123456", "thumbsup")
        assert resp.ok is True
        mock_web.reactions_add.assert_called_once()
        call_kwargs = mock_web.reactions_add.call_args[1]
        assert call_kwargs["name"] == "thumbsup"
        assert call_kwargs["channel"] == "C123456789A"

    async def test_add_reaction_error(self, client_with_mock):
        client, mock_web = client_with_mock
        mock_web.reactions_add = AsyncMock(
            side_effect=SlackClientError("already_reacted")
        )
        resp = await client.add_reaction("C123456789A", "1705363200.123456", "thumbsup")
        assert resp.ok is False
        assert "already_reacted" in resp.error


@pytest.mark.asyncio
class TestClientGetReactions:
    """Tests for SlackAPIClient.get_reactions."""

    @pytest.fixture
    def client_with_mock(self):
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_web = AsyncMock()
            mock_class.return_value = mock_web
            mock_web.reactions_get = AsyncMock(return_value={
                "ok": True,
                "message": {
                    "reactions": [
                        {"name": "thumbsup", "count": 2, "users": ["U1", "U2"]},
                        {"name": "heart", "count": 1, "users": ["U3"]},
                    ]
                }
            })
            # Need users_list for _get_user_map (called internally)
            mock_web.users_list = AsyncMock(return_value={
                "ok": True, "members": [], "response_metadata": {"next_cursor": ""}
            })
            client = SlackAPIClient("xoxb-test-token")
            return client, mock_web

    async def test_get_reactions_success(self, client_with_mock):
        client, _ = client_with_mock
        resp = await client.get_reactions("C123456789A", "1705363200.123456")
        assert resp.ok is True
        assert len(resp.reactions) == 2
        assert resp.reactions[0].emoji == "thumbsup"
        assert resp.reactions[0].count == 2
        assert resp.reactions[1].emoji == "heart"


@pytest.mark.asyncio
class TestClientGetUserPresence:
    """Tests for SlackAPIClient.get_user_presence."""

    @pytest.fixture
    def client_with_mock(self):
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_web = AsyncMock()
            mock_class.return_value = mock_web
            mock_web.users_getPresence = AsyncMock(return_value={
                "ok": True, "presence": "active"
            })
            mock_web.dnd_info = AsyncMock(return_value={
                "ok": True, "dnd_enabled": True, "next_dnd_end_ts": 1705400000
            })
            mock_web.users_list = AsyncMock(return_value={
                "ok": True, "members": [], "response_metadata": {"next_cursor": ""}
            })
            client = SlackAPIClient("xoxb-test-token")
            return client, mock_web

    async def test_get_user_presence_active_with_dnd(self, client_with_mock):
        client, _ = client_with_mock
        resp = await client.get_user_presence("U1234567890")
        assert resp.ok is True
        assert resp.presence == "active"
        assert resp.dnd_enabled is True
        assert resp.dnd_next_expiry == 1705400000

    async def test_get_user_presence_dnd_fails_gracefully(self, client_with_mock):
        client, mock_web = client_with_mock
        mock_web.dnd_info = AsyncMock(side_effect=SlackClientError("user_not_found"))
        resp = await client.get_user_presence("U1234567890")
        assert resp.ok is True
        assert resp.presence == "active"
        assert resp.dnd_enabled is False


@pytest.mark.asyncio
class TestClientSendBlockKit:
    """Tests for SlackAPIClient.send_block_kit."""

    @pytest.fixture
    def client_with_mock(self):
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_web = AsyncMock()
            mock_class.return_value = mock_web
            mock_web.chat_postMessage = AsyncMock(return_value={
                "ok": True, "ts": "1705363300.111111", "channel": "C1234567890"
            })
            mock_web.users_list = AsyncMock(return_value={
                "ok": True, "members": [], "response_metadata": {"next_cursor": ""}
            })
            client = SlackAPIClient("xoxb-test-token")
            return client, mock_web

    async def test_send_block_kit_success(self, client_with_mock):
        client, mock_web = client_with_mock
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Hello"}}]
        resp = await client.send_block_kit("C1234567890", blocks, "Hello")
        assert resp.ok is True
        assert resp.ts == "1705363300.111111"
        call_kwargs = mock_web.chat_postMessage.call_args[1]
        assert call_kwargs["blocks"] == blocks
        assert call_kwargs["unfurl_links"] is False

    async def test_send_block_kit_with_thread(self, client_with_mock):
        client, mock_web = client_with_mock
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Reply"}}]
        resp = await client.send_block_kit(
            "C1234567890", blocks, "Reply", thread_ts="1705363200.123456"
        )
        call_kwargs = mock_web.chat_postMessage.call_args[1]
        assert call_kwargs["thread_ts"] == "1705363200.123456"


@pytest.mark.asyncio
class TestClientCreateChannel:
    """Tests for SlackAPIClient.create_channel."""

    @pytest.fixture
    def client_with_mock(self):
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_web = AsyncMock()
            mock_class.return_value = mock_web
            mock_web.conversations_create = AsyncMock(return_value={
                "ok": True,
                "channel": {"id": "C999NEWCHAN", "name": "my-channel"}
            })
            mock_web.users_list = AsyncMock(return_value={
                "ok": True, "members": [], "response_metadata": {"next_cursor": ""}
            })
            client = SlackAPIClient("xoxb-test-token")
            return client, mock_web

    async def test_create_channel_public(self, client_with_mock):
        client, mock_web = client_with_mock
        resp = await client.create_channel("my-channel")
        assert resp.ok is True
        assert resp.channel_id == "C999NEWCHAN"
        assert resp.channel_name == "my-channel"
        call_kwargs = mock_web.conversations_create.call_args[1]
        assert call_kwargs["is_private"] is False

    async def test_create_channel_private(self, client_with_mock):
        client, mock_web = client_with_mock
        resp = await client.create_channel("secret", is_private=True)
        call_kwargs = mock_web.conversations_create.call_args[1]
        assert call_kwargs["is_private"] is True


# ============================================================================
# Formatter Tests
# ============================================================================

class TestReactionFormatters:
    """Tests for reaction formatters."""

    def test_reactions_markdown_with_reactions(self):
        resp = GetReactionsResponse(
            ok=True,
            reactions=[
                ReactionInfo(emoji="thumbsup", count=3, users=["U1", "U2", "U3"]),
                ReactionInfo(emoji="heart", count=1, users=["U4"]),
            ],
        )
        result = format_reactions_markdown(resp)
        assert "Message Reactions" in result
        assert "thumbsup" in result
        assert "heart" in result
        assert "3" in result

    def test_reactions_markdown_empty(self):
        resp = GetReactionsResponse(ok=True, reactions=[])
        result = format_reactions_markdown(resp)
        assert "No reactions" in result

    def test_reactions_markdown_error(self):
        resp = GetReactionsResponse(ok=False, error="not_found")
        result = format_reactions_markdown(resp)
        assert "Failed" in result
        assert "not_found" in result

    def test_reactions_json(self):
        resp = GetReactionsResponse(
            ok=True,
            reactions=[ReactionInfo(emoji="fire", count=2, users=["U1", "U2"])],
        )
        result = format_reactions_json(resp)
        data = json.loads(result)
        assert data["ok"] is True
        assert len(data["reactions"]) == 1
        assert data["reactions"][0]["emoji"] == "fire"


class TestUserPresenceFormatters:
    """Tests for user presence formatters."""

    def test_presence_markdown_active(self):
        resp = UserPresenceResponse(ok=True, presence="active", dnd_enabled=False)
        result = format_user_presence_markdown(resp)
        assert "active" in result
        assert "Disabled" in result

    def test_presence_markdown_with_dnd(self):
        resp = UserPresenceResponse(
            ok=True, presence="away", dnd_enabled=True, dnd_next_expiry=1705400000
        )
        result = format_user_presence_markdown(resp)
        assert "away" in result
        assert "Enabled" in result
        assert "DND expires" in result

    def test_presence_markdown_error(self):
        resp = UserPresenceResponse(ok=False, error="user_not_found")
        result = format_user_presence_markdown(resp)
        assert "Failed" in result

    def test_presence_json(self):
        resp = UserPresenceResponse(ok=True, presence="active", dnd_enabled=False)
        result = format_user_presence_json(resp)
        data = json.loads(result)
        assert data["presence"] == "active"


class TestCreateChannelFormatters:
    """Tests for create channel formatters."""

    def test_create_channel_markdown_success(self):
        resp = CreateChannelResponse(ok=True, channel_id="C999", channel_name="my-channel")
        result = format_create_channel_markdown(resp)
        assert "Created Successfully" in result
        assert "my-channel" in result
        assert "C999" in result

    def test_create_channel_markdown_error(self):
        resp = CreateChannelResponse(ok=False, error="name_taken")
        result = format_create_channel_markdown(resp)
        assert "Failed" in result
        assert "name_taken" in result

    def test_create_channel_json(self):
        resp = CreateChannelResponse(ok=True, channel_id="C999", channel_name="test")
        result = format_create_channel_json(resp)
        data = json.loads(result)
        assert data["ok"] is True
        assert data["channel_id"] == "C999"


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestAntiNoiseRateLimiting:
    """Tests for the anti-noise rate limiting on unsolicited DMs."""

    def _make_bot_identity(self, send_enabled=True):
        from sgept_slack_mcp.identities import IdentityConfig
        return IdentityConfig(
            name="testbot",
            token_env="TEST_TOKEN",
            send_enabled=send_enabled,
            token="xoxb-test-bot-token",
        )

    def _make_user_identity(self, send_enabled=True):
        from sgept_slack_mcp.identities import IdentityConfig
        return IdentityConfig(
            name="testuser",
            token_env="TEST_TOKEN",
            send_enabled=send_enabled,
            token="xoxp-test-user-token",
        )

    def test_rate_limit_skipped_for_channels(self, tmp_path):
        from sgept_slack_mcp.server import _check_unsolicited_rate_limit
        identity = self._make_bot_identity()
        # Channel ID (not DM)
        result = _check_unsolicited_rate_limit("C1234567890", identity, force=False)
        assert result is None

    def test_rate_limit_skipped_for_user_tokens(self, tmp_path):
        from sgept_slack_mcp.server import _check_unsolicited_rate_limit
        identity = self._make_user_identity()
        result = _check_unsolicited_rate_limit("D1234567890", identity, force=False)
        assert result is None

    def test_rate_limit_skipped_with_force(self, tmp_path):
        from sgept_slack_mcp.server import _check_unsolicited_rate_limit
        identity = self._make_bot_identity()
        result = _check_unsolicited_rate_limit("D1234567890", identity, force=True)
        assert result is None

    def test_rate_limit_blocks_after_max(self, tmp_path, monkeypatch):
        from sgept_slack_mcp.server import (
            _check_unsolicited_rate_limit,
            _record_unsolicited_send,
            _SEND_COUNTS_PATH,
        )
        # Use a temp path for counts
        test_counts_path = tmp_path / "slack_send_counts.json"
        monkeypatch.setattr("sgept_slack_mcp.server._SEND_COUNTS_PATH", test_counts_path)
        monkeypatch.setenv("METIS_MAX_UNSOLICITED_PER_DAY", "2")

        identity = self._make_bot_identity()

        # First two should pass
        assert _check_unsolicited_rate_limit("D1234567890", identity, False) is None
        _record_unsolicited_send("D1234567890", identity)
        assert _check_unsolicited_rate_limit("D1234567890", identity, False) is None
        _record_unsolicited_send("D1234567890", identity)

        # Third should be blocked
        result = _check_unsolicited_rate_limit("D1234567890", identity, False)
        assert result is not None
        assert "rate limit" in result.lower()

    def test_record_ignores_non_dm(self, tmp_path, monkeypatch):
        from sgept_slack_mcp.server import _record_unsolicited_send, _SEND_COUNTS_PATH
        test_counts_path = tmp_path / "slack_send_counts.json"
        monkeypatch.setattr("sgept_slack_mcp.server._SEND_COUNTS_PATH", test_counts_path)

        identity = self._make_bot_identity()
        _record_unsolicited_send("C1234567890", identity)
        # File should not be created for channel messages
        assert not test_counts_path.exists()


# ============================================================================
# Schedule Message Model Tests
# ============================================================================

class TestScheduleMessageModels:
    """Tests for schedule/delete scheduled message Pydantic models."""

    def test_schedule_message_input_valid(self):
        inp = ScheduleMessageInput(
            channel="C1234567890",
            text="Good morning!",
            post_at=1705400000,
        )
        assert inp.text == "Good morning!"
        assert inp.post_at == 1705400000
        assert inp.identity is None
        assert inp.thread_ts is None
        assert inp.blocks is None

    def test_schedule_message_input_with_optional_fields(self):
        inp = ScheduleMessageInput(
            channel="C1234567890",
            text="Threaded reply",
            post_at=1705400000,
            thread_ts="1705363200.123456",
            blocks='[{"type":"section"}]',
            identity="claudino",
        )
        assert inp.thread_ts == "1705363200.123456"
        assert inp.blocks == '[{"type":"section"}]'
        assert inp.identity == "claudino"

    def test_schedule_message_input_rejects_bad_channel(self):
        with pytest.raises(Exception):
            ScheduleMessageInput(
                channel="invalid",
                text="Hello",
                post_at=1705400000,
            )

    def test_schedule_message_input_rejects_empty_text(self):
        with pytest.raises(Exception):
            ScheduleMessageInput(
                channel="C1234567890",
                text="",
                post_at=1705400000,
            )

    def test_delete_scheduled_message_input_valid(self):
        inp = DeleteScheduledMessageInput(
            channel="C1234567890",
            scheduled_message_id="Q1234ABCD5678",
        )
        assert inp.scheduled_message_id == "Q1234ABCD5678"
        assert inp.identity is None

    def test_delete_scheduled_message_input_rejects_bad_channel(self):
        with pytest.raises(Exception):
            DeleteScheduledMessageInput(
                channel="invalid",
                scheduled_message_id="Q1234ABCD5678",
            )

    def test_delete_scheduled_message_input_rejects_empty_id(self):
        with pytest.raises(Exception):
            DeleteScheduledMessageInput(
                channel="C1234567890",
                scheduled_message_id="",
            )

    def test_schedule_message_response_model(self):
        resp = ScheduleMessageResponse(
            ok=True,
            scheduled_message_id="Q1234ABCD5678",
            channel="C1234567890",
            post_at=1705400000,
        )
        assert resp.ok
        assert resp.scheduled_message_id == "Q1234ABCD5678"
        assert resp.post_at == 1705400000

    def test_delete_scheduled_message_response_model(self):
        resp = DeleteScheduledMessageResponse(ok=True)
        assert resp.ok
        assert resp.error is None


# ============================================================================
# Schedule Message Client Tests (mocked Slack API)
# ============================================================================

@pytest.mark.asyncio
class TestClientScheduleMessage:
    """Tests for SlackAPIClient.schedule_message."""

    @pytest.fixture
    def client_with_mock(self):
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_web = AsyncMock()
            mock_class.return_value = mock_web
            mock_web.chat_scheduleMessage = AsyncMock(return_value={
                "ok": True,
                "scheduled_message_id": "Q1234ABCD5678",
                "channel": "C1234567890",
                "post_at": 1705400000,
            })
            mock_web.users_list = AsyncMock(return_value={
                "ok": True, "members": [], "response_metadata": {"next_cursor": ""}
            })
            client = SlackAPIClient("xoxb-test-token")
            return client, mock_web

    async def test_schedule_message_success(self, client_with_mock):
        client, mock_web = client_with_mock
        resp = await client.schedule_message("C1234567890", "Hello!", 1705400000)
        assert resp.ok is True
        assert resp.scheduled_message_id == "Q1234ABCD5678"
        assert resp.channel == "C1234567890"
        assert resp.post_at == 1705400000
        call_kwargs = mock_web.chat_scheduleMessage.call_args[1]
        assert call_kwargs["channel"] == "C1234567890"
        assert call_kwargs["text"] == "Hello!"
        assert call_kwargs["post_at"] == 1705400000

    async def test_schedule_message_with_thread(self, client_with_mock):
        client, mock_web = client_with_mock
        resp = await client.schedule_message(
            "C1234567890", "Reply!", 1705400000, thread_ts="1705363200.123456"
        )
        call_kwargs = mock_web.chat_scheduleMessage.call_args[1]
        assert call_kwargs["thread_ts"] == "1705363200.123456"

    async def test_schedule_message_with_blocks(self, client_with_mock):
        client, mock_web = client_with_mock
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Hello"}}]
        resp = await client.schedule_message(
            "C1234567890", "Hello!", 1705400000, blocks=blocks
        )
        call_kwargs = mock_web.chat_scheduleMessage.call_args[1]
        assert call_kwargs["blocks"] == blocks

    async def test_schedule_message_error(self, client_with_mock):
        client, mock_web = client_with_mock
        mock_web.chat_scheduleMessage = AsyncMock(
            side_effect=SlackClientError("time_in_past")
        )
        resp = await client.schedule_message("C1234567890", "Hello!", 1000)
        assert resp.ok is False
        assert "time_in_past" in resp.error


@pytest.mark.asyncio
class TestClientDeleteScheduledMessage:
    """Tests for SlackAPIClient.delete_scheduled_message."""

    @pytest.fixture
    def client_with_mock(self):
        with patch('sgept_slack_mcp.client.AsyncWebClient') as mock_class:
            mock_web = AsyncMock()
            mock_class.return_value = mock_web
            mock_web.chat_deleteScheduledMessage = AsyncMock(return_value={"ok": True})
            mock_web.users_list = AsyncMock(return_value={
                "ok": True, "members": [], "response_metadata": {"next_cursor": ""}
            })
            client = SlackAPIClient("xoxb-test-token")
            return client, mock_web

    async def test_delete_scheduled_message_success(self, client_with_mock):
        client, mock_web = client_with_mock
        resp = await client.delete_scheduled_message("C1234567890", "Q1234ABCD5678")
        assert resp.ok is True
        call_kwargs = mock_web.chat_deleteScheduledMessage.call_args[1]
        assert call_kwargs["channel"] == "C1234567890"
        assert call_kwargs["scheduled_message_id"] == "Q1234ABCD5678"

    async def test_delete_scheduled_message_error(self, client_with_mock):
        client, mock_web = client_with_mock
        mock_web.chat_deleteScheduledMessage = AsyncMock(
            side_effect=SlackClientError("invalid_scheduled_message_id")
        )
        resp = await client.delete_scheduled_message("C1234567890", "QBADID")
        assert resp.ok is False
        assert "invalid_scheduled_message_id" in resp.error


# ============================================================================
# Schedule Message Formatter Tests
# ============================================================================

class TestScheduledMessageFormatters:
    """Tests for scheduled message formatters."""

    def test_scheduled_message_markdown_success(self):
        resp = ScheduleMessageResponse(
            ok=True,
            scheduled_message_id="Q1234ABCD5678",
            channel="C1234567890",
            post_at=1705400000,
        )
        result = format_scheduled_message_markdown(resp)
        assert "Scheduled Successfully" in result
        assert "Q1234ABCD5678" in result
        assert "C1234567890" in result

    def test_scheduled_message_markdown_error(self):
        resp = ScheduleMessageResponse(ok=False, error="time_in_past")
        result = format_scheduled_message_markdown(resp)
        assert "Failed" in result
        assert "time_in_past" in result

    def test_scheduled_message_json(self):
        resp = ScheduleMessageResponse(
            ok=True,
            scheduled_message_id="Q1234ABCD5678",
            channel="C1234567890",
            post_at=1705400000,
        )
        result = format_scheduled_message_json(resp)
        data = json.loads(result)
        assert data["ok"] is True
        assert data["scheduled_message_id"] == "Q1234ABCD5678"
        assert data["post_at"] == 1705400000


class TestDeleteScheduledMessageFormatters:
    """Tests for delete scheduled message formatters."""

    def test_delete_scheduled_message_markdown_success(self):
        resp = DeleteScheduledMessageResponse(ok=True)
        result = format_delete_scheduled_message_markdown(resp)
        assert "Deleted Successfully" in result

    def test_delete_scheduled_message_markdown_error(self):
        resp = DeleteScheduledMessageResponse(ok=False, error="invalid_scheduled_message_id")
        result = format_delete_scheduled_message_markdown(resp)
        assert "Failed" in result
        assert "invalid_scheduled_message_id" in result

    def test_delete_scheduled_message_json(self):
        resp = DeleteScheduledMessageResponse(ok=True)
        result = format_delete_scheduled_message_json(resp)
        data = json.loads(result)
        assert data["ok"] is True
        assert data["error"] is None
