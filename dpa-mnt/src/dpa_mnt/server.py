"""MCP server for DPA monitoring and automated review.

Buzessa Claudini (reviewer) / Buzetta Claudini (author).
Uses direct MySQL access to lux_* tables for DPA Activity Tracker data.
"""

import asyncio
import os
import sys
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .api import DPADatabaseClient
from .source_fetcher import SourceFetcher
from .constants import (
    SANCHO_USER_ID,
    DPA_FRAMEWORK_ID,
    REVIEWER_NAME,
    BC_REVIEW_ISSUE_ID,
    VALID_STATUS_IDS,
    STATUS_ID_NAMES,
)
from .formatters import (
    format_review_queue,
    format_event_detail,
    format_intervention_context,
    format_source_result,
    format_templates
)


mcp = FastMCP("dpa_mnt")


# Shared base for all MCP tool inputs. Strips whitespace on strings,
# rejects unknown fields (catches LLM field-name drift like `status_id`
# vs `new_status_id`, or `measure_id` vs `event_id`), and revalidates on
# attribute assignment.
class _StrictInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid',
        validate_assignment=True,
    )


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

class ListReviewQueueInput(_StrictInput):
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


class GetEventInput(_StrictInput):
    """Input for getting event details."""
    event_id: int = Field(..., description="Event ID")
    include_intervention: bool = Field(default=True, description="Include intervention details")
    include_comments: bool = Field(default=True, description="Include existing comments")


class GetSourceInput(_StrictInput):
    """Input for getting source content."""
    event_id: int = Field(..., description="Event ID")
    source_index: int = Field(default=0, ge=0, description="Which source to fetch (0-indexed)")
    fetch_content: bool = Field(default=True, description="Fetch and extract content")


class AddCommentInput(_StrictInput):
    """Input for adding a comment."""
    event_id: int = Field(..., description="Event ID")
    comment_text: str = Field(..., description="Full comment text (structured per spec)")
    template_id: Optional[int] = Field(default=None, description="Optional template ID")


class SetStatusInput(_StrictInput):
    """Input for setting status.

    Review outcomes: 3=Publishable (PASS), 4=Concern (CONDITIONAL/ESCALATION),
    5=Under revision (FAIL). Other valid statuses exist but are set by the
    dashboard, not by review tools.
    """
    event_id: int = Field(..., description="Event ID")
    new_status_id: int = Field(
        ...,
        description=(
            "Status ID — review outcomes: 3=Publishable, 4=Concern, 5=Under revision. "
            "Full valid set {1,2,3,4,5,7}; see STATUS_ID_NAMES in constants."
        ),
    )
    comment: Optional[str] = Field(default=None, description="Optional reason for status change")

    @field_validator('new_status_id')
    @classmethod
    def _status_id_must_be_known(cls, v: int) -> int:
        if v not in VALID_STATUS_IDS:
            valid_pairs = ", ".join(
                f"{sid}={name}" for sid, name in sorted(STATUS_ID_NAMES.items())
            )
            raise ValueError(
                f"new_status_id must be one of {{{', '.join(str(s) for s in sorted(VALID_STATUS_IDS))}}} "
                f"({valid_pairs}); got {v}"
            )
        return v


class AddReviewTagInput(_StrictInput):
    """Input for tagging an intervention as reviewed."""
    event_id: int = Field(..., description="Event ID (intervention is looked up automatically)")


class ListTemplatesInput(_StrictInput):
    """Input for listing templates."""
    include_checklist: bool = Field(default=False, description="Include checklist templates")


class GetInterventionContextInput(_StrictInput):
    """Input for getting intervention context (all sibling events)."""
    intervention_id: int = Field(..., description="Intervention ID (from get_event result)")


class LookupEventAnalystsInput(_StrictInput):
    """Input for looking up analysts who created events."""
    event_ids: List[int] = Field(..., description="List of event IDs to look up creators for")


