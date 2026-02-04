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


class SearchMessagesInput(BaseModel):
    """Input for slack_search_messages tool."""
    model_config = ConfigDict(extra='forbid')

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
