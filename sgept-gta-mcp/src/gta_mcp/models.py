"""Pydantic models for GTA MCP server input validation."""

from enum import Enum
from typing import Literal, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# Detail level controls how much data is returned per intervention
DetailLevel = Literal["overview", "standard", "full"]


# Valid count_by dimension values for the GTA counts endpoint
CountByDimension = Literal[
    "affected",
    "affected_group",
    "implementer",
    "implementer_group",
    "mast_chapter",
    "intervention_type",
    "implementation_level",
    "eligible_firm",
    "gta_evaluation",
    "affected_flow",
    "date_implemented_year",
    "date_implemented_month",
    "date_removed_year",
    "date_removed_month",
    "date_published_year",
    "date_published_month",
    "date_announced_year",
    "date_announced_month",
    "product",
    "product_level2",
    "product_group",
    "sector",
    "sector_level2",
    "sector_group",
    "intervention_id",
    "state_act_id",
]


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class GTASearchInput(BaseModel):
    """Input model for searching GTA interventions."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="List of implementing jurisdiction ISO codes (e.g., ['USA', 'CHN', 'DEU']). "
                   "Filter interventions by countries that implemented the measure. "
                   "See gta://reference/jurisdictions for complete list."
    )

    affected_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="List of affected jurisdiction ISO codes (e.g., ['USA', 'CHN', 'DEU']). "
                   "Filter interventions by countries affected by the measure. "
                   "See gta://reference/jurisdictions for complete list."
    )
    
    affected_products: Optional[List[int]] = Field(
        default=None,
        description="List of HS product codes (6-digit integers, e.g., [292149, 292229]). "
                   "Filter interventions affecting specific products. "
                   "Note: HS codes only cover goods, not services. Use affected_sectors for services."
    )

    affected_sectors: Optional[List[str | int]] = Field(
        default=None,
        description=(
            "Filter by CPC sector codes or names for broader product coverage including services. "
            "Use for services queries (ID >= 500) or broad categories. "
            "Accepts IDs ([711]), names (['Financial services']), or mixed with fuzzy matching. "
            "See gta://guide/cpc-vs-hs for guidance and gta://reference/sectors-list for all sectors."
        )
    )

    intervention_types: Optional[List[str]] = Field(
        default=None,
        description="List of intervention types (e.g., ['Import tariff', 'Export subsidy', 'State aid']). "
                   "Filter by type of trade measure. "
                   "See gta://reference/intervention-types for complete list."
    )

    mast_chapters: Optional[List[str]] = Field(
        default=None,
        description=(
            "Filter by UN MAST chapter classifications (A-P) - broad categories of non-tariff measures "
            "from import quotas to subsidies, localization requirements, investment actions, and beyond. "
            "Use mast_chapters for generic queries (e.g., 'all subsidies' → ['L']), "
            "intervention_types for specific measures. "
            "Accepts letters (A-P), IDs (1-20), or special categories. "
            "See gta://reference/mast-chapters for complete taxonomy and usage guide."
        )
    )

    gta_evaluation: Optional[List[str]] = Field(
        default=None,
        description="GTA evaluation colors: 'Red' (harmful), 'Amber' (likely harmful), or 'Green' (liberalising). "
                   "Filter by impact assessment. Use 'Harmful' as shorthand for Red+Amber."
    )

    eligible_firms: Optional[List[str | int]] = Field(
        default=None,
        description=(
            "Filter by firm types eligible for the intervention (all, SMEs, firm-specific, state-controlled, sector-specific, location-specific). "
            "Use to find targeted vs universal policies or company-specific incentives. "
            "See gta://reference/eligible-firms for descriptions and examples."
        )
    )

    implementation_levels: Optional[List[str | int]] = Field(
        default=None,
        description=(
            "Filter by government level implementing the intervention (Supranational, National, Subnational, SEZ, IFI, NFI). "
            "Use for distinguishing central vs regional policies or financial institution programs. "
            "See gta://reference/implementation-levels for hierarchy and examples."
        )
    )

    date_announced_gte: Optional[str] = Field(
        default=None,
        description="Filter interventions announced on or after this date (ISO format: YYYY-MM-DD, e.g., '2024-01-01')"
    )
    
    date_announced_lte: Optional[str] = Field(
        default=None,
        description="Filter interventions announced on or before this date (ISO format: YYYY-MM-DD)"
    )
    
    date_implemented_gte: Optional[str] = Field(
        default=None,
        description="Filter interventions implemented on or after this date (ISO format: YYYY-MM-DD)"
    )
    
    date_implemented_lte: Optional[str] = Field(
        default=None,
        description="Filter interventions implemented on or before this date (ISO format: YYYY-MM-DD)"
    )

    date_modified_gte: Optional[str] = Field(
        default=None,
        description="Filter interventions modified/updated on or after this date (ISO format: YYYY-MM-DD). "
                   "Useful for monitoring: 'What changed since my last check?'"
    )

    date_modified_lte: Optional[str] = Field(
        default=None,
        description="Filter interventions modified/updated on or before this date (ISO format: YYYY-MM-DD)"
    )

    is_in_force: Optional[bool] = Field(
        default=None,
        description="Filter by whether intervention is currently in force (True) or has been removed (False)"
    )

    query: Optional[str] = Field(
        default=None,
        description=(
            "Full-text search for entity names and specific products ONLY. "
            "⚠️ CRITICAL: Use structured filters FIRST (intervention_types, jurisdictions, products, dates), "
            "then add query ONLY for named entities not captured by filters (companies: 'Tesla', 'Huawei'; "
            "programs: 'Made in China 2025'; technologies: 'AI', '5G'). "
            "DO NOT use for policy types, countries, or concepts covered by structured filters. "
            "Supports operators: | (OR), & (AND), # (wildcard). "
            "See gta://guide/query-syntax for complete syntax reference and strategy guide."
        )
    )

    limit: int = Field(
        default=50,
        description="Maximum number of interventions to return (1-1000)",
        ge=1,
        le=1000
    )

    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )

    sorting: Optional[str] = Field(
        default="-date_announced",
        description=(
            "Sort order for results. Use '-' prefix for descending. "
            "Common: '-date_announced' (newest first, recommended), 'date_announced' (oldest first), "
            "'-last_updated' (most recently modified first — useful with date_modified_gte for monitoring). "
            "Valid fields: date_announced, date_published, date_implemented, date_removed, intervention_id, last_updated. "
            "Can combine with commas."
        )
    )

    detail_level: Optional[DetailLevel] = Field(
        default=None,
        description=(
            "Controls how much data is returned per intervention. "
            "'overview': compact triage data (ID, title, type, evaluation, date, implementer) — "
            "auto-raises limit to 1000 for broad triage. "
            "'standard': analysis-ready data (adds sectors, affected countries, all dates, MAST chapter) — "
            "best for detailed work on a filtered set. "
            "'full': everything including descriptions, sources, and product-level detail — "
            "best for deep dives on specific interventions. "
            "Default behaviour: broad searches auto-select 'overview' (up to 1000 compact results); "
            "searches with specific intervention_id auto-select 'standard'. "
            "You rarely need to set this explicitly."
        )
    )

    show_keys: Optional[List[str]] = Field(
        default=None,
        description=(
            "Primary control for response width — restrict which fields are returned per record. "
            "Use this to stay within token budget. Overrides detail_level when set. "
            "Available keys: intervention_id, state_act_id, state_act_title, intervention_type, "
            "gta_evaluation, mast_chapter, implementation_level, eligible_firm, "
            "date_announced, date_implemented, date_removed, is_in_force, "
            "implementing_jurisdictions, affected_jurisdictions, affected_sectors, "
            "affected_products, intervention_description, state_act_source, "
            "intervention_url, state_act_url, is_official_source, score. "
            "Pass [\"*\"] for all fields."
        )
    )

    semantic_query: Optional[str] = Field(
        default=None,
        description=(
            "Natural-language query for semantic (vector) ranking. When set, the server first runs "
            "the structured filters to collect candidate interventions (up to the candidate ceiling), "
            "then re-ranks them by text similarity to this query. Results are returned in "
            "score-descending order and each record includes a 'score' field (0–1). "
            "Cannot be combined with 'sorting' — ordering source must be unambiguous."
        )
    )

    # Exclusion/inclusion controls (keep parameters)
    keep_affected: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified affected jurisdictions. "
            "Example: keep_affected=False excludes listed countries. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_implementer: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified implementing jurisdictions. "
            "Example: keep_implementer=False excludes G7 countries. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_intervention_types: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified intervention types. "
            "Example: keep_intervention_types=False for non-tariff measures. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_mast_chapters: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified MAST chapters. "
            "Example: keep_mast_chapters=False excludes subsidies. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_implementation_level: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified implementation levels. "
            "Example: keep_implementation_level=False for subnational only. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_eligible_firms: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified firm types. "
            "Example: keep_eligible_firms=False for universal policies. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_affected_sectors: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified CPC sectors. "
            "Example: keep_affected_sectors=False excludes agriculture. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_affected_products: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified HS products. "
            "Example: keep_affected_products=False excludes semiconductors. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_implementation_na: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) interventions with NO implementation date. "
            "Set False to require known implementation dates. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    keep_revocation_na: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) interventions with NO revocation date. "
            "Set False to show only revoked measures with known dates. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    intervention_id: Optional[List[int]] = Field(
        default=None,
        description=(
            "Filter by specific GTA intervention IDs (e.g., [138295, 138296, 138297]). "
            "Use this to retrieve multiple specific interventions in a single query. "
            "Combine with keep_intervention_id=False to exclude specific interventions instead."
        )
    )

    keep_intervention_id: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified intervention IDs. "
            "Example: keep_intervention_id=False excludes specific interventions. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    include_facets: Optional[List[str]] = Field(
        default=None,
        description=(
            "Request facet aggregations alongside results. "
            "Returns per-value counts for each requested dimension, "
            "reflecting the full filtered set (not just the returned page). "
            "Valid dimensions: gta_evaluation, implementing_country, intervention_type, "
            "mast_chapter, year."
        )
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('include_facets')
    @classmethod
    def validate_include_facets(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        valid = set(FACET_VALID_DIMENSIONS)
        unknown = [d for d in v if d not in valid]
        if unknown:
            raise ValueError(
                f"Unknown facet dimension(s): {unknown}. "
                f"Valid dimensions: {FACET_VALID_DIMENSIONS}"
            )
        return v

    @field_validator('implementing_jurisdictions', 'affected_jurisdictions')
    @classmethod
    def validate_iso_codes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure ISO codes are uppercase."""
        if v is not None:
            return [code.upper() for code in v]
        return v

    @model_validator(mode='after')
    def validate_semantic_query_sorting_conflict(self) -> 'GTASearchInput':
        if self.semantic_query is not None and self.sorting is not None:
            raise ValueError(
                "Cannot set both 'semantic_query' and 'sorting': ordering source must be unambiguous. "
                "When semantic_query is set, results are ordered by relevance score."
            )
        return self


