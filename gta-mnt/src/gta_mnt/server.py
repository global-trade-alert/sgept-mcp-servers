"""MCP server for GTA monitoring and automated review (Sancho Claudino).

Refactored to use direct MySQL database access instead of REST API endpoints.
"""

import os
import sys
from typing import Optional, List
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

from .api import GTADatabaseClient
from .source_fetcher import SourceFetcher
from .constants import SANCHO_USER_ID, SANCHO_FRAMEWORK_ID
from .formatters import (
    format_step1_queue,
    format_measure_detail,
    format_source_result,
    format_templates
)


# Initialize FastMCP server
mcp = FastMCP("gta_mnt")

# Global singletons (lazy-initialized)
_db_client: Optional[GTADatabaseClient] = None
_source_fetcher: Optional[SourceFetcher] = None


def get_db_client() -> GTADatabaseClient:
    """Get or create the database client."""
    global _db_client
    if _db_client is None:
        _db_client = GTADatabaseClient()
    return _db_client


def get_source_fetcher() -> SourceFetcher:
    """Get or create the source fetcher."""
    global _source_fetcher
    if _source_fetcher is None:
        _source_fetcher = SourceFetcher()
    return _source_fetcher


# Input models for tools
class ListStep1QueueInput(BaseModel):
    """Input for listing Step 1 review queue."""
    limit: int = Field(default=20, ge=1, le=100, description="Max measures to return (1-100)")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter by jurisdiction codes (e.g., ['USA', 'CHN'])"
    )
    date_entered_review_gte: Optional[str] = Field(
        default=None,
        description="Filter by date entered review (YYYY-MM-DD)"
    )


class GetMeasureInput(BaseModel):
    """Input for getting measure details."""
    state_act_id: int = Field(..., description="StateAct ID")
    include_interventions: bool = Field(default=True, description="Include nested interventions")
    include_comments: bool = Field(default=True, description="Include existing comments")


class GetSourceInput(BaseModel):
    """Input for getting source content."""
    state_act_id: int = Field(..., description="StateAct ID")
    source_index: int = Field(default=0, ge=0, description="Which source to fetch (0-indexed)")
    fetch_content: bool = Field(default=True, description="Fetch and extract content")


class AddCommentInput(BaseModel):
    """Input for adding a comment."""
    measure_id: int = Field(..., description="StateAct ID")
    comment_text: str = Field(..., description="Full comment text (structured per spec)")
    template_id: Optional[int] = Field(default=None, description="Optional template ID")


class SetStatusInput(BaseModel):
    """Input for setting status."""
    state_act_id: int = Field(..., description="StateAct ID")
    new_status_id: int = Field(..., description="Status ID (2=Step1, 3=Publishable, 6=Under revision, 22=SC Reviewed)")
    comment: Optional[str] = Field(default=None, description="Optional reason for status change")


class AddFrameworkInput(BaseModel):
    """Input for adding framework tag."""
    state_act_id: int = Field(..., description="StateAct ID")
    framework_name: str = Field(default="sancho claudino review", description="Framework name")


class ListTemplatesInput(BaseModel):
    """Input for listing templates."""
    include_checklist: bool = Field(default=False, description="Include checklist templates")


class LogReviewInput(BaseModel):
    """Input for logging a review."""
    state_act_id: int = Field(..., description="StateAct ID")
    source_url: str = Field(..., description="Source URL used for validation")
    fields_validated: List[str] = Field(default_factory=list, description="List of fields checked")
    issues_found: List[str] = Field(default_factory=list, description="List of issues discovered (empty if none)")
    decision: str = Field(..., description="APPROVE or DISAPPROVE")
    actions_taken: List[str] = Field(default_factory=list, description="List of actions (comments posted, status changed, framework added)")


@mcp.tool(name="gta_mnt_list_step1_queue")
async def list_step1_queue(params: ListStep1QueueInput) -> str:
    """List measures awaiting Step 1 review, ordered by status_time DESC (most recent first).

    Uses api_state_act_status_log for accurate ordering.
    """
    db_client = get_db_client()
    data = await db_client.list_step1_queue(
        limit=params.limit,
        offset=params.offset,
        implementing_jurisdictions=params.implementing_jurisdictions,
        date_entered_review_gte=params.date_entered_review_gte
    )
    return format_step1_queue(data)


@mcp.tool(name="gta_mnt_get_measure")
async def get_measure(params: GetMeasureInput) -> str:
    """Get complete StateAct details including all interventions, comments, and source references.

    Returns full measure data for validation.
    """
    db_client = get_db_client()
    measure = await db_client.get_measure(
        state_act_id=params.state_act_id,
        include_interventions=params.include_interventions,
        include_comments=params.include_comments
    )
    return format_measure_detail(measure)