class LogReviewInput(_StrictInput):
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
    data = await asyncio.to_thread(
        db_client.list_review_queue,
        limit=params.limit,
        offset=params.offset,
        implementing_jurisdictions=params.implementing_jurisdictions,
        date_entered_review_gte=params.date_entered_review_gte,
    )
    return format_review_queue(data)


@mcp.tool(name="dpa_mnt_get_event")
async def get_event(params: GetEventInput) -> str:
    """Get complete DPA event details including intervention, sources, and comments.

    Returns full event data for validation against official sources, with the
    event's author (first user to touch the event) and — when include_intervention=True —
    the intervention's benchmarks, issues, rationales, and linked agents.
    """
    db_client = get_db_client()
    event_data = await asyncio.to_thread(
        db_client.get_event,
        event_id=params.event_id,
        include_intervention=params.include_intervention,
        include_comments=params.include_comments,
    )
    if isinstance(event_data, dict) and event_data.get("error"):
        raise ToolError(event_data["error"])
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
    data = await asyncio.to_thread(
        db_client.get_intervention_context,
        intervention_id=params.intervention_id,
    )
    if isinstance(data, dict) and data.get("error"):
        raise ToolError(data["error"])
    return format_intervention_context(data)


@mcp.tool(name="dpa_mnt_get_source")
async def get_source(params: GetSourceInput) -> str:
    """Retrieve official source for a DPA event.

    Priority: source_url (web URL) first, file_url (S3 HTTP) fallback.
    Extracts text from PDFs and HTML. Use source_index for multiple sources.
    """
    db_client = get_db_client()
    source_fetcher = get_source_fetcher()

    event_data = await asyncio.to_thread(
        db_client.get_event,
        event_id=params.event_id,
        include_intervention=False,
        include_comments=False,
    )
    if isinstance(event_data, dict) and event_data.get("error"):
        raise ToolError(event_data["error"])

    sources = event_data.get('sources', [])
    if not sources:
        raise ToolError(f"Event {params.event_id} has no linked sources.")
    if params.source_index >= len(sources):
        raise ToolError(
            f"source_index {params.source_index} out of range for event {params.event_id} "
            f"(valid indices 0-{len(sources) - 1})."
        )

    source_data = sources[params.source_index]
    intervention_id = event_data.get('event', {}).get('intervention_id')

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
    result = await asyncio.to_thread(
        db_client.add_comment,
        event_id=params.event_id,
        comment_text=params.comment_text,
        template_id=params.template_id,
    )

    if not result.get('success'):
        raise ToolError(result.get('message') or 'Failed to add comment')

    return (
        f"Comment added.\n\n"
        f"Comment ID: {result['comment_id']}\n"
        f"Event: {params.event_id}\n"
        f"Author: {REVIEWER_NAME} (user_id={SANCHO_USER_ID})"
    )


@mcp.tool(name="dpa_mnt_set_status")
async def set_status(params: SetStatusInput) -> str:
    """Update DPA event status (e.g., to 'Under revision' after issues found).

    Creates entry in lux_event_status_log.

    Review outcomes: 3=Publishable (PASS), 4=Concern (CONDITIONAL/ESCALATION),
    5=Under revision (FAIL). Validator rejects any other integer with an
    enumerated error message.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(
        db_client.set_status,
        event_id=params.event_id,
        new_status_id=params.new_status_id,
        comment=params.comment,
    )

    if not result.get('success'):
        raise ToolError(result.get('message') or 'Failed to update status')

    return f"Status updated.\n\nEvent {result['event_id']} -> Status {result['new_status_id']}"


@mcp.tool(name="dpa_mnt_add_review_tag")
async def add_review_tag(params: AddReviewTagInput) -> str:
    """Tag the intervention with 'BC review' issue after reviewing an event.

    Looks up the intervention from the event_id and adds issue 83 ('BC review')
    to lux_intervention_issue_log. Idempotent — safe to call multiple times.
    Call this after every completed review (PASS, CONDITIONAL, or FAIL).
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(
        db_client.add_review_tag,
        event_id=params.event_id,
    )

    if not result.get('success'):
        raise ToolError(result.get('message') or 'Failed to add review tag')

    return (
        f"Review tag applied.\n\n"
        f"Intervention: {result.get('intervention_id')}\n"
        f"Issue ID: {BC_REVIEW_ISSUE_ID} (BC review)\n"
        f"Event: {params.event_id}\n"
        f"{result['message']}"
    )