FACET_VALID_DIMENSIONS = sorted([
    "gta_evaluation",
    "implementing_country",
    "intervention_type",
    "mast_chapter",
    "year",
])


SHOW_KEYS_AVAILABLE = [
    "intervention_id", "state_act_id", "state_act_title", "intervention_type",
    "gta_evaluation", "mast_chapter", "implementation_level", "eligible_firm",
    "date_announced", "date_implemented", "date_removed", "is_in_force",
    "implementing_jurisdictions", "affected_jurisdictions", "affected_sectors",
    "affected_products", "intervention_description", "state_act_source",
    "intervention_url", "state_act_url", "is_official_source", "score",
]

# Default candidate ceiling for unified semantic search (structured filter → semantic rank)
SEMANTIC_CANDIDATE_CEILING_DEFAULT = 1000


class GTAGetInterventionInput(BaseModel):
    """Input model for fetching one or more interventions by ID with optional field projection.

    Supply exactly one of:
    - ``intervention_id`` — fetch a single record (back-compat).
    - ``intervention_ids`` — fetch multiple records in one call.

    Use ``show_keys`` to project only the fields you need. Available fields:
    intervention_id, state_act_id, state_act_title, intervention_type,
    gta_evaluation, mast_chapter, implementation_level, eligible_firm,
    date_announced, date_implemented, date_removed, is_in_force,
    implementing_jurisdictions, affected_jurisdictions, affected_sectors,
    affected_products, intervention_description, state_act_source,
    intervention_url, state_act_url, is_official_source.
    Pass ``["*"]`` for the full record.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    intervention_id: Optional[int] = Field(
        default=None,
        description="Single GTA intervention ID (e.g., 138295). Mutually exclusive with intervention_ids.",
        gt=0
    )

    intervention_ids: Optional[List[int]] = Field(
        default=None,
        description="List of GTA intervention IDs for batch fetch (e.g., [138295, 138296]). "
                    "Mutually exclusive with intervention_id.",
    )

    show_keys: Optional[List[str]] = Field(
        default=None,
        description=(
            "Project only these fields per record. Available: "
            "intervention_id, state_act_id, state_act_title, intervention_type, "
            "gta_evaluation, mast_chapter, implementation_level, eligible_firm, "
            "date_announced, date_implemented, date_removed, is_in_force, "
            "implementing_jurisdictions, affected_jurisdictions, affected_sectors, "
            "affected_products, intervention_description, state_act_source, "
            "intervention_url, state_act_url, is_official_source. "
            "Pass [\"*\"] for all fields."
        )
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @model_validator(mode='after')
    def validate_id_fields(self) -> 'GTAGetInterventionInput':
        has_single = self.intervention_id is not None
        has_batch = self.intervention_ids is not None and len(self.intervention_ids) > 0
        if has_single and has_batch:
            raise ValueError("Provide either intervention_id or intervention_ids, not both.")
        if not has_single and not has_batch:
            raise ValueError("One of intervention_id or intervention_ids is required.")
        if has_batch:
            for id_ in self.intervention_ids:
                if id_ <= 0:
                    raise ValueError(f"All intervention_ids must be positive integers, got {id_}")
        return self


SEMANTIC_SEARCH_SHOW_KEYS_AVAILABLE = [
    "intervention_id", "title", "score", "blurb", "url", "publication_date",
]


class GTASemanticSearchInput(BaseModel):
    """Input model for semantic (vector) search over GTA intervention descriptions.

    Ranks a candidate pool by text similarity to a natural-language query.
    Use when you already have a list of intervention IDs to rank (the focused
    "rank a known ID list" path).

    For new workflows that combine structured filters with semantic ranking,
    use ``gta_search_interventions(semantic_query=...)`` instead.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    query: str = Field(
        ...,
        description="Natural-language query to rank interventions by text similarity.",
        min_length=1,
    )

    intervention_ids: Optional[List[int]] = Field(
        default=None,
        description=(
            "Restrict ranking to this specific set of intervention IDs. "
            "Omit to rank across the full corpus."
        ),
    )

    limit: int = Field(
        default=20,
        description="Maximum number of ranked interventions to return (1-100).",
        ge=1,
        le=100,
    )

    show_keys: Optional[List[str]] = Field(
        default=None,
        description=(
            "Restrict which fields are returned per record. "
            "Available keys: intervention_id, title, score, blurb, url, publication_date. "
            "Pass [\"*\"] for all fields (default)."
        ),
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class GTATickerInput(BaseModel):
    """Input model for GTA ticker updates."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter by implementing jurisdiction ISO codes"
    )
    
    intervention_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by intervention types"
    )
    
    date_modified_gte: Optional[str] = Field(
        default=None,
        description="Filter updates modified on or after this date (ISO format: YYYY-MM-DD)"
    )
    
    limit: int = Field(
        default=50,
        description="Maximum number of ticker entries to return (1-1000)",
        ge=1,
        le=1000
    )
    
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GTAImpactChainInput(BaseModel):
    """Input model for GTA impact chain queries."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    granularity: str = Field(
        ...,
        description="Granularity level: 'product' for HS product codes or 'sector' for broader sectors"
    )
    
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter by implementing jurisdiction ISO codes"
    )
    
    affected_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="Filter by affected jurisdiction ISO codes"
    )
    
    limit: int = Field(
        default=50,
        description="Maximum number of impact chains to return (1-1000)",
        ge=1,
        le=1000
    )
    
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )
    
    @field_validator('granularity')
    @classmethod
    def validate_granularity(cls, v: str) -> str:
        """Validate granularity is either 'product' or 'sector'."""
        if v.lower() not in ['product', 'sector']:
            raise ValueError("Granularity must be either 'product' or 'sector'")
        return v.lower()


