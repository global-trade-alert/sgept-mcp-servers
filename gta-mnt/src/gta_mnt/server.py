"""MCP server for GTA monitoring, review, and entry creation.

Two automated users with strictly separated roles:
- Sancho Claudino (9900): REVIEWER — comments, status changes, framework tags
- Sancho Claudito (9901): AUTHOR — creates state acts, interventions, relationships

These must never be mixed. A reviewer must not appear as entry author.
"""

import asyncio
import os
import sys
from typing import Optional, List
import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .api import GTADatabaseClient, BastiatAPIClient, semantic_search_via_rag
from .source_fetcher import SourceFetcher
from .constants import (
    SANCHO_USER_ID,
    SANCHO_AUTHOR_ID,
    SANCHO_FRAMEWORK_ID,
    FRAMEWORK_IDS,
)
from .formatters import (
    format_step1_queue,
    format_measure_detail,
    format_source_result,
    format_templates,
    format_guessed_hs_codes
)


# Initialize FastMCP server
mcp = FastMCP("gta_mnt")


# Shared base for all MCP tool inputs. Strips whitespace on strings,
# rejects unknown fields (catches LLM field-name drift like `status_id`
# vs `new_status_id`), and revalidates on attribute assignment.
class _StrictInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid',
        validate_assignment=True,
    )

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
class ListStep1QueueInput(_StrictInput):
    """Input for listing Step 1 review queue."""
    limit: Optional[int] = Field(default=None, ge=1, description="Max measures to return. Omit or null to return all.")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter by jurisdiction codes (e.g., ['USA', 'CHN'])"
    )
    date_entered_review_gte: Optional[str] = Field(
        default=None,
        description="Filter by date entered review (YYYY-MM-DD)"
    )
    exclude_framework_id: Optional[int] = Field(
        default=None,
        description="Exclude measures that have this framework ID attached (e.g., 495 for 'sancho claudino review')"
    )


class ListStep2QueueInput(_StrictInput):
    """Input for listing Step 2 review queue."""
    limit: Optional[int] = Field(default=None, ge=1, description="Max measures to return. Omit or null to return all.")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter by jurisdiction codes (e.g., ['USA', 'CHN'])"
    )
    date_entered_review_gte: Optional[str] = Field(
        default=None,
        description="Filter by date entered review (YYYY-MM-DD)"
    )
    exclude_framework_id: Optional[int] = Field(
        default=None,
        description="Exclude measures that have this framework ID attached (e.g., 495 for 'sancho claudino review')"
    )


class ListQueueByStatusInput(_StrictInput):
    """Input for listing measures by arbitrary status ID."""
    status_id: int = Field(..., description="Status ID: 1=In progress, 2=Step 1, 3=Publishable, 6=Under revision, 19=Step 2")
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


class GetMeasureInput(_StrictInput):
    """Input for getting measure details."""
    state_act_id: int = Field(..., description="StateAct ID")
    include_interventions: bool = Field(default=True, description="Include nested interventions")
    include_comments: bool = Field(default=True, description="Include existing comments")


class GetSourceInput(_StrictInput):
    """Input for getting source content."""
    state_act_id: int = Field(..., description="StateAct ID")
    source_index: int = Field(default=0, ge=0, description="Which source to fetch (0-indexed)")
    fetch_content: bool = Field(default=True, description="Fetch and extract content")


class AddCommentInput(_StrictInput):
    """Input for adding a comment."""
    measure_id: int = Field(..., description="StateAct ID")
    comment_text: str = Field(..., description="Full comment text (structured per spec)")
    template_id: Optional[int] = Field(default=None, description="Optional template ID")


_VALID_STATUS_IDS = {1, 2, 3, 6, 19}


class SetStatusInput(_StrictInput):
    """Input for setting status."""
    state_act_id: int = Field(..., description="StateAct ID")
    new_status_id: int = Field(..., description="Status ID (2=Step1, 3=Publishable, 6=Under revision, 19=Step2)")
    comment: Optional[str] = Field(default=None, description="Optional reason for status change")

    @field_validator('new_status_id')
    @classmethod
    def _status_id_must_be_known(cls, v: int) -> int:
        if v not in _VALID_STATUS_IDS:
            raise ValueError(
                f"new_status_id must be one of {{1, 2, 3, 6, 19}} "
                "(1=In progress, 2=Step 1 review, 3=Publishable, 6=Under revision, 19=Step 2 review); "
                f"got {v}"
            )
        return v


class AddFrameworkInput(_StrictInput):
    """Input for adding framework tag."""
    state_act_id: int = Field(..., description="StateAct ID")
    framework_name: str = Field(default="sancho claudino review", description="Framework name")


class ListTemplatesInput(_StrictInput):
    """Input for listing templates."""
    include_checklist: bool = Field(default=False, description="Include checklist templates")


class LogReviewInput(_StrictInput):
    """Input for logging a review."""
    state_act_id: int = Field(..., description="StateAct ID")
    source_url: str = Field(..., description="Source URL used for validation")
    fields_validated: List[str] = Field(default_factory=list, description="List of fields checked")
    issues_found: List[str] = Field(default_factory=list, description="List of issues discovered (empty if none)")
    decision: str = Field(..., description="APPROVE or DISAPPROVE")
    actions_taken: List[str] = Field(default_factory=list, description="List of actions (comments posted, status changed, framework added)")


# ========================================================================
# Entry Creation Input Models
# ========================================================================

class LookupInput(_StrictInput):
    """Input for looking up reference table values."""
    table: str = Field(..., description="Table short name: jurisdiction, product, sector, rationale, unit, firm, intervention_type, mast_chapter, mast_subchapter, evaluation, affected_flow, eligible_firm, implementation_level, intervention_area, firm_role, level_type, action")
    query: str = Field(..., description="Search string (matched with LIKE %%query%%)")
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")


