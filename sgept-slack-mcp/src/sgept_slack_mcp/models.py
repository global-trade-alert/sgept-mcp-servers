"""Pydantic models for Slack MCP server input validation and response schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ConversationType(str, Enum):
    """Slack conversation types."""
    PUBLIC_CHANNEL = "public_channel"
    PRIVATE_CHANNEL = "private_channel"
    IM = "im"
    MPIM = "mpim"


class SortOrder(str, Enum):
    """Search result sort order."""
    TIMESTAMP = "timestamp"
    SCORE = "score"


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ============================================================================
# Input Models (Tool Parameters)
# ============================================================================

class ListConversationsInput(BaseModel):
    """Input for slack_list_conversations tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    types: list[ConversationType] = Field(
        default=[
            ConversationType.PUBLIC_CHANNEL,
            ConversationType.PRIVATE_CHANNEL,
            ConversationType.MPIM,
            ConversationType.IM
        ],
        description="Conversation types to include"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum conversations to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class ListUsersInput(BaseModel):
    """Input for slack_list_users tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    limit: int = Field(
        default=200,
        ge=1,
        le=1000,
        description="Maximum users to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GetMessagesInput(BaseModel):
    """Input for slack_get_messages tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel_id: str = Field(
        ...,
        description="Channel or DM ID (e.g., C1234567890, D1234567890, G1234567890)",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of messages to return"
    )
    oldest: Optional[str] = Field(
        default=None,
        description="Only messages after this Unix timestamp (e.g., '1234567890.123456')"
    )
    latest: Optional[str] = Field(
        default=None,
        description="Only messages before this Unix timestamp"
    )
    include_thread_info: bool = Field(
        default=False,
        description="Include thread metadata (reply_count, thread_ts) for messages"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GetThreadInput(BaseModel):
    """Input for slack_get_thread tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel_id: str = Field(
        ...,
        description="Channel ID where the thread exists",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    thread_ts: str = Field(
        ...,
        description="Thread parent timestamp (e.g., '1234567890.123456')",
        pattern=r"^\d+\.\d+$"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum replies to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class SendMessageInput(BaseModel):
    """Input for slack_send_message tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel_id: str = Field(
        ...,
        description="Channel or DM ID to send message to",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=40000,
        description="Message text (supports Slack markdown)"
    )
    thread_ts: Optional[str] = Field(
        default=None,
        description="Reply in thread if provided (thread parent timestamp)",
        pattern=r"^\d+\.\d+$"
    )
    force: bool = Field(
        default=False,
        description="Bypass anti-noise rate limit for unsolicited DMs (default: false)"
    )


class SearchMessagesInput(BaseModel):
    """Input for slack_search_messages tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query (supports Slack search syntax: from:user, in:channel, etc.)"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum results to return"
    )
    sort: SortOrder = Field(
        default=SortOrder.TIMESTAMP,
        description="Sort by 'timestamp' (newest first) or 'score' (most relevant)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class AddReactionInput(BaseModel):
    """Input for slack_add_reaction tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel: str = Field(
        ...,
        description="Channel ID where the message exists",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    timestamp: str = Field(
        ...,
        description="Message timestamp to react to (e.g., '1234567890.123456')",
        pattern=r"^\d+\.\d+$"
    )
    emoji: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Emoji name without colons (e.g., 'thumbsup', 'white_check_mark')"
    )


class GetReactionsInput(BaseModel):
    """Input for slack_get_reactions tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel: str = Field(
        ...,
        description="Channel ID where the message exists",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    timestamp: str = Field(
        ...,
        description="Message timestamp to get reactions for (e.g., '1234567890.123456')",
        pattern=r"^\d+\.\d+$"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GetUserPresenceInput(BaseModel):
    """Input for slack_get_user_presence tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    user_id: str = Field(
        ...,
        description="User ID to check presence for (e.g., 'U1234567890')",
        pattern=r"^U[A-Z0-9]{8,}$"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class SendBlockKitInput(BaseModel):
    """Input for slack_send_block_kit tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel: str = Field(
        ...,
        description="Channel or DM ID to send to",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    blocks: str = Field(
        ...,
        min_length=2,
        description="Block Kit blocks as JSON string (array of block objects)"
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=40000,
        description="Fallback text for notifications and accessibility"
    )
    thread_ts: Optional[str] = Field(
        default=None,
        description="Reply in thread if provided (thread parent timestamp)",
        pattern=r"^\d+\.\d+$"
    )
    force: bool = Field(
        default=False,
        description="Bypass anti-noise rate limit for unsolicited DMs (default: false)"
    )


class CreateChannelInput(BaseModel):
    """Input for slack_create_channel tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="Channel name (will be slugified: lowercased, spaces to hyphens)"
    )
    is_private: bool = Field(
        default=False,
        description="Create as private channel (default: public)"
    )


class ScheduleMessageInput(BaseModel):
    """Input for slack_schedule_message tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel: str = Field(
        ...,
        description="Channel or DM ID to send to",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=40000,
        description="Message text (supports Slack markdown)"
    )
    post_at: int = Field(
        ...,
        description="Unix timestamp for when to send the message (must be in the future)"
    )
    thread_ts: Optional[str] = Field(
        default=None,
        description="Reply in thread if provided (thread parent timestamp)",
        pattern=r"^\d+\.\d+$"
    )
    blocks: Optional[str] = Field(
        default=None,
        description="Block Kit blocks as JSON string (array of block objects)"
    )


class DeleteScheduledMessageInput(BaseModel):
    """Input for slack_delete_scheduled_message tool."""
    model_config = ConfigDict(extra='forbid')

    identity: Optional[str] = Field(
        default=None,
        description="Slack identity to use (e.g., 'claudino', 'claudante', 'johannes'). Uses default if omitted."
    )
    channel: str = Field(
        ...,
        description="Channel ID where the scheduled message was targeting",
        pattern=r"^[CDGW][A-Z0-9]{8,}$"
    )
    scheduled_message_id: str = Field(
        ...,
        min_length=1,
        description="The scheduled_message_id returned when the message was scheduled"
    )


# ============================================================================
# Response Models (Output Schemas)
# ============================================================================

class SlackConversation(BaseModel):
    """A Slack conversation (channel or DM)."""
    id: str
    name: Optional[str] = None
    type: str
    is_member: bool = False
    user_id: Optional[str] = None  # For DMs
    user_name: Optional[str] = None  # For DMs


class SlackUser(BaseModel):
    """A Slack workspace user."""
    id: str
    name: str
    real_name: Optional[str] = None
    display_name: Optional[str] = None
    is_bot: bool = False


class SlackMessage(BaseModel):
    """A Slack message."""
    ts: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    text: str
    timestamp: str  # Human-readable timestamp
    thread_ts: Optional[str] = None
    reply_count: int = 0
    is_parent: bool = False


class SlackSearchResult(BaseModel):
    """A Slack search result."""
    channel_id: str
    channel_name: Optional[str] = None
    ts: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    text: str
    timestamp: str
    permalink: Optional[str] = None
    score: Optional[float] = None


class SendMessageResponse(BaseModel):
    """Response from sending a message."""
    ok: bool
    ts: Optional[str] = None
    channel_id: Optional[str] = None
    error: Optional[str] = None


class ReactionInfo(BaseModel):
    """A single reaction on a message."""
    emoji: str
    count: int
    users: list[str] = Field(default_factory=list)


class GetReactionsResponse(BaseModel):
    """Response from getting reactions on a message."""
    ok: bool
    reactions: list[ReactionInfo] = Field(default_factory=list)
    error: Optional[str] = None


class UserPresenceResponse(BaseModel):
    """Response from getting user presence."""
    ok: bool
    presence: Optional[str] = None  # "active" or "away"
    dnd_enabled: bool = False
    dnd_next_expiry: Optional[int] = None  # Unix timestamp
    error: Optional[str] = None


class CreateChannelResponse(BaseModel):
    """Response from creating a channel."""
    ok: bool
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    error: Optional[str] = None


class ScheduleMessageResponse(BaseModel):
    """Response from scheduling a message."""
    ok: bool
    scheduled_message_id: Optional[str] = None
    channel: Optional[str] = None
    post_at: Optional[int] = None
    error: Optional[str] = None


class DeleteScheduledMessageResponse(BaseModel):
    """Response from deleting a scheduled message."""
    ok: bool
    error: Optional[str] = None