@mcp.tool(name="gta_mnt_get_source")
async def get_source(params: GetSourceInput) -> str:
    """Retrieve official source for a StateAct.

    Priority: S3 archived file, fallback to URL. Extracts text from PDFs and HTML.
    Use source_index to fetch different sources (0=first, 1=second, etc.).
    """
    db_client = get_db_client()
    source_fetcher = get_source_fetcher()

    # First get measure to retrieve source URLs
    measure = await db_client.get_measure(
        state_act_id=params.state_act_id,
        include_interventions=False,
        include_comments=False
    )

    # Check how many sources are available
    sources = measure.get('sources', [])
    if params.source_index >= len(sources):
        return f"❌ Source index {params.source_index} out of range. StateAct {params.state_act_id} has {len(sources)} source(s) (indices 0-{len(sources)-1})."

    # Fetch source using SourceFetcher
    source_result = await source_fetcher.get_source(
        state_act_id=params.state_act_id,
        measure_data=measure,
        fetch_content=params.fetch_content,
        source_index=params.source_index
    )

    return format_source_result(source_result)


@mcp.tool(name="gta_mnt_add_comment")
async def add_comment(params: AddCommentInput) -> str:
    """Add a structured review comment to a measure.

    Supports issue comments, verification comments, and review complete comments.
    """
    db_client = get_db_client()
    result = await db_client.add_comment(
        measure_id=params.measure_id,
        comment_text=params.comment_text,
        template_id=params.template_id
    )

    if result['success']:
        return f"✅ {result['message']}\n\nComment ID: {result['comment_id']}\nAuthor: Sancho Claudino (user_id={SANCHO_USER_ID})"
    else:
        return f"❌ {result['message']}"


@mcp.tool(name="gta_mnt_set_status")
async def set_status(params: SetStatusInput) -> str:
    """Update StateAct status (e.g., to 'Under revision' after issues found).

    Creates entry in api_state_act_status_log.
    """
    db_client = get_db_client()
    result = await db_client.set_status(
        state_act_id=params.state_act_id,
        new_status_id=params.new_status_id,
        comment=params.comment
    )

    if result['success']:
        return f"✅ {result['message']}\n\nStateAct {result['state_act_id']} → Status {result['new_status_id']}"
    else:
        return f"❌ {result['message']}"


@mcp.tool(name="gta_mnt_add_framework")
async def add_framework(params: AddFrameworkInput) -> str:
    """Attach 'sancho claudino review' framework tag to a measure for tracking.

    Use this to mark that a measure has been reviewed by Sancho Claudino.
    """
    db_client = get_db_client()
    result = await db_client.add_framework(
        state_act_id=params.state_act_id,
        framework_name=params.framework_name
    )

    if result['success']:
        if result.get('framework_id'):
            return f"✅ {result['message']}\n\nFramework ID: {result['framework_id']}"
        else:
            return f"✅ {result['message']}\n\nStatus ID: {result.get('status_id', 22)}"
    else:
        return f"❌ {result['message']}"


@mcp.tool(name="gta_mnt_list_templates")
async def list_templates(params: ListTemplatesInput) -> str:
    """List available comment templates for standardized feedback."""
    db_client = get_db_client()
    data = await db_client.list_templates(
        include_checklist=params.include_checklist
    )
    return format_templates(data)


@mcp.tool(name="gta_mnt_log_review")
async def log_review(params: LogReviewInput) -> str:
    """Save review log to persistent storage.

    Creates review-log.md with timestamp, source, fields validated, issues found, and actions taken.
    """
    from .storage import ReviewStorage
    storage = ReviewStorage()

    log_path = storage.save_log(
        state_act_id=params.state_act_id,
        source_url=params.source_url,
        fields_validated=params.fields_validated,
        issues_found=params.issues_found,
        decision=params.decision,
        actions_taken=params.actions_taken
    )

    return f"✅ Review log saved\n\nStateAct: {params.state_act_id}\nDecision: {params.decision}\nLog: {log_path}"


def main():
    """Entry point for running the GTA MNT MCP server."""
    # Check for required env vars (database credentials)
    required_vars = ['GTA_DB_HOST', 'GTA_DB_PASSWORD_WRITE']
    missing = [v for v in required_vars if not os.getenv(v)]

    # Also accept legacy credential names
    if 'GTA_DB_PASSWORD_WRITE' in missing and os.getenv('GTA_DB_PASSWORD'):
        missing.remove('GTA_DB_PASSWORD_WRITE')

    if missing:
        print(
            f"ERROR: Missing required environment variables: {', '.join(missing)}\n"
            "Please set database credentials before starting the server:\n"
            "  export GTA_DB_HOST='your-db-host'\n"
            "  export GTA_DB_PASSWORD_WRITE='your-password'\n"
            "  gta-mnt",
            file=sys.stderr
        )
        sys.exit(1)

    # Run the server with stdio transport (default for MCP)
    mcp.run()


if __name__ == "__main__":
    main()