class CreateStateActInput(_StrictInput):
    """Input for creating a new state act (measure)."""
    title: str = Field(..., description="State act title")
    description: str = Field(..., description="Announcement description text")
    source_url: str = Field(..., description="Primary source URL")
    is_source_official: int = Field(..., description="1 if official source, 0 if not")
    date_announced: str = Field(..., description="Date announced (YYYY-MM-DD)")
    evaluation_id: int = Field(..., description="1=Red, 2=Amber, 3=Green")
    source_citation: Optional[str] = Field(
        default=None,
        description="Full GTA citation string: 'Author (Date). TITLE. Publisher (Retrieved date): URL'. Stored in source_markdown and source fields. Falls back to source_url if omitted."
    )
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class CreateInterventionInput(_StrictInput):
    """Input for creating a new intervention."""
    state_act_id: int = Field(..., description="FK to state act (from gta_mnt_create_state_act)")
    description: str = Field(..., description="Intervention description text")
    intervention_type_id: int = Field(..., description="FK to api_intervention_type_list (e.g. 81=Equity stake)")
    chapter_id: int = Field(..., description="MAST chapter ID (e.g. 10=L)")
    subchapter_id: int = Field(..., description="MAST subchapter ID (e.g. 55=L13)")
    gta_evaluation_id: int = Field(..., description="1=Red, 2=Amber, 3=Green")
    affected_flow_id: int = Field(..., description="1=Inward, 2=Outward, 3=Outward subsidy")
    eligible_firm_id: int = Field(..., description="FK to api_eligible_firm_list (e.g. 3=firm-specific)")
    implementation_level_id: int = Field(..., description="FK to api_implementation_level_list (e.g. 6=NFI)")
    intervention_area_id: int = Field(..., description="1=goods, 2=service, 3=investment, 4=migration")
    date_implemented: str = Field(..., description="Implementation date (YYYY-MM-DD)")
    date_announced: str = Field(..., description="Announcement date (YYYY-MM-DD)")
    title: Optional[str] = Field(default=None, description="Optional title (defaults to state act title)")
    announced_as_temporary: int = Field(default=0, description="0=permanent, 1=temporary")
    is_horizontal: int = Field(default=0, description="1 if measure affects practically all sectors with uncertain intensity. Mutually exclusive with specific products/sectors (QC-TAX-005).")
    aj_type: int = Field(default=1, description="1=inferred, 2=targeted, 3=excluded, 4=incidental")
    dm_type: int = Field(default=1, description="1=inferred, 2=targeted, 3=excluded, 4=incidental")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddIJInput(_StrictInput):
    """Input for adding implementing jurisdiction to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    jurisdiction_id: int = Field(..., description="FK to api_jurisdiction_list (look up via gta_mnt_lookup)")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddProductInput(_StrictInput):
    """Input for adding affected product (HS6) to an intervention. For sources
    that publish at HS8/10/12/14, use gta_mnt_add_product_level instead."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    product_id: int = Field(..., description="FK to api_product_list (look up HS code via gta_mnt_lookup)")
    prior_level: Optional[str] = Field(default=None, description="Prior tariff/level value for this product (e.g. '5.0')")
    new_level: Optional[str] = Field(default=None, description="New tariff/level value for this product (e.g. '25.0')")
    unit_id: Optional[int] = Field(default=None, description="FK to api_unit_list (look up via gta_mnt_lookup table='unit')")
    date_implemented: Optional[str] = Field(default=None, description="Per-product implementation date (YYYY-MM-DD)")
    date_removed: Optional[str] = Field(default=None, description="Per-product removal date (YYYY-MM-DD)")
    is_investigated_only: bool = Field(default=False, description="True for trade-defence cases (anti-dumping/anti-subsidy/safeguard) where this product is under investigation only; False for ordinary affected products")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddSectorInput(_StrictInput):
    """Input for adding affected sector to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    sector_id: int = Field(..., description="FK to api_sector_list")
    sector_type: str = Field(default='N', description="'N'=normal, 'A'=additional, 'D'=deleted")
    is_investigated_only: bool = Field(default=False, description="True for trade-defence cases where this sector is under investigation only; False for normal affected-sector tags")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddProductLevelInput(_StrictInput):
    """Input for adding a tariff-line row at HS8/10/12/14 to an intervention.

    Analysts insert at the ORIGINAL SOURCE's HS granularity — if the source
    publishes 10-digit codes, pass level=10; if it publishes 8-digit codes,
    pass level=8. The gta-api back-end aggregates upward to HS6 and produces
    the A/A_MIN/A_MAX type markers on coarser tables; this tool always writes
    type='N'.

    HS code formatting: pass the source's HS code as a string in any of:
      '0102.10.20', '0102-10-20', '0102 10 20', '01021020'
    The handler strips non-digits and validates the length matches `level`.
    Leading zeros (chapters 01–09) survive validation; the master table stores
    HS codes as integers and drops them, but the lookup remains consistent
    because both sides drop the same way.
    """
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    level: int = Field(..., description="HS granularity: 8, 10, 12, or 14")
    hs_code: str = Field(..., description="HS code as stated in the source (any common formatting; will be cleaned)")
    jurisdiction_id: int = Field(..., description="FK to api_jurisdiction_list — jurisdiction whose tariff schedule this line belongs to")
    prior_value: Optional[str] = Field(default=None, description="Prior tariff/level value (e.g. '5.0')")
    new_value: Optional[str] = Field(default=None, description="New tariff/level value (e.g. '25.0')")
    unit_id: Optional[int] = Field(default=None, description="FK to api_unit_list (lookup table='unit')")
    date_implemented: Optional[str] = Field(default=None, description="Implementation date (YYYY-MM-DD)")
    date_removed: Optional[str] = Field(default=None, description="Removal date (YYYY-MM-DD)")
    is_investigated_only: bool = Field(default=False, description="True for trade-defence cases under investigation only")
    is_in_original: bool = Field(default=True, description="True if this code appears in the original source")
    is_positively_affected: bool = Field(default=False, description="True if the measure is favourable to the product")
    is_tariff_line_official: bool = Field(default=True, description="True if this comes from an official tariff schedule")
    is_tariff_peak: Optional[int] = Field(default=None, description="Optional tariff-peak flag (0/1)")
    action_id: Optional[int] = Field(default=None, description="FK to api_action_log. REQUIRED for level 8/10 (lookup table='action'); ignored for level 12/14")
    applicability_reason_id: int = Field(default=1, description="1='explicit in scope' (default), 2='explicit out of scope', 3='implicit in scope'. Level 8/10 only")
    verification_status_id: int = Field(default=1, description="1='HS code is in official source (HS 2022)' (default), 2='HS 2017 or earlier', 3='Not official'. Level 8/10 only")
    is_completely_captured: bool = Field(default=False, description="Aggregation hint; default False. Level 8/10 only")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddRationaleInput(_StrictInput):
    """Input for adding rationale/motive to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    rationale_id: int = Field(..., description="FK to api_rationale_list")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddFirmInput(_StrictInput):
    """Input for adding a firm to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    firm_name: str = Field(..., description="Firm name (looked up or created in mtz_firm_log)")
    role_id: int = Field(..., description="FK to mtz_firm_role: 1=beneficiary, 2=target, 3=acting agency, 4=petitioner, 5=exempted, 6=intermediary")
    jurisdiction_id: Optional[int] = Field(default=None, description="Optional: firm's home jurisdiction ID")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddSourceInput(_StrictInput):
    """Input for adding a source URL to a state act."""
    state_act_id: int = Field(..., description="FK to api_state_act_log")
    source_url: str = Field(..., description="Source URL")
    source_citation: Optional[str] = Field(default=None, description="Full GTA citation string (e.g. 'Author (Date). TITLE. Publisher (Retrieved): URL'). Stored in api_state_act_source_log_new for admin dashboard display. If omitted, source_url is used.")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class QueueRecalculationInput(_StrictInput):
    """Input for queuing AJ/DM recalculation."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddMotiveQuoteInput(_StrictInput):
    """Input for adding a stated motive quote to a state act."""
    state_act_id: int = Field(..., description="FK to api_state_act_log")
    motive_quote: str = Field(..., description="The quoted text from the source justifying the motive tag")
    source_url: Optional[str] = Field(default=None, description="URL where the quote was found")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddLevelInput(_StrictInput):
    """Input for adding a level row to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    prior_level: Optional[str] = Field(default=None, description="Prior level value")
    new_level: Optional[str] = Field(default=None, description="New level value")
    unit_id: Optional[int] = Field(default=None, description="FK to api_unit_list")
    level_type_id: Optional[int] = Field(default=None, description="FK to api_level_type_list")
    tariff_peak: Optional[int] = Field(default=None, description="Tariff peak indicator")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class FindDuplicatesInput(_StrictInput):
    """Input for find_duplicates duplicate detection.

    Either pass `state_act_id` (canonical fields are read from the DB) or pass
    the identity fields directly (useful before insertion).
    """
    state_act_id: Optional[int] = Field(default=None, description="If set, identity fields are read from the DB")
    jurisdiction_ids: Optional[List[int]] = Field(default=None, description="Implementing jurisdiction FK list")
    date_announced: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    intervention_type_ids: Optional[List[int]] = Field(default=None, description="api_intervention_type_list IDs")
    hs_codes: Optional[List[str]] = Field(default=None, description="HS6 codes (strings or numerics)")
    source_urls: Optional[List[str]] = Field(default=None, description="Official source URLs to match against api_state_act_source")
    title: Optional[str] = Field(default=None, description="Draft title (used for decree-number regex)")
    description: Optional[str] = Field(default=None, description="Draft description (used for semantic search query)")
    exclude_state_act_ids: Optional[List[int]] = Field(default=None, description="State act IDs to omit from results")
    date_window_days: int = Field(default=60, ge=0, le=365, description="Date window for vectors D and E (±days)")
    include_statuses: Optional[List[int]] = Field(default=None, description="Status IDs to consider; default [1,2,3,4,6,19]")
    limit: int = Field(default=20, ge=1, le=200, description="Max candidates to return")
    semantic_search: bool = Field(default=True, description="Run Vector G via the RAG (skipped if RAG_BASE_URL/RAG_API_KEY not set)")
    semantic_threshold_review: float = Field(default=0.70, ge=0.0, le=1.0, description="Minimum cosine score to include in results")


@mcp.tool(name="gta_mnt_list_step1_queue")
async def list_step1_queue(params: ListStep1QueueInput) -> str:
    """List measures awaiting Step 1 review, ordered by status_time DESC (most recent first).

    Uses api_state_act_status_log for accurate ordering.
    Pass exclude_framework_id=495 to exclude measures already reviewed by Sancho Claudino.
    """
    db_client = get_db_client()
    data = await asyncio.to_thread(db_client.list_step1_queue, 
        limit=params.limit,
        offset=params.offset,
        implementing_jurisdictions=params.implementing_jurisdictions,
        date_entered_review_gte=params.date_entered_review_gte,
        exclude_framework_id=params.exclude_framework_id
    )
    return format_step1_queue(data)


@mcp.tool(name="gta_mnt_list_step2_queue")
async def list_step2_queue(params: ListStep2QueueInput) -> str:
    """List measures awaiting Step 2 review (status 19), ordered by status_time DESC.

    Uses api_state_act_status_log for accurate ordering.
    Pass exclude_framework_id=495 to exclude measures already reviewed by Sancho Claudino.
    """
    db_client = get_db_client()
    data = await asyncio.to_thread(db_client.list_step1_queue, 
        status_id=19,
        limit=params.limit,
        offset=params.offset,
        implementing_jurisdictions=params.implementing_jurisdictions,
        date_entered_review_gte=params.date_entered_review_gte,
        exclude_framework_id=params.exclude_framework_id
    )
    return format_step1_queue(data, queue_label="Step 2")


STATUS_LABELS = {1: "In Progress", 2: "Step 1", 3: "Publishable", 6: "Under Revision", 19: "Step 2"}


@mcp.tool(name="gta_mnt_list_queue_by_status")
async def list_queue_by_status(params: ListQueueByStatusInput) -> str:
    """List measures by any status ID. Useful for checking unpublished pipeline entries.

    Status IDs: 1=In progress, 2=Step 1 review, 3=Publishable, 6=Under revision, 19=Step 2 review.
    """
    db_client = get_db_client()
    data = await asyncio.to_thread(db_client.list_step1_queue, 
        status_id=params.status_id,
        limit=params.limit,
        offset=params.offset,
        implementing_jurisdictions=params.implementing_jurisdictions,
        date_entered_review_gte=params.date_entered_review_gte
    )
    label = STATUS_LABELS.get(params.status_id, f"Status {params.status_id}")
    return format_step1_queue(data, queue_label=label)


@mcp.tool(name="gta_mnt_get_measure")
async def get_measure(params: GetMeasureInput) -> str:
    """Get complete StateAct details including all interventions, comments, and source references.

    Returns full measure data for validation.
    """
    db_client = get_db_client()
    measure = await asyncio.to_thread(db_client.get_measure, 
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
    measure = await asyncio.to_thread(db_client.get_measure, 
        state_act_id=params.state_act_id,
        include_interventions=False,
        include_comments=False
    )

    # Check how many sources are available
    sources = measure.get('sources', [])
    if not sources:
        raise ToolError(
            f"StateAct {params.state_act_id} has no linked sources. "
            "Cannot fetch source content."
        )
    if params.source_index >= len(sources):
        raise ToolError(
            f"source_index {params.source_index} out of range. "
            f"StateAct {params.state_act_id} has {len(sources)} source(s) "
            f"(valid indices 0-{len(sources) - 1})."
        )

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
    result = await asyncio.to_thread(db_client.add_comment, 
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
    result = await asyncio.to_thread(db_client.set_status, 
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
    """Attach a framework tag to a measure for tracking.

    Supported frameworks:
    - 'sancho claudino review' (ID 495, default) — marks a measure as reviewed by Sancho Claudino
    - 'sancho claudito reported' (ID 500) — marks a measure as first-drafted by Sancho Claudito
    """
    if params.framework_name not in FRAMEWORK_IDS:
        known = ", ".join(f"'{name}'" for name in FRAMEWORK_IDS)
        raise ToolError(
            f"Unknown framework_name '{params.framework_name}'. "
            f"Supported frameworks: {known}."
        )

    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_framework,
        state_act_id=params.state_act_id,
        framework_name=params.framework_name
    )

    if result['success']:
        return f"✅ {result['message']}\n\nFramework ID: {result['framework_id']}"
    else:
        return f"❌ {result['message']}"


@mcp.tool(name="gta_mnt_list_templates")
async def list_templates(params: ListTemplatesInput) -> str:
    """List available comment templates for standardized feedback."""
    db_client = get_db_client()
    data = await asyncio.to_thread(db_client.list_templates, 
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


# ========================================================================
# Entry Creation Tools
# ========================================================================

@mcp.tool(name="gta_mnt_lookup")
async def lookup(params: LookupInput) -> str:
    """Look up IDs in GTA reference tables by search string.

    Supports: jurisdiction, product, sector, rationale, unit, firm, intervention_type,
    mast_chapter, mast_subchapter, evaluation, affected_flow, eligible_firm,
    implementation_level, intervention_area, firm_role, level_type, action.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.lookup, 
        table=params.table,
        query=params.query,
        limit=params.limit
    )

    if result.get('error'):
        return f"❌ {result['error']}"

    results = result['results']
    if not results:
        return f"No matches for '{params.query}' in {result['table']}"

    lines = [f"# Lookup: {result['table']} ({len(results)} results)\n"]
    for row in results:
        lines.append(f"- **{row.get(result['id_column'], 'N/A')}**: {row.get(result['name_column'], 'N/A')}")
    return "\n".join(lines)


