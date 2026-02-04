"""Slack API client wrapper with pagination, rate limiting, and caching."""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Any

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from .cache import TTLCache
from .models import (
    SlackConversation,
    SlackUser,
    SlackMessage,
    SlackSearchResult,
    SendMessageResponse,
    ConversationType,
)

logger = logging.getLogger(__name__)

# Error message mapping for user-friendly responses
SLACK_ERROR_MESSAGES = {
    "missing_scope": "Missing OAuth permission: {detail}. Please re-authorize the app.",
    "channel_not_found": "Channel not found. Check channel ID or permissions.",
    "thread_not_found": "Thread not found. The parent message may have been deleted.",
    "invalid_auth": "Slack token is invalid or expired. Please check SLACK_USER_TOKEN.",
    "account_inactive": "Slack account is inactive. Please contact your administrator.",
    "ratelimited": "Rate limited by Slack. Retrying in {retry_after} seconds...",
    "is_archived": "Channel is archived. Unarchive to access messages.",
    "not_in_channel": "You are not a member of this channel.",
    "no_permission": "You don't have permission to perform this action.",
    "user_not_found": "User not found.",
    "cant_dm_bot": "Cannot send direct messages to this bot.",
}


class SlackClientError(Exception):
    """Custom exception for Slack client errors."""

    def __init__(self, message: str, slack_error: Optional[str] = None):
        super().__init__(message)
        self.slack_error = slack_error


