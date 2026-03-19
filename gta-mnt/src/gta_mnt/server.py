"""MCP server for GTA monitoring, review, and entry creation.

Two automated users with strictly separated roles:
- Sancho Claudino (9900): REVIEWER — comments, status changes, framework tags
- Sancho Claudito (9901): AUTHOR — creates state acts, interventions, relationships

These must never be mixed. A reviewer must not appear as entry author.
"""

import os
import sys
from typing import Optional, List
import httpx
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

from .api import GTADatabaseClient, BastiatAPIClient
from .source_fetcher import SourceFetcher
from .constants import SANCHO_USER_ID, SANCHO_AUTHOR_ID, SANCHO_FRAMEWORK_ID
from .formatters import (
    format_step1_queue,
    format_measure_detail,
    format_source_result,
    format_templates,
    format_guessed_hs_codes
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


class ListStep2QueueInput(BaseModel):
    """Input for listing Step 2 review queue."""
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


class ListQueueByStatusInput(BaseModel):
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
    new_status_id: int = Field(..., description="Status ID (2=Step1, 3=Publishable, 6=Under revision, 19=Step2)")
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


# ========================================================================
# Entry Creation Input Models
# ========================================================================

class LookupInput(BaseModel):
    """Input for looking up reference table values."""
    table: str = Field(..., description="Table short name: jurisdiction, product, sector, rationale, unit, firm, intervention_type, mast_chapter, mast_subchapter, evaluation, affected_flow, eligible_firm, implementation_level, intervention_area, firm_role, level_type")
    query: str = Field(..., description="Search string (matched with LIKE %%query%%)")
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")


class CreateStateActInput(BaseModel):
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


class CreateInterventionInput(BaseModel):
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
    aj_type: int = Field(default=1, description="1=inferred, 2=targeted, 3=excluded, 4=incidental")
    dm_type: int = Field(default=1, description="1=inferred, 2=targeted, 3=excluded, 4=incidental")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddIJInput(BaseModel):
    """Input for adding implementing jurisdiction to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    jurisdiction_id: int = Field(..., description="FK to api_jurisdiction_list (look up via gta_mnt_lookup)")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddProductInput(BaseModel):
    """Input for adding affected product to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    product_id: int = Field(..., description="FK to api_product_list (look up HS code via gta_mnt_lookup)")
    prior_level: Optional[str] = Field(default=None, description="Prior tariff/level value for this product (e.g. '5.0')")
    new_level: Optional[str] = Field(default=None, description="New tariff/level value for this product (e.g. '25.0')")
    unit_id: Optional[int] = Field(default=None, description="FK to api_unit_list (look up via gta_mnt_lookup table='unit')")
    date_implemented: Optional[str] = Field(default=None, description="Per-product implementation date (YYYY-MM-DD)")
    date_removed: Optional[str] = Field(default=None, description="Per-product removal date (YYYY-MM-DD)")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddSectorInput(BaseModel):
    """Input for adding affected sector to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    sector_id: int = Field(..., description="FK to api_sector_list")
    sector_type: str = Field(default='N', description="'N'=normal, 'A'=additional, 'P'=primary")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddRationaleInput(BaseModel):
    """Input for adding rationale/motive to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    rationale_id: int = Field(..., description="FK to api_rationale_list")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddFirmInput(BaseModel):
    """Input for adding a firm to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    firm_name: str = Field(..., description="Firm name (looked up or created in mtz_firm_log)")
    role_id: int = Field(..., description="FK to mtz_firm_role: 1=beneficiary, 2=target, 3=acting agency, 4=petitioner, 5=exempted, 6=intermediary")
    jurisdiction_id: Optional[int] = Field(default=None, description="Optional: firm's home jurisdiction ID")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddSourceInput(BaseModel):
    """Input for adding a source URL to a state act."""
    state_act_id: int = Field(..., description="FK to api_state_act_log")
    source_url: str = Field(..., description="Source URL")
    source_citation: Optional[str] = Field(default=None, description="Full GTA citation string (e.g. 'Author (Date). TITLE. Publisher (Retrieved): URL'). Stored in api_state_act_source_log_new for admin dashboard display. If omitted, source_url is used.")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class QueueRecalculationInput(BaseModel):
    """Input for queuing AJ/DM recalculation."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddMotiveQuoteInput(BaseModel):
    """Input for adding a stated motive quote to a state act."""
    state_act_id: int = Field(..., description="FK to api_state_act_log")
    motive_quote: str = Field(..., description="The quoted text from the source justifying the motive tag")
    source_url: Optional[str] = Field(default=None, description="URL where the quote was found")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


class AddLevelInput(BaseModel):
    """Input for adding a level row to an intervention."""
    intervention_id: int = Field(..., description="FK to api_intervention_log")
    prior_level: Optional[str] = Field(default=None, description="Prior level value")
    new_level: Optional[str] = Field(default=None, description="New level value")
    unit_id: Optional[int] = Field(default=None, description="FK to api_unit_list")
    level_type_id: Optional[int] = Field(default=None, description="FK to api_level_type_list")
    tariff_peak: Optional[int] = Field(default=None, description="Tariff peak indicator")
    dry_run: bool = Field(default=False, description="If True, return SQL without executing")


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


@mcp.tool(name="gta_mnt_list_step2_queue")
async def list_step2_queue(params: ListStep2QueueInput) -> str:
    """List measures awaiting Step 2 review (status 19), ordered by status_time DESC.

    Uses api_state_act_status_log for accurate ordering.
    """
    db_client = get_db_client()
    data = await db_client.list_step1_queue(
        status_id=19,
        limit=params.limit,
        offset=params.offset,
        implementing_jurisdictions=params.implementing_jurisdictions,
        date_entered_review_gte=params.date_entered_review_gte
    )
    return format_step1_queue(data, queue_label="Step 2")


STATUS_LABELS = {1: "In Progress", 2: "Step 1", 3: "Publishable", 6: "Under Revision", 19: "Step 2"}


@mcp.tool(name="gta_mnt_list_queue_by_status")
async def list_queue_by_status(params: ListQueueByStatusInput) -> str:
    """List measures by any status ID. Useful for checking unpublished pipeline entries.

    Status IDs: 1=In progress, 2=Step 1 review, 3=Publishable, 6=Under revision, 19=Step 2 review.
    """
    db_client = get_db_client()
    data = await db_client.list_step1_queue(
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
        return f"✅ {result['message']}\n\nFramework ID: {result['framework_id']}"
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


# ========================================================================
# Entry Creation Tools
# ========================================================================

@mcp.tool(name="gta_mnt_lookup")
async def lookup(params: LookupInput) -> str:
    """Look up IDs in GTA reference tables by search string.

    Supports: jurisdiction, product, sector, rationale, unit, firm, intervention_type,
    mast_chapter, mast_subchapter, evaluation, affected_flow, eligible_firm,
    implementation_level, intervention_area, firm_role, level_type.
    """
    db_client = get_db_client()
    result = await db_client.lookup(
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
    result = await db_client.create_state_act(
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
    result = await db_client.create_intervention(
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
    result = await db_client.add_ij(
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
    """Add affected product to an intervention.

    Use gta_mnt_lookup with table='product' to find the product_id from HS code description.
    """
    db_client = get_db_client()
    result = await db_client.add_product(
        intervention_id=params.intervention_id,
        product_id=params.product_id,
        prior_level=params.prior_level,
        new_level=params.new_level,
        unit_id=params.unit_id,
        date_implemented=params.date_implemented,
        date_removed=params.date_removed,
        dry_run=params.dry_run
    )

    if result.get('dry_run'):
        return f"🔍 DRY RUN — Add Product\n\nSQL: `{result['sql']}`\nParams: {result['params']}"

    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result.get('error', 'Unknown error')}"


@mcp.tool(name="gta_mnt_add_sector")
async def add_sector(params: AddSectorInput) -> str:
    """Add affected sector to an intervention.

    Use gta_mnt_lookup with table='sector' to find the sector_id.
    """
    db_client = get_db_client()
    result = await db_client.add_sector(
        intervention_id=params.intervention_id,
        sector_id=params.sector_id,
        sector_type=params.sector_type,
        dry_run=params.dry_run
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
    result = await db_client.add_rationale(
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
    result = await db_client.add_firm(
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
    result = await db_client.add_source(
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
    result = await db_client.queue_recalculation(
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
    result = await db_client.add_level(
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
    result = await db_client.add_motive_quote(
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


class GuessHSCodesInput(BaseModel):
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
        return "❌ GTA_API_KEY environment variable not set. Cannot access Bastiat API."

    try:
        client = BastiatAPIClient(api_key=api_key)
        result = await client.guess_hs_codes(
            article_text=params.product_description,
            target_hs_levels=params.target_hs_levels,
            initial_hs_codes=params.hint_codes,
        )
        return format_guessed_hs_codes(result)
    except httpx.HTTPStatusError as e:
        return f"❌ Bastiat API error: {e.response.status_code} — {e.response.text[:200]}"
    except httpx.TimeoutException:
        return "❌ Bastiat API timeout (90s). Try a shorter product description."
    except Exception as e:
        return f"❌ Error guessing HS codes: {str(e)}"


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