@mcp.tool(name="gta_mnt_create_state_act")
async def create_state_act(params: CreateStateActInput) -> str:
    """Create a new state act (measure) in the GTA database.

    Always creates with status_id=1 (In progress). Never creates in publishable or review state.
    Also creates source URL entry and links it to the state act.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.create_state_act, 
        title=params.title,
        description=params.description,
        source_url=params.source_url,
        is_source_official=params.is_source_official,
        date_announced=params.date_announced,
        evaluation_id=params.evaluation_id,
        source_citation=params.source_citation,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — State Act\n\nSQL:\n```sql\n{result['sql']}\n```\n\nParams: {result['params']}\n\nRollback: `{result['rollback']}`"

    if result['success']:
        return f"✅ {result['message']}\n\nState Act ID: {result['state_act_id']}\nSource ID: {result['source_id']}\nStatus: {result['status_id']} (Step 1 review)\nAuthor: Sancho Claudito (user_id={SANCHO_AUTHOR_ID})"
    else:
        return f"❌ {result['message']}"


@mcp.tool(name="gta_mnt_create_intervention")
async def create_intervention(params: CreateInterventionInput) -> str:
    """Create a new intervention under an existing state act.

    Requires a state_act_id from gta_mnt_create_state_act.
    Use gta_mnt_lookup to find IDs for intervention_type, chapter, subchapter, etc.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.create_intervention, 
        state_act_id=params.state_act_id,
        description=params.description,
        intervention_type_id=params.intervention_type_id,
        chapter_id=params.chapter_id,
        subchapter_id=params.subchapter_id,
        gta_evaluation_id=params.gta_evaluation_id,
        affected_flow_id=params.affected_flow_id,
        eligible_firm_id=params.eligible_firm_id,
        implementation_level_id=params.implementation_level_id,
        intervention_area_id=params.intervention_area_id,
        date_implemented=params.date_implemented,
        date_announced=params.date_announced,
        title=params.title,
        announced_as_temporary=params.announced_as_temporary,
        is_horizontal=params.is_horizontal,
        aj_type=params.aj_type,
        dm_type=params.dm_type,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Intervention\n\nSQL:\n```sql\n{result['sql']}\n```\n\nParams: {result['params']}\n\nRollback: `{result['rollback']}`"

    if result['success']:
        return f"✅ {result['message']}\n\nIntervention ID: {result['intervention_id']}"
    else:
        return f"❌ {result.get('message', result.get('error', 'Unknown error'))}"