@mcp.tool(name="dpa_mnt_list_templates")
async def list_templates(params: ListTemplatesInput) -> str:
    """List available comment templates for standardised feedback."""
    db_client = get_db_client()
    data = await asyncio.to_thread(
        db_client.list_templates,
        include_checklist=params.include_checklist,
    )
    return format_templates(data)


@mcp.tool(name="dpa_mnt_log_review")
async def log_review(params: LogReviewInput) -> str:
    """Save review log to persistent storage.

    Creates review-log.md with timestamp, source, fields validated, issues found, and actions taken.
    """
    from .storage import ReviewStorage
    storage = ReviewStorage()

    log_path = await asyncio.to_thread(
        storage.save_log,
        intervention_id=params.intervention_id,
        event_id=params.event_id,
        source_url=params.source_url,
        fields_validated=params.fields_validated,
        issues_found=params.issues_found,
        decision=params.decision,
        actions_taken=params.actions_taken,
    )

    return (
        f"Review log saved.\n\n"
        f"Event: {params.event_id}\n"
        f"Intervention: {params.intervention_id}\n"
        f"Decision: {params.decision}\n"
        f"Log: {log_path}"
    )


@mcp.tool(name="dpa_mnt_lookup_analysts")
async def lookup_event_analysts(params: LookupEventAnalystsInput) -> str:
    """Look up which analyst created each event.

    Returns the user who set status_id=1 (created/in progress) for each event,
    with their name. Useful for Slack notifications after batch reviews.
    """
    db_client = get_db_client()
    data = await asyncio.to_thread(db_client.lookup_event_analysts, params.event_ids)

    if not data['analysts']:
        return "No analyst records found for the given event IDs."

    lines = ["# Event Analysts\n"]
    for row in data['analysts']:
        name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip() or "Unknown"
        lines.append(f"- Event {row['event_id']}: user_id={row['user_id']} ({name})")

    return '\n'.join(lines)


# ============================================================================
# MCP Resources — agent-facing reference docs
# ============================================================================

from .resources_loader import load_resource as _load_resource  # noqa: E402


@mcp.resource(
    "dpa-mnt://review-criteria",
    name="Buzessa Claudini Review Criteria",
    description="Minimum field-surface for a DPA review, criticality rubric, and verdict→tool-call mapping.",
    mime_type="text/markdown",
)
def _res_review_criteria() -> str:
    return _load_resource("review_criteria")


@mcp.resource(
    "dpa-mnt://status-id-decision-tree",
    name="DPA Status ID Decision Tree",
    description="Which of the six valid DPA status IDs (1/2/3/4/5/7) to use, with flow diagrams for reviewer and author paths.",
    mime_type="text/markdown",
)
def _res_status_tree() -> str:
    return _load_resource("status_id_decision_tree")


@mcp.resource(
    "dpa-mnt://comment-templates",
    name="DPA Comment Template Catalogue",
    description="Canonical issue / verification / review-complete comment structures for DPA review, and which formatter helper to call.",
    mime_type="text/markdown",
)
def _res_comment_templates() -> str:
    return _load_resource("comment_templates")


@mcp.resource(
    "dpa-mnt://issue-ids",
    name="DPA Issue IDs",
    description="The BC review issue tag (83) attached by Buzessa reviews to interventions, plus guidance on thematic tag semantics.",
    mime_type="text/markdown",
)
def _res_issue_ids() -> str:
    return _load_resource("issue_ids")


@mcp.resource(
    "dpa-mnt://source-extraction-notes",
    name="DPA Source Extraction Notes",
    description="URL / S3 / PDF / HTML extraction gotchas for dpa_mnt_get_source. Read before chasing source-mismatch bugs.",
    mime_type="text/markdown",
)
def _res_source_extraction() -> str:
    return _load_resource("source_extraction_notes")


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