class SlackAPIClient:
    """
    Async Slack API client with pagination, rate limiting, and caching.

    Features:
    - Transparent pagination (auto-fetches all pages)
    - Exponential backoff on rate limits (uses Retry-After header)
    - User cache with 5-minute TTL
    - mrkdwn to readable text conversion
    - User-friendly error messages
    """

    def __init__(self, token: str, cache_ttl: float = 300.0):
        """
        Initialize Slack API client.

        Args:
            token: Slack user token (must start with 'xoxp-')
            cache_ttl: Cache TTL in seconds (default: 5 minutes)

        Raises:
            ValueError: If token format is invalid
        """
        self._validate_token(token)
        self._client = AsyncWebClient(token=token)
        self._user_cache: TTLCache[dict[str, SlackUser]] = TTLCache(ttl_seconds=cache_ttl)
        self._user_map_key = "user_map"

    def _validate_token(self, token: str) -> None:
        """Validate token format without logging the token value."""
        if not token:
            raise ValueError("Slack token is required")
        if not token.startswith("xoxp-"):
            raise ValueError(
                "Invalid token format: must be a user token (xoxp-*). "
                "Bot tokens (xoxb-*) are not supported."
            )

    def _get_error_message(self, error: str, **kwargs: Any) -> str:
        """Map Slack error code to user-friendly message."""
        template = SLACK_ERROR_MESSAGES.get(error, f"Slack API error: {error}")
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    async def _call_with_retry(
        self,
        method: str,
        max_retries: int = 5,
        **kwargs: Any
    ) -> dict:
        """
        Call Slack API with exponential backoff on rate limits.

        Args:
            method: Slack API method name (e.g., 'conversations_list')
            max_retries: Maximum retry attempts
            **kwargs: Arguments to pass to the API method

        Returns:
            API response as dict

        Raises:
            SlackClientError: On API error after retries exhausted
        """
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                api_method = getattr(self._client, method)
                result = await api_method(**kwargs)
                return result
            except SlackApiError as e:
                error_code = e.response.get("error", "unknown_error")

                if error_code == "ratelimited":
                    # Use Retry-After header from Slack
                    retry_after = int(
                        e.response.headers.get("Retry-After", base_delay * (2 ** attempt))
                    )
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Rate limited, retrying in {retry_after}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(retry_after)
                        continue

                # Non-retryable error or retries exhausted
                raise SlackClientError(
                    self._get_error_message(error_code, retry_after=retry_after if error_code == "ratelimited" else 0),
                    slack_error=error_code
                )

        raise SlackClientError("Rate limited after maximum retries")

    async def _get_user_map(self) -> dict[str, SlackUser]:
        """Get or fetch user map (user_id -> SlackUser)."""
        cached = self._user_cache.get(self._user_map_key)
        if cached is not None:
            return cached

        # Fetch all users
        users = await self._fetch_all_users()
        user_map = {user.id: user for user in users}
        self._user_cache.set(self._user_map_key, user_map)
        return user_map

    async def _fetch_all_users(self) -> list[SlackUser]:
        """Fetch all users with pagination."""
        users: list[SlackUser] = []
        cursor: Optional[str] = None

        while True:
            kwargs: dict[str, Any] = {"limit": 200}
            if cursor:
                kwargs["cursor"] = cursor

            result = await self._call_with_retry("users_list", **kwargs)

            for member in result.get("members", []):
                if member.get("deleted", False):
                    continue  # Skip deleted users

                profile = member.get("profile", {})
                users.append(SlackUser(
                    id=member["id"],
                    name=member.get("name", ""),
                    real_name=profile.get("real_name"),
                    display_name=profile.get("display_name"),
                    is_bot=member.get("is_bot", False),
                ))

            # Check for next page
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return users

    def _resolve_user_name(self, user_id: Optional[str], user_map: dict[str, SlackUser]) -> Optional[str]:
        """Resolve user_id to display name."""
        if not user_id:
            return None
        user = user_map.get(user_id)
        if not user:
            return user_id  # Return ID if user not found
        return user.display_name or user.real_name or user.name

    def _resolve_mrkdwn(self, text: str, user_map: dict[str, SlackUser]) -> str:
        """
        Convert Slack mrkdwn to readable text.

        Converts:
        - <@U123> -> @username
        - <#C123|channel-name> -> #channel-name
        - <https://url|display text> -> display text (url)
        - <https://url> -> url
        """
        if not text:
            return ""

        # Resolve user mentions: <@U123> or <@U123|display>
        def replace_user(match: re.Match) -> str:
            user_id = match.group(1)
            user = user_map.get(user_id)
            if user:
                return f"@{user.display_name or user.real_name or user.name}"
            return f"@{user_id}"

        text = re.sub(r"<@([A-Z0-9]+)(?:\|[^>]*)?>", replace_user, text)

        # Resolve channel references: <#C123|channel-name>
        text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"#\1", text)
        text = re.sub(r"<#([A-Z0-9]+)>", r"#\1", text)

        # Resolve links: <https://url|display> or <https://url>
        text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2 (\1)", text)
        text = re.sub(r"<(https?://[^>]+)>", r"\1", text)

        # Resolve special mentions
        text = text.replace("<!here>", "@here")
        text = text.replace("<!channel>", "@channel")
        text = text.replace("<!everyone>", "@everyone")

        return text

    def _format_timestamp(self, ts: str) -> str:
        """Convert Slack timestamp to human-readable format."""
        try:
            unix_ts = float(ts.split(".")[0])
            dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, IndexError):
            return ts

    # =========================================================================
    # Public API Methods
    # =========================================================================

    async def list_conversations(
        self,
        types: Optional[list[ConversationType]] = None,
        limit: int = 100,
    ) -> list[SlackConversation]:
        """
        List accessible conversations (channels and DMs).

        Args:
            types: Conversation types to include (default: all)
            limit: Maximum conversations to return

        Returns:
            List of conversations
        """
        if types is None:
            types = list(ConversationType)

        types_str = ",".join(t.value for t in types)
        conversations: list[SlackConversation] = []
        cursor: Optional[str] = None
        user_map = await self._get_user_map()

        while len(conversations) < limit:
            kwargs: dict[str, Any] = {
                "types": types_str,
                "limit": min(200, limit - len(conversations)),
                "exclude_archived": True,
            }
            if cursor:
                kwargs["cursor"] = cursor

            result = await self._call_with_retry("conversations_list", **kwargs)

            for channel in result.get("channels", []):
                conv_type = self._determine_conversation_type(channel)

                conv = SlackConversation(
                    id=channel["id"],
                    name=channel.get("name"),
                    type=conv_type,
                    is_member=channel.get("is_member", False),
                )

                # For DMs, resolve user name
                if conv_type == "im" and channel.get("user"):
                    conv.user_id = channel["user"]
                    conv.user_name = self._resolve_user_name(channel["user"], user_map)

                conversations.append(conv)

                if len(conversations) >= limit:
                    break

            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return conversations

    def _determine_conversation_type(self, channel: dict) -> str:
        """Determine conversation type from channel data."""
        if channel.get("is_im"):
            return "im"
        if channel.get("is_mpim"):
            return "mpim"
        if channel.get("is_private"):
            return "private_channel"
        return "public_channel"

    async def list_users(self, limit: int = 200) -> list[SlackUser]:
        """
        List workspace users.

        Args:
            limit: Maximum users to return

        Returns:
            List of users
        """
        user_map = await self._get_user_map()
        users = list(user_map.values())
        return users[:limit]

    async def get_messages(
        self,
        channel_id: str,
        limit: int = 20,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        include_thread_info: bool = False,
    ) -> list[SlackMessage]:
        """
        Fetch messages from a conversation.

        Args:
            channel_id: Channel or DM ID
            limit: Maximum messages to return
            oldest: Only messages after this timestamp
            latest: Only messages before this timestamp
            include_thread_info: Include thread metadata

        Returns:
            List of messages (newest first)
        """
        user_map = await self._get_user_map()
        messages: list[SlackMessage] = []

        kwargs: dict[str, Any] = {
            "channel": channel_id,
            "limit": min(100, limit),
        }
        if oldest:
            kwargs["oldest"] = oldest
        if latest:
            kwargs["latest"] = latest

        result = await self._call_with_retry("conversations_history", **kwargs)

        for msg in result.get("messages", []):
            if msg.get("subtype") == "message_deleted":
                continue  # Skip deleted messages

            user_id = msg.get("user")
            text = msg.get("text", "")

            # Handle edited messages
            if "edited" in msg:
                text = msg.get("text", "")

            message = SlackMessage(
                ts=msg["ts"],
                user_id=user_id,
                user_name=self._resolve_user_name(user_id, user_map),
                text=self._resolve_mrkdwn(text, user_map),
                timestamp=self._format_timestamp(msg["ts"]),
            )

            if include_thread_info:
                message.thread_ts = msg.get("thread_ts")
                message.reply_count = msg.get("reply_count", 0)
                message.is_parent = msg.get("thread_ts") == msg["ts"]

            messages.append(message)

            if len(messages) >= limit:
                break

        return messages

    async def get_thread(
        self,
        channel_id: str,
        thread_ts: str,
        limit: int = 50,
    ) -> list[SlackMessage]:
        """
        Fetch all replies in a thread.

        Args:
            channel_id: Channel ID where thread exists
            thread_ts: Thread parent timestamp
            limit: Maximum replies to return

        Returns:
            List of thread messages (parent first, then replies chronologically)
        """
        user_map = await self._get_user_map()
        messages: list[SlackMessage] = []
        cursor: Optional[str] = None

        while len(messages) < limit:
            kwargs: dict[str, Any] = {
                "channel": channel_id,
                "ts": thread_ts,
                "limit": min(100, limit - len(messages)),
            }
            if cursor:
                kwargs["cursor"] = cursor

            result = await self._call_with_retry("conversations_replies", **kwargs)

            for msg in result.get("messages", []):
                user_id = msg.get("user")
                is_parent = msg["ts"] == thread_ts

                messages.append(SlackMessage(
                    ts=msg["ts"],
                    user_id=user_id,
                    user_name=self._resolve_user_name(user_id, user_map),
                    text=self._resolve_mrkdwn(msg.get("text", ""), user_map),
                    timestamp=self._format_timestamp(msg["ts"]),
                    thread_ts=thread_ts,
                    is_parent=is_parent,
                ))

                if len(messages) >= limit:
                    break

            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return messages

    async def send_message(
        self,
        channel_id: str,
        text: str,
        thread_ts: Optional[str] = None,
    ) -> SendMessageResponse:
        """
        Send a message to a channel or DM.

        SECURITY: Sets unfurl_links=False and unfurl_media=False to prevent
        link unfurling vulnerabilities.

        Args:
            channel_id: Channel or DM ID
            text: Message text
            thread_ts: Reply in thread if provided

        Returns:
            Send result with message ts
        """
        kwargs: dict[str, Any] = {
            "channel": channel_id,
            "text": text,
            "unfurl_links": False,  # SECURITY: Prevent link unfurling
            "unfurl_media": False,  # SECURITY: Prevent media unfurling
        }
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        try:
            result = await self._call_with_retry("chat_postMessage", **kwargs)
            return SendMessageResponse(
                ok=True,
                ts=result.get("ts"),
                channel_id=result.get("channel"),
            )
        except SlackClientError as e:
            return SendMessageResponse(
                ok=False,
                error=str(e),
            )

    async def search_messages(
        self,
        query: str,
        limit: int = 20,
        sort: str = "timestamp",
        sort_dir: str = "desc",
    ) -> list[SlackSearchResult]:
        """
        Search messages across the workspace.

        Args:
            query: Search query (supports Slack search syntax)
            limit: Maximum results to return
            sort: Sort by 'timestamp' or 'score'
            sort_dir: Sort direction ('desc' or 'asc')

        Returns:
            List of search results
        """
        user_map = await self._get_user_map()
        results: list[SlackSearchResult] = []

        # Sanitize query
        query = query.replace("\n", " ").replace("\r", " ")[:1000]

        result = await self._call_with_retry(
            "search_messages",
            query=query,
            sort=sort,
            sort_dir=sort_dir,
            count=min(100, limit),
        )

        matches = result.get("messages", {}).get("matches", [])

        for match in matches[:limit]:
            user_id = match.get("user")
            channel_info = match.get("channel", {})

            results.append(SlackSearchResult(
                channel_id=channel_info.get("id", ""),
                channel_name=channel_info.get("name"),
                ts=match.get("ts", ""),
                user_id=user_id,
                user_name=self._resolve_user_name(user_id, user_map),
                text=self._resolve_mrkdwn(match.get("text", ""), user_map),
                timestamp=self._format_timestamp(match.get("ts", "")),
                permalink=match.get("permalink"),
                score=match.get("score"),
            ))

        return results

    def invalidate_cache(self) -> None:
        """Invalidate all cached data (useful after errors)."""
        self._user_cache.invalidate_all()