@mcp.tool(name="gta_mnt_add_ij")
async def add_ij(params: AddIJInput) -> str:
    """Add implementing jurisdiction to an intervention.

    Use gta_mnt_lookup with table='jurisdiction' to find the jurisdiction_id.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_ij, 
        intervention_id=params.intervention_id,
        jurisdiction_id=params.jurisdiction_id,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add IJ\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_product")
async def add_product(params: AddProductInput) -> str:
    """Add affected product (HS6) to an intervention.

    Use gta_mnt_lookup with table='product' to find the product_id from the HS6
    code description. If the source publishes a longer HS code (HS8/10/12/14),
    use gta_mnt_add_product_level instead — the back-end aggregates upward.

    Pass is_investigated_only=True only for trade-defence cases (anti-dumping,
    anti-subsidy, safeguard) where the product is under investigation only.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_product,
        intervention_id=params.intervention_id,
        product_id=params.product_id,
        prior_level=params.prior_level,
        new_level=params.new_level,
        unit_id=params.unit_id,
        date_implemented=params.date_implemented,
        date_removed=params.date_removed,
        is_investigated_only=params.is_investigated_only,
        dry_run=params.dry_run,
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Product\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_product_level")
async def add_product_level(params: AddProductLevelInput) -> str:
    """Add a tariff-line row at HS8/10/12/14 to an intervention.

    Use this when the source publishes HS codes longer than 6 digits. The back-
    end aggregates finer rows up to HS6, so analysts only insert at the source
    level — never insert the same intervention at multiple HS granularities.

    HS code formatting: pass the source's HS code as a string in any common
    format ('0102.10.20', '0102-10-20', '0102 10 20', or '01021020'). The tool
    strips non-digits and validates the length matches `level`.

    Leading zeros (HS chapters 01–09): the cleaned 8/10/12/14-char string is
    validated on length, then converted to an integer for the master-table
    lookup. The master tables store HS codes as integers, so leading zeros
    are dropped consistently on both sides — the lookup still works.

    For level 8 and 10 the schema is richer and `action_id` is REQUIRED
    (look up with gta_mnt_lookup table='action'; common values: 1 = U.S. HTS
    Tariff Schedule). For level 12 and 14 (log tables) the schema is leaner.

    Always writes type='N'; A/A_MIN/A_MAX are aggregation artifacts produced
    by the back-end, never set by analyst inserts.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_product_level,
        intervention_id=params.intervention_id,
        level=params.level,
        hs_code=params.hs_code,
        jurisdiction_id=params.jurisdiction_id,
        prior_value=params.prior_value,
        new_value=params.new_value,
        unit_id=params.unit_id,
        date_implemented=params.date_implemented,
        date_removed=params.date_removed,
        is_investigated_only=params.is_investigated_only,
        is_in_original=params.is_in_original,
        is_positively_affected=params.is_positively_affected,
        is_tariff_line_official=params.is_tariff_line_official,
        is_tariff_peak=params.is_tariff_peak,
        action_id=params.action_id,
        applicability_reason_id=params.applicability_reason_id,
        verification_status_id=params.verification_status_id,
        is_completely_captured=params.is_completely_captured,
        dry_run=params.dry_run,
    )

    if result.get('dry_run'):
        return (f"🔍 DRY RUN — Add Product Level{params.level}\n\n"
                f"Cleaned HS code: `{result['cleaned_hs_code']}`\n"
                f"Master composite (product_level{params.level}_id): `{result['master_id']}`\n"
                f"SQL: `{result['sql']}`\nParams: {result['params']}")

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_sector")
async def add_sector(params: AddSectorInput) -> str:
    """Add affected sector to an intervention.

    Use gta_mnt_lookup with table='sector' to find the sector_id. Pass
    is_investigated_only=True only for trade-defence cases where the sector
    is under investigation only.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_sector,
        intervention_id=params.intervention_id,
        sector_id=params.sector_id,
        sector_type=params.sector_type,
        is_investigated_only=params.is_investigated_only,
        dry_run=params.dry_run,
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Sector\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_rationale")
async def add_rationale(params: AddRationaleInput) -> str:
    """Add rationale/motive tag to an intervention.

    Use gta_mnt_lookup with table='rationale' to find the rationale_id.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_rationale, 
        intervention_id=params.intervention_id,
        rationale_id=params.rationale_id,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Rationale\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_firm")
async def add_firm(params: AddFirmInput) -> str:
    """Add a firm to an intervention. Creates firm in mtz_firm_log if it doesn't already exist.

    Firm roles: 1=beneficiary, 2=target, 3=acting agency, 4=petitioner, 5=exempted, 6=intermediary.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_firm, 
        intervention_id=params.intervention_id,
        firm_name=params.firm_name,
        role_id=params.role_id,
        jurisdiction_id=params.jurisdiction_id,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Firm\n\nSQL: {result['sql']}\nExisting firm: {result['existing_firm']}"

    if result['success']:
        created = " (newly created)" if result.get('created_new') else " (existing)"
        return f"✅ {result['message']}{created}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_source")
