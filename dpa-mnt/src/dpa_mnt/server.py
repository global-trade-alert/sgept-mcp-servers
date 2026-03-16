"""MCP server for DPA monitoring and automated review.

Buzessa Claudini (reviewer) / Buzetta Claudini (author).
Uses direct MySQL access to lux_* tables for DPA Activity Tracker data.
"""

import os
import sys
from typing import Optional, List
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

from .api import DPADatabaseClient
from .source_fetcher import SourceFetcher
from .constants import SANCHO_USER_ID, DPA_FRAMEWORK_ID, REVIEWER_NAME, BC_REVIEW_ISSUE_ID
from .formatters import (
    format_review_queue,
    format_event_detail,
    format_intervention_context,
    format_source_result,
    format_templates
)


mcp = FastMCP("dpa_mnt")

_db_client: Optional[DPADatabaseClient] = None
_source_fetcher: Optional[SourceFetcher] = None


def get_db_client() -> DPADatabaseClient:
    global _db_client
    if _db_client is None:
        _db_client = DPADatabaseClient()
    return _db_client


def get_source_fetcher() -> SourceFetcher:
    global _source_fetcher
    if _source_fetcher is None:
        _source_fetcher = SourceFetcher()
    return _source_fetcher


# ============================================================================
# Input Models
# ============================================================================

class ListReviewQueueInput(BaseModel):
    """Input for listing review queue."""
    limit: int = Field(default=20, ge=1, le=100, description="Max events to return (1-100)")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter by jurisdiction codes (e.g., ['USA', 'CHN'])"
    )
    date_entered_review_gte: Optional[str] = Field(
        default=None,
        description="Filter by date entered review (YYYY-MM-DD)"
    )


class GetEventInput(BaseModel):
    """Input for getting event details."""
    event_id: int = Field(..., description="Event ID")
    include_intervention: bool = Field(default=True, description="Include intervention details")
    include_comments: bool = Field(default=True, description="Include existing comments")


class GetSourceInput(BaseModel):
    """Input for getting source content."""
    event_id: int = Field(..., description="Event ID")
    source_index: int = Field(default=0, ge=0, description="Which source to fetch (0-indexed)")
    fetch_content: bool = Field(default=True, description="Fetch and extract content")


class AddCommentInput(BaseModel):
    """Input for adding a comment."""
    event_id: int = Field(..., description="Event ID")
    comment_text: str = Field(..., description="Full comment text (structured per spec)")
    template_id: Optional[int] = Field(default=None, description="Optional template ID")


class SetStatusInput(BaseModel):
    """Input for setting status."""
    event_id: int = Field(..., description="Event ID")
    new_status_id: int = Field(..., description="Status ID: 3=Publishable (PASS), 4=Concern (CONDITIONAL), 5=Under revision (FAIL)")
    comment: Optional[str] = Field(default=None, description="Optional reason for status change")


class AddReviewTagInput(BaseModel):
    """Input for tagging an intervention as reviewed."""
    event_id: int = Field(..., description="Event ID (intervention is looked up automatically)")


class ListTemplatesInput(BaseModel):
    """Input for listing templates."""
    include_checklist: bool = Field(default=False, description="Include checklist templates")


class GetInterventionContextInput(BaseModel):
    """Input for getting intervention context (all sibling events)."""
    intervention_id: int = Field(..., description="Intervention ID (from get_event result)")


class LogReviewInput(BaseModel):
    """Input for logging a review."""
    event_id: int = Field(..., description="Event ID")
    intervention_id: int = Field(..., description="Intervention ID (from get_event result)")
    source_url: str = Field(..., description="Source URL used for validation")
    fields_validated: List[str] = Field(default_factory=list, description="List of fields checked")
    issues_found: List[str] = Field(default_factory=list, description="List of issues discovered (empty if none)")
    decision: str = Field(..., description="APPROVE or DISAPPROVE")
    actions_taken: List[str] = Field(default_factory=list, description="List of actions (comments posted, status changed, framework added)")


# ============================================================================
# Tools
# ============================================================================

@mcp.tool(name="dpa_mnt_list_review_queue")
async def list_review_queue(params: ListReviewQueueInput) -> str:
    """List DPA events awaiting review, ordered by date entered review (most recent first).

    Events with status_id=2 (AT: in step 1 review) are shown.
    """
    db_client = get_db_client()
    data = await db_client.list_review_queue(
        limit=params.limit,
        offset=params.offset,
        implementing_jurisdictions=params.implementing_jurisdictions,
        date_entered_review_gte=params.date_entered_review_gte
    )
    return format_review_queue(data)


@mcp.tool(name="dpa_mnt_get_event")
async def get_event(params: GetEventInput) -> str:
    """Get complete DPA event details including intervention, sources, and comments.

    Returns full event data for validation against official sources.
    """
    db_client = get_db_client()
    event_data = await db_client.get_event(
        event_id=params.event_id,
        include_intervention=params.include_intervention,
        include_comments=params.include_comments
    )
    return format_event_detail(event_data)


@mcp.tool(name="dpa_mnt_get_intervention_context")
async def get_intervention_context(params: GetInterventionContextInput) -> str:
    """Get all events on an intervention for lifecycle and consistency review.

    Returns intervention metadata plus ALL sibling events ordered by date.
    Published events (status 7) are verified context; in-review events are the
    review targets. Use this as the mandatory first step (Gate 0) before
    reviewing any individual event.
    """
    db_client = get_db_client()
    data = await db_client.get_intervention_context(
        intervention_id=params.intervention_id
    )
    return format_intervention_context(data)


