"""Pydantic models for gta_mnt MCP server."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Tool Input Models
# ============================================================================

class Step1QueueInput(BaseModel):
    """Input parameters for listing Step 1 review queue."""
    limit: int = Field(default=20, ge=1, le=100, description="Max measures to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    implementing_jurisdictions: Optional[list[str]] = Field(
        default=None,
        description="Filter by implementing jurisdiction codes (e.g., ['USA', 'CHN'])"
    )
    date_entered_review_gte: Optional[str] = Field(
        default=None,
        description="Filter by date entered review (YYYY-MM-DD)"
    )


class GetMeasureInput(BaseModel):
    """Input parameters for getting measure details."""
    state_act_id: int = Field(description="StateAct ID")
    include_interventions: bool = Field(default=True, description="Include nested interventions")
    include_comments: bool = Field(default=True, description="Include existing comments")


class GetSourceInput(BaseModel):
    """Input parameters for getting official source."""
    state_act_id: int = Field(description="StateAct ID")
    fetch_content: bool = Field(
        default=True,
        description="Fetch and extract file/URL content"
    )


class AddCommentInput(BaseModel):
    """Input parameters for adding a comment."""
    measure_id: int = Field(description="StateAct ID")
    comment_text: str = Field(description="Full comment text (structured per spec)")
    template_id: Optional[int] = Field(
        default=None,
        description="Optional template ID for standardized comments"
    )


class SetStatusInput(BaseModel):
    """Input parameters for setting measure status."""
    state_act_id: int = Field(description="StateAct ID")
    new_status_id: int = Field(
        description="Status ID (2=Step1, 3=Publishable, 6=Under revision)"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional reason for status change"
    )


class AddFrameworkInput(BaseModel):
    """Input parameters for adding framework tag."""
    state_act_id: int = Field(description="StateAct ID")
    framework_name: str = Field(
        default="sancho claudino review",
        description="Framework name to attach"
    )


class LogReviewCompleteInput(BaseModel):
    """Input parameters for logging review completion."""
    state_act_id: int = Field(description="StateAct ID")


class ListTemplatesInput(BaseModel):
    """Input parameters for listing comment templates."""
    include_checklist: bool = Field(
        default=False,
        description="Include checklist templates"
    )


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
    state_act_id: int
    new_status_id: int
    success: bool
    message: str


class FrameworkResult(BaseModel):
    """Result from add_framework tool."""
    state_act_id: int
    framework_id: int
    success: bool
    message: str