async def add_source_tool(params: AddSourceInput) -> str:
    """Add a source URL to a state act. Creates source in api_source_list if URL is new.

    Note: gta_mnt_create_state_act already adds the primary source. Use this for additional sources.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_source, 
        state_act_id=params.state_act_id,
        source_url=params.source_url,
        source_citation=params.source_citation,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Source\n\nSQL: {result['sql']}"

    if result['success']:
        return f"✅ {result['message']}\n\nSource ID: {result['source_id']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_queue_recalculation")
async def queue_recalculation(params: QueueRecalculationInput) -> str:
    """Queue an intervention for AJ/DM auto-population from COMTRADE trade data.

    Only needed for inferred AJ/DM types (aj_type=1, dm_type=1).
    The population_procedure runs asynchronously and populates api_intervention_aj and api_intervention_dm.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.queue_recalculation, 
        intervention_id=params.intervention_id,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Queue Recalculation\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_level")
async def add_level(params: AddLevelInput) -> str:
    """Add a level row (prior/new level with unit) to an intervention.

    Use gta_mnt_lookup with table='unit' or table='level_type' to find IDs.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_level, 
        intervention_id=params.intervention_id,
        prior_level=params.prior_level,
        new_level=params.new_level,
        unit_id=params.unit_id,
        level_type_id=params.level_type_id,
        tariff_peak=params.tariff_peak,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Level\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_motive_quote")
async def add_motive_quote(params: AddMotiveQuoteInput) -> str:
    """Add a stated motive quote to a state act (gta_stated_motive_log).

    Stores the actual quoted text from the source that justifies the rationale/motive tags.
    Use after gta_mnt_add_rationale to provide the supporting quote.
    """
    db_client = get_db_client()
    result = await asyncio.to_thread(db_client.add_motive_quote, 
        state_act_id=params.state_act_id,
        motive_quote=params.motive_quote,
        source_url=params.source_url,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Motive Quote\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


class GuessHSCodesInput(_StrictInput):
    """Input for AI-powered HS code guessing via Bastiat API."""
    product_description: str = Field(
        ...,
        description="Natural language description of the product or goods (e.g. 'satellite imaging equipment', 'steel coils', 'lithium-ion batteries')"
    )
    target_hs_levels: Optional[List[int]] = Field(
        default=None,
        description="HS digit levels to return (e.g. [2, 4, 6]). Default: all levels."
    )
    hint_codes: Optional[List[str]] = Field(
        default=None,
        description="Optional HS codes to guide the search (e.g. ['8802', '8806'])"
    )


@mcp.tool(name="gta_mnt_guess_hs_codes")
async def guess_hs_codes(params: GuessHSCodesInput) -> str:
    """AI-powered HS code identification from natural language product descriptions.

    Uses the Bastiat API (semantic AI model) to match product descriptions to HS codes.
    Unlike gta_mnt_lookup(table='product'), which does substring matching on ~7K codes,
    this tool understands product semantics (e.g. 'satellite imaging equipment' → HS 880260).

    Use this when:
    - You have a natural language product description (not an HS code number)
    - Substring lookup returned no/poor results
    - You need to identify HS codes for a new GTA entry

    After getting results, use gta_mnt_lookup(table='product', query='<hs_code>') to get
    the database product_id needed for gta_mnt_add_product.
    """
    api_key = os.getenv("GTA_API_KEY")
    if not api_key:
        raise ToolError(
            "GTA_API_KEY environment variable not set. "
            "Cannot access Bastiat API for HS code inference."
        )

    try:
        client = BastiatAPIClient(api_key=api_key)
        result = await client.guess_hs_codes(
            article_text=params.product_description,
            target_hs_levels=params.target_hs_levels,
            initial_hs_codes=params.hint_codes,
        )
        return format_guessed_hs_codes(result)
    except httpx.HTTPStatusError as e:
        raise ToolError(
            f"Bastiat API returned {e.response.status_code}: "
            f"{e.response.text[:200]}"
        ) from e
    except httpx.TimeoutException as e:
        raise ToolError(
            "Bastiat API timed out after 90s. "
            "Try a shorter product_description."
        ) from e


class ScrapeUrlInput(_StrictInput):
    """Input for fetching text content from an arbitrary URL via Bastiat scrape_urls."""
    url: str = Field(
        ...,
        description="URL to fetch. Must include scheme (http:// or https://)."
    )
    agent: bool = Field(
        default=False,
        description=(
            "When true, run the BastiatAgentScraper (LLM-driven browser) to "
            "navigate the page, discover content URLs, and fetch their text. "
            "Use for index/listing pages or sites where the seed URL is not "
            "the direct content. Slower (minutes per URL). Default false."
        ),
    )
    instructions: str = Field(
        default="",
        description=(
            "Optional note_for_agent (agent mode only). Tells the LLM how to "
            "navigate this specific site, e.g. 'Click the L (Legislation) tab.'."
        ),
    )
    cleaning_mode: str = Field(
        default="no_cleaning",
        description=(
            "HTML cleaning mode: 'no_cleaning' (default, raw HTML), "
            "'readability', 'docling', 'density', 'hybrid'. PDF/DOCX extraction "
            "runs server-side regardless."
        ),
    )


@mcp.tool(name="gta_mnt_scrape_url")
async def scrape_url_tool(params: ScrapeUrlInput) -> str:
    """Fetch text content from a URL via the Bastiat scrape_urls endpoint.

    Uses Scrapling tiered fetcher (curl_cffi → Playwright → Camoufox stealth),
    handles PDF/DOCX/ZIP extraction server-side, and can optionally run an
    LLM-driven browser agent for sites that require navigation.

    Use when:
    - You need to fetch arbitrary URLs (not DB-linked sources)
    - WebFetch fails due to Cloudflare, JS rendering, or anti-bot blocks
    - You need PDF/DOCX text extraction

    For DB-linked review sources, prefer gta_mnt_get_source (S3 priority).
    """
    api_key = os.getenv("GTA_API_KEY")
    if not api_key:
        raise ToolError(
            "GTA_API_KEY environment variable not set. "
            "Cannot access Bastiat scrape_urls endpoint."
        )

    try:
        client = BastiatAPIClient(api_key=api_key)
        result = await client.scrape_url(
            url=params.url,
            agent=params.agent,
            instructions=params.instructions,
            cleaning_mode=params.cleaning_mode,
        )
    except TimeoutError as e:
        raise ToolError(str(e)) from e
    except RuntimeError as e:
        raise ToolError(f"Scrape failed: {e}") from e
    except httpx.HTTPStatusError as e:
        raise ToolError(
            f"Bastiat API returned {e.response.status_code}: "
            f"{e.response.text[:200]}"
        ) from e

    if result["mode"] == "static":
        text = result.get("text") or ""
        return (
            f"# Scraped content\n\n"
            f"**URL:** {result['url']}\n"
            f"**Mode:** static (cleaning_mode={params.cleaning_mode})\n"
            f"**Length:** {len(text)} chars\n\n"
            f"---\n\n{text}"
        )
    else:
        discovered = result.get("discovered_urls", [])
        content = result.get("content", {})
        outcome = result.get("outcome")
        if not discovered:
            err = result.get("error")
            return (
                f"# Scrape (agent mode) — no URLs discovered\n\n"
                f"**Seed URL:** {result.get('seed_url')}\n"
                f"**Outcome:** {outcome}\n"
                f"**Iterations:** {result.get('iterations')}\n"
                + (f"**Error:** {err}\n" if err else "")
            )
        sections = [
            f"# Scrape (agent mode)",
            f"",
            f"**Seed URL:** {result.get('seed_url')}",
            f"**Outcome:** {outcome}",
            f"**Iterations:** {result.get('iterations')}",
            f"**Duration:** {result.get('duration')}s",
            f"**Discovered URLs:** {len(discovered)}",
            f"",
            f"---",
        ]
        for u in discovered:
            text = content.get(u, "")
            sections.append(f"\n## {u}\n\n**Length:** {len(text)} chars\n\n{text}")
        return "\n".join(sections)


@mcp.tool(name="gta_mnt_find_duplicates")
async def find_duplicates(params: FindDuplicatesInput) -> str:
    """Find candidate duplicate state acts via deterministic SQL vectors plus optional semantic ranking.

    Vectors run (each skipped if its inputs are missing):

    - **A — URL**: state acts that share a normalised host+path with any input source URL.
    - **B — DECREE**: regex-extracted decree/regulation/notification numbers from the
      title (e.g. "MP 1340", "VR 2036/2026", "BGBl I Nr. 96/2018"), LIKE-matched within
      the same implementing jurisdiction.
    - **C — TYPE+DATE**: same jurisdiction, same `date_announced`, same `intervention_type_id`.
    - **D — HS+DATE**: same jurisdiction, `date_announced` within ±`date_window_days`,
      ≥1 shared HS code.
    - **E — POOL**: wide net (jurisdiction + date window) — collected as a candidate pool.
    - **G — SEMANTIC**: cosine similarity over title+description via the GTA RAG, scoped
      to the Vector E pool. Skipped if `RAG_BASE_URL`/`RAG_API_KEY` not set, or if
      `semantic_search=False`. Currently indexes published only — drafts are pending BT-263.

    Decision rule for the caller:

    - Vectors A or B firing → **DUPLICATE** (deterministic).
    - Vector C firing → **DUPLICATE** (near-deterministic).
    - Vector D firing or G score ≥ 0.85 → **DUPLICATE**.
    - G score 0.70–0.85 → **CONDITIONAL** (Slack-escalate per JCC-819 plan).

    Inputs may either provide `state_act_id` (canonical fields read from the DB) or
    pass identity fields directly (jurisdiction_ids, date_announced, etc.) — useful
    when checking a draft before insertion.
    """
    db_client = get_db_client()
    sql_result = await asyncio.to_thread(
        db_client.find_duplicates,
        state_act_id=params.state_act_id,
        jurisdiction_ids=params.jurisdiction_ids,
        date_announced=params.date_announced,
        intervention_type_ids=params.intervention_type_ids,
        hs_codes=params.hs_codes,
        source_urls=params.source_urls,
        title=params.title,
        description=params.description,
        exclude_state_act_ids=params.exclude_state_act_ids,
        date_window_days=params.date_window_days,
        include_statuses=params.include_statuses,
        limit=params.limit,
    )

    candidates = sql_result['candidates']
    pool_ids = sql_result['pool_intervention_ids']
    semantic_skipped_reason = None
    semantic_hits: list[dict] = []

    if params.semantic_search and (sql_result['self_title'] or sql_result['self_description']):
        query_text = ' '.join(filter(None, [sql_result['self_title'], (sql_result['self_description'] or '')[:1500]])).strip()
        if query_text:
            rag = await semantic_search_via_rag(
                query=query_text,
                intervention_ids=pool_ids if pool_ids else None,
                limit=20,
            )
            if rag.get('skipped'):
                semantic_skipped_reason = rag.get('reason')
            else:
                # Merge RAG hits into candidate set, mapping intervention_id → state_act_id
                rag_results = rag.get('results', []) or []
                # Build interv→state_act mapping for hits we don't already have
                hit_iids = [r['intervention_id'] for r in rag_results if r.get('score', 0) >= params.semantic_threshold_review]
                if hit_iids:
                    iid_to_sa = {}
                    conn = db_client._get_connection()
                    cur = conn.cursor()
                    placeholders = ','.join(['%s'] * len(hit_iids))
                    cur.execute(
                        f'''SELECT i.intervention_id, sa.state_act_id, sa.title, sa.status_id, sa.date_announced
                            FROM api_intervention_log i
                            JOIN api_state_act_log sa ON sa.state_act_id = i.state_act_id
                            WHERE i.intervention_id IN ({placeholders})''',
                        hit_iids,
                    )
                    for row in cur.fetchall():
                        iid_to_sa[row['intervention_id']] = row
                    excluded = set(sql_result['inputs_resolved'].get('exclude_state_act_ids') or [])
                    for r in rag_results:
                        if r.get('score', 0) < params.semantic_threshold_review:
                            continue
                        sa_row = iid_to_sa.get(r['intervention_id'])
                        if not sa_row:
                            continue
                        if sa_row['state_act_id'] in excluded:
                            continue
                        semantic_hits.append({
                            'state_act_id': sa_row['state_act_id'],
                            'title': sa_row.get('title'),
                            'status_id': sa_row.get('status_id'),
                            'date_announced': (
                                sa_row['date_announced'].strftime('%Y-%m-%d')
                                if sa_row.get('date_announced') and hasattr(sa_row['date_announced'], 'strftime')
                                else sa_row.get('date_announced')
                            ),
                            'cosine_score': round(float(r['score']), 4),
                            'rag_intervention_id': r['intervention_id'],
                            'rag_title': r.get('title'),
                            'rag_blurb': (r.get('blurb') or '')[:200],
                        })
                    # Annotate matching SQL candidates with their best RAG score, and
                    # add new SEMANTIC-only hits.
                    cand_by_id = {c['state_act_id']: c for c in candidates}
                    for hit in semantic_hits:
                        sa_id = hit['state_act_id']
                        if sa_id in cand_by_id:
                            cand = cand_by_id[sa_id]
                            existing_score = cand.get('cosine_score') or 0
                            if hit['cosine_score'] > existing_score:
                                cand['cosine_score'] = hit['cosine_score']
                            if 'SEMANTIC' not in cand['match_vectors']:
                                cand['match_vectors'].append('SEMANTIC')
                        else:
                            candidates.append({
                                'state_act_id': sa_id,
                                'title': hit['title'],
                                'status_id': hit['status_id'],
                                'date_announced': hit['date_announced'],
                                'match_vectors': ['SEMANTIC'],
                                'shared_urls': [],
                                'shared_decree_tokens': [],
                                'shared_intervention_types': [],
                                'shared_hs_codes': [],
                                'cosine_score': hit['cosine_score'],
                            })

    # Re-rank: any deterministic vector first, then by vector count, then cosine
    DETERMINISTIC = {'URL', 'DECREE', 'TYPE+DATE'}
    def _rank_key(c):
        is_det = bool(set(c['match_vectors']) & DETERMINISTIC)
        return (
            -1 if is_det else 0,
            -len(c['match_vectors']),
            -(c.get('cosine_score') or 0),
        )
    candidates = sorted(candidates, key=_rank_key)[:params.limit]

    # Format output
    vectors_run = list(sql_result['vectors_run'])
    if params.semantic_search:
        vectors_run.append('SEMANTIC' if not semantic_skipped_reason else f'SEMANTIC (skipped: {semantic_skipped_reason})')

    lines = ['# Duplicate detection results\n']
    lines.append(f"**Vectors run:** {', '.join(vectors_run) or '(none — no inputs given)'}")
    lines.append(f"**Candidate pool size (Vector E):** {len(pool_ids)} interventions")
    if semantic_skipped_reason:
        lines.append(f"**Note:** {semantic_skipped_reason}")
    lines.append(f"**Candidates found:** {len(candidates)}\n")

    if not candidates:
        lines.append('No duplicate candidates surfaced. Proceeding is safe per these vectors.')
    else:
        # Verdict suggestion
        det_hit = any(set(c['match_vectors']) & DETERMINISTIC for c in candidates)
        strong_semantic = any((c.get('cosine_score') or 0) >= 0.85 for c in candidates)
        if det_hit:
            lines.append('## Suggested verdict: **DUPLICATE** (deterministic vector hit)\n')
        elif strong_semantic:
            lines.append('## Suggested verdict: **DUPLICATE** (semantic similarity ≥ 0.85)\n')
        else:
            lines.append('## Suggested verdict: **CONDITIONAL** — review candidates below; consider Slack escalation\n')

        for i, c in enumerate(candidates, 1):
            lines.append(f"### {i}. SA {c['state_act_id']} — {c.get('title', '?')}")
            score_str = f", cosine={c['cosine_score']:.3f}" if c.get('cosine_score') else ''
            lines.append(f"- **Vectors:** {', '.join(c['match_vectors'])}{score_str}")
            lines.append(f"- **Status:** {c.get('status_id')} | **Announced:** {c.get('date_announced')}")
            if c.get('shared_urls'):
                lines.append(f"- **Shared URLs:** {len(c['shared_urls'])} — {c['shared_urls'][0]}{'…' if len(c['shared_urls']) > 1 else ''}")
            if c.get('shared_decree_tokens'):
                lines.append(f"- **Decree token match:** {', '.join(c['shared_decree_tokens'])}")
            if c.get('shared_intervention_types'):
                lines.append(f"- **Shared intervention types:** {c['shared_intervention_types']}")
            if c.get('shared_hs_codes'):
                lines.append(f"- **Shared HS codes:** {', '.join(c['shared_hs_codes'][:5])}{'…' if len(c['shared_hs_codes']) > 5 else ''}")
            lines.append(f"- Admin URL: https://ric.globaltradealert.org/gta-admin-dashboard/measures/{c['state_act_id']}/edit\n")

    return '\n'.join(lines)


# ========================================================================
# MCP Resources — agent-facing reference docs
# ========================================================================

from .resources_loader import load_resource as _load_resource  # noqa: E402


@mcp.resource(
    "gta-mnt://review-criteria",
    name="Sancho Claudino Review Criteria",
    description="Minimum field-surface for a Step-1 review, criticality rubric, and verdict→tool-call mapping.",
    mime_type="text/markdown",
)
def _res_review_criteria() -> str:
    return _load_resource("review_criteria")


@mcp.resource(
    "gta-mnt://status-id-decision-tree",
    name="Status ID Decision Tree",
    description="Which of the five valid status IDs (1/2/3/6/19) to use, with flow diagrams for reviewer and author paths.",
    mime_type="text/markdown",
)
def _res_status_tree() -> str:
    return _load_resource("status_id_decision_tree")


@mcp.resource(
    "gta-mnt://comment-templates",
    name="Comment Template Catalogue",
    description="Canonical issue / verification / review-complete comment structures, and which formatter helper to call.",
    mime_type="text/markdown",
)
def _res_comment_templates() -> str:
    return _load_resource("comment_templates")


@mcp.resource(
    "gta-mnt://framework-ids",
    name="Framework IDs",
    description="The two framework IDs (495 Sancho Claudino review, 500 Sancho Claudito reported) — when to attach each.",
    mime_type="text/markdown",
)
def _res_framework_ids() -> str:
    return _load_resource("framework_ids")


@mcp.resource(
    "gta-mnt://source-extraction-notes",
    name="Source Extraction Notes",
    description="S3 / URL / PDF / HTML extraction gotchas for gta_mnt_get_source. Read before chasing source-mismatch bugs.",
    mime_type="text/markdown",
)
def _res_source_extraction() -> str:
    return _load_resource("source_extraction_notes")


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