@mcp.tool(name="dpa_mnt_get_source")
async def get_source(params: GetSourceInput) -> str:
    """Retrieve official source for a DPA event.

    Priority: source_url (web URL) first, file_url (S3 HTTP) fallback.
    Extracts text from PDFs and HTML. Use source_index for multiple sources.
    """
    db_client = get_db_client()
    source_fetcher = get_source_fetcher()

    # Get event to retrieve source list and intervention_id
    event_data = await db_client.get_event(
        event_id=params.event_id,
        include_intervention=False,
        include_comments=False
    )

    sources = event_data.get('sources', [])
    if params.source_index >= len(sources):
        return f"Source index {params.source_index} out of range. Event {params.event_id} has {len(sources)} source(s) (indices 0-{len(sources)-1})."

    source_data = sources[params.source_index]
    intervention_id = event_data.get('intervention_id')

    source_result = await source_fetcher.get_source(
        intervention_id=intervention_id,
        event_id=params.event_id,
        source_data=source_data,
        fetch_content=params.fetch_content
    )

    return format_source_result(source_result)


@mcp.tool(name="dpa_mnt_add_comment")
async def add_comment(params: AddCommentInput) -> str:
    """Add a structured review comment to a DPA event.

    Supports issue comments, verification comments, and review complete comments.
    """
    db_client = get_db_client()
    result = await db_client.add_comment(
        event_id=params.event_id,
        comment_text=params.comment_text,
        template_id=params.template_id
    )

    if result['success']:
        return f"Comment added.\n\nComment ID: {result['comment_id']}\nEvent: {params.event_id}\nAuthor: {REVIEWER_NAME} (user_id={SANCHO_USER_ID})"
    else:
        return f"Failed: {result['message']}"


@mcp.tool(name="dpa_mnt_set_status")
async def set_status(params: SetStatusInput) -> str:
    """Update DPA event status (e.g., to 'Under revision' after issues found).

    Creates entry in lux_event_status_log.

    Status IDs: 3=Publishable (PASS), 4=Concern (CONDITIONAL/ESCALATION), 5=Under revision (FAIL).
    """
    db_client = get_db_client()
    result = await db_client.set_status(
        event_id=params.event_id,
        new_status_id=params.new_status_id,
        comment=params.comment
    )

    if result['success']:
        return f"Status updated.\n\nEvent {result['event_id']} -> Status {result['new_status_id']}"
    else:
        return f"Failed: {result['message']}"


@mcp.tool(name="dpa_mnt_add_review_tag")
async def add_review_tag(params: AddReviewTagInput) -> str:
    """Tag the intervention with 'BC review' issue after reviewing an event.

    Looks up the intervention from the event_id and adds issue 83 ('BC review')
    to lux_intervention_issue_log. Idempotent — safe to call multiple times.
    Call this after every completed review (PASS, CONDITIONAL, or FAIL).
    """
    db_client = get_db_client()
    result = await db_client.add_review_tag(
        event_id=params.event_id
    )

    if result['success']:
        return f"Review tag applied.\n\nIntervention: {result.get('intervention_id')}\nIssue ID: {BC_REVIEW_ISSUE_ID} (BC review)\nEvent: {params.event_id}\n{result['message']}"
    else:
        return f"Failed: {result['message']}"


@mcp.tool(name="dpa_mnt_list_templates")
async def list_templates(params: ListTemplatesInput) -> str:
    """List available comment templates for standardised feedback."""
    db_client = get_db_client()
    data = await db_client.list_templates(
        include_checklist=params.include_checklist
    )
    return format_templates(data)


@mcp.tool(name="dpa_mnt_log_review")
async def log_review(params: LogReviewInput) -> str:
    """Save review log to persistent storage.

    Creates review-log.md with timestamp, source, fields validated, issues found, and actions taken.
    """
    from .storage import ReviewStorage
    storage = ReviewStorage()

    log_path = storage.save_log(
        intervention_id=params.intervention_id,
        event_id=params.event_id,
        source_url=params.source_url,
        fields_validated=params.fields_validated,
        issues_found=params.issues_found,
        decision=params.decision,
        actions_taken=params.actions_taken
    )

    return f"Review log saved.\n\nEvent: {params.event_id}\nIntervention: {params.intervention_id}\nDecision: {params.decision}\nLog: {log_path}"


def main():
    """Entry point for running the DPA MNT MCP server."""
    required_vars = ['GTA_DB_HOST', 'GTA_DB_PASSWORD_WRITE']
    missing = [v for v in required_vars if not os.getenv(v)]

    if 'GTA_DB_PASSWORD_WRITE' in missing and os.getenv('GTA_DB_PASSWORD'):
        missing.remove('GTA_DB_PASSWORD_WRITE')

    if missing:
        print(
            f"ERROR: Missing required environment variables: {', '.join(missing)}\n"
            "Please set database credentials before starting the server:\n"
            "  export GTA_DB_HOST='your-db-host'\n"
            "  export GTA_DB_PASSWORD_WRITE='your-password'\n"
            "  dpa-mnt",
            file=sys.stderr
        )
        sys.exit(1)

    mcp.run()


if __name__ == "__main__":
    main()
