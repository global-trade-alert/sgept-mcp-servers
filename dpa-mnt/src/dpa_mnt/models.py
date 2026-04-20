"""Pydantic models for dpa_mnt MCP server."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Output Models
# ============================================================================

class SourceResult(BaseModel):
    """Result from get_source tool."""
    source_type: Literal["file", "url"]
    source_url: str
    content: Optional[str] = None
    content_type: str  # "pdf", "html", "text"


class CommentResult(BaseModel):
    """Result from add_comment tool."""
    comment_id: int
    success: bool
    message: str


class StatusResult(BaseModel):
    """Result from set_status tool."""
    event_id: int
    new_status_id: int
    success: bool
    message: str


class FrameworkResult(BaseModel):
    """Result from add_framework tool."""
    event_id: int
    framework_id: int
    success: bool
    message: str