class GTACountInput(BaseModel):
    """Input model for counting/aggregating GTA interventions.

    Use this to get summary statistics like annual breakdowns, counts by
    intervention type, or cross-tabulations of evaluation by year.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    count_by: List[CountByDimension] = Field(
        ...,
        description=(
            "Dimensions to group/aggregate counts by (1-3 recommended). "
            "Common dimensions: 'date_announced_year' (annual breakdown), "
            "'gta_evaluation' (harmful/liberalizing split), 'intervention_type', "
            "'implementer' (by country), 'mast_chapter' (by policy category). "
            "Multiple dimensions produce cross-tabulations."
        ),
        min_length=1,
    )

    count_variable: Literal["intervention_id", "state_act_id", "affected_products", "affected_sectors"] = Field(
        default="intervention_id",
        description=(
            "What to count: 'intervention_id' counts individual interventions (default), "
            "'state_act_id' counts unique state acts (legal instruments, which may contain "
            "multiple interventions), 'affected_products' counts distinct HS product codes affected, "
            "'affected_sectors' counts distinct CPC sectors affected."
        ),
    )

    # --- Filter parameters (same as GTASearchInput) ---

    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="List of implementing jurisdiction ISO codes (e.g., ['USA', 'CHN', 'DEU'])."
    )

    affected_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="List of affected jurisdiction ISO codes (e.g., ['USA', 'CHN', 'DEU'])."
    )

    affected_products: Optional[List[int]] = Field(
        default=None,
        description="List of HS product codes (6-digit integers). Only covers goods, not services."
    )

    affected_sectors: Optional[List[Union[str, int]]] = Field(
        default=None,
        description=(
            "Filter by CPC sector codes or names. Use for services (ID >= 500) or broad categories. "
            "Accepts IDs, names, or mixed with fuzzy matching."
        )
    )

    intervention_types: Optional[List[str]] = Field(
        default=None,
        description="List of intervention types (e.g., ['Import tariff', 'Export subsidy'])."
    )

    mast_chapters: Optional[List[str]] = Field(
        default=None,
        description="Filter by UN MAST chapter classifications (A-P). Use for broad policy categories."
    )

    gta_evaluation: Optional[List[str]] = Field(
        default=None,
        description="GTA evaluation: 'Red' (harmful), 'Amber' (likely harmful), 'Green' (liberalising). Use 'Harmful' for Red+Amber combined."
    )

    eligible_firms: Optional[List[Union[str, int]]] = Field(
        default=None,
        description="Filter by eligible firm types (all, SMEs, firm-specific, state-controlled, etc.)."
    )

    implementation_levels: Optional[List[Union[str, int]]] = Field(
        default=None,
        description="Filter by government level (Supranational, National, Subnational, SEZ, IFI, NFI)."
    )

    date_announced_gte: Optional[str] = Field(
        default=None,
        description="Announced on or after this date (YYYY-MM-DD)."
    )

    date_announced_lte: Optional[str] = Field(
        default=None,
        description="Announced on or before this date (YYYY-MM-DD)."
    )

    date_implemented_gte: Optional[str] = Field(
        default=None,
        description="Implemented on or after this date (YYYY-MM-DD)."
    )

    date_implemented_lte: Optional[str] = Field(
        default=None,
        description="Implemented on or before this date (YYYY-MM-DD)."
    )

    date_removed_gte: Optional[str] = Field(
        default=None,
        description="Revoked/removed on or after this date (YYYY-MM-DD)."
    )

    date_removed_lte: Optional[str] = Field(
        default=None,
        description="Revoked/removed on or before this date (YYYY-MM-DD)."
    )

    affected_flow: Optional[List[int]] = Field(
        default=None,
        description="Filter by trade flow direction: 1 (Inward), 2 (Outward), 3 (Outward subsidy)."
    )

    is_in_force: Optional[bool] = Field(
        default=None,
        description="Filter by whether intervention is currently in force."
    )

    query: Optional[str] = Field(
        default=None,
        description="Full-text search for entity names only (companies, programs). Use structured filters first."
    )

    # Exclusion/inclusion controls
    keep_affected: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified affected jurisdictions.")
    keep_implementer: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified implementing jurisdictions.")
    keep_intervention_types: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified intervention types.")
    keep_mast_chapters: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified MAST chapters.")
    keep_implementation_level: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified implementation levels.")
    keep_eligible_firms: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified firm types.")
    keep_affected_sectors: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified CPC sectors.")
    keep_affected_products: Optional[bool] = Field(default=None, description="Include (True) or exclude (False) specified HS products.")

    intervention_id: Optional[List[int]] = Field(
        default=None,
        description="Filter by specific GTA intervention IDs."
    )
    keep_intervention_id: Optional[bool] = Field(
        default=None,
        description="Include (True) or exclude (False) specified intervention IDs."
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable tables or 'json' for raw data."
    )

    @field_validator('implementing_jurisdictions', 'affected_jurisdictions')
    @classmethod
    def validate_count_iso_codes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure ISO codes are uppercase."""
        if v is not None:
            return [code.upper() for code in v]
        return v
