"""Pydantic models for GTA MCP server input validation."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


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
        description="GTA evaluation colors: 'Red' (harmful), 'Amber' (mixed), or 'Green' (liberalizing). "
                   "Filter by impact assessment."
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
            "Common: '-date_announced' (newest first, recommended), 'date_announced' (oldest first). "
            "Valid fields: date_announced, date_published, date_implemented, date_removed, intervention_id. "
            "Can combine with commas."
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

    keep_implementation_period_na: Optional[bool] = Field(
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

    keep_intervention_id: Optional[bool] = Field(
        default=None,
        description=(
            "Include (True, default) or exclude (False) specified intervention IDs. "
            "Example: keep_intervention_id=False excludes specific interventions. "
            "See gta://guide/exclusion-filters for complete guide."
        )
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )
    
    @field_validator('implementing_jurisdictions', 'affected_jurisdictions')
    @classmethod
    def validate_iso_codes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure ISO codes are uppercase."""
        if v is not None:
            return [code.upper() for code in v]
        return v


class GTAGetInterventionInput(BaseModel):
    """Input model for fetching a specific intervention."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    intervention_id: int = Field(
        ...,
        description="The unique GTA intervention ID (e.g., 138295)",
        gt=0
    )
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
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
