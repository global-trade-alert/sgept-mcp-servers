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
                   "Filter interventions by countries that implemented the measure."
    )
    
    affected_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="List of affected jurisdiction ISO codes (e.g., ['USA', 'CHN', 'DEU']). "
                   "Filter interventions by countries affected by the measure."
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
                   "Filter by type of trade measure."
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
            "Sort order for results. Common values:\n"
            "- '-date_announced': Newest interventions first (RECOMMENDED for finding recent data)\n"
            "- 'date_announced': Oldest interventions first\n"
            "- '-intervention_id': Highest intervention ID first\n"
            "- 'intervention_id': Lowest intervention ID first\n"
            "Valid sort fields: date_announced, date_published, date_implemented, date_removed, intervention_id\n"
            "Use '-' prefix for descending order. Can combine multiple fields with commas."
        )
    )

    # Exclusion/inclusion controls (keep parameters)
    keep_affected: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified affected jurisdictions are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified affected jurisdictions\n"
            "• False: EXCLUDE specified jurisdictions, show everything else\n\n"
            "Example - Everything EXCEPT measures affecting China:\n"
            "  affected_jurisdictions=['CHN'], keep_affected=False"
        )
    )

    keep_implementer: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified implementing jurisdictions are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified implementing jurisdictions\n"
            "• False: EXCLUDE specified jurisdictions, show everything else\n\n"
            "Example - All measures EXCEPT those by G7 countries:\n"
            "  implementing_jurisdictions=['USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN'], keep_implementer=False"
        )
    )

    keep_intervention_types: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified intervention types are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified intervention types\n"
            "• False: EXCLUDE specified types, show all other types\n\n"
            "Example - All non-tariff measures (exclude tariffs):\n"
            "  intervention_types=['Import tariff', 'Export tariff'], keep_intervention_types=False"
        )
    )

    keep_mast_chapters: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified MAST chapters are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified MAST chapters\n"
            "• False: EXCLUDE specified chapters, show all others\n\n"
            "Example - All measures EXCEPT subsidies:\n"
            "  mast_chapters=['L'], keep_mast_chapters=False"
        )
    )

    keep_implementation_level: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified implementation levels are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified implementation levels\n"
            "• False: EXCLUDE specified levels, show all others\n\n"
            "Example - Only subnational measures (exclude national):\n"
            "  implementation_levels=['National', 'Supranational'], keep_implementation_level=False"
        )
    )

    keep_eligible_firms: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified eligible firm types are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified firm types\n"
            "• False: EXCLUDE specified types, show all others\n\n"
            "Example - Universal policies only (exclude firm-specific):\n"
            "  eligible_firms=['firm-specific', 'SMEs'], keep_eligible_firms=False"
        )
    )

    keep_affected_sectors: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified CPC sectors are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified sectors\n"
            "• False: EXCLUDE specified sectors, show all others\n\n"
            "Example - All sectors EXCEPT agriculture:\n"
            "  affected_sectors=[11, 12, 13, 21, 22], keep_affected_sectors=False"
        )
    )

    keep_affected_products: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified HS product codes are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified products\n"
            "• False: EXCLUDE specified products, show all others\n\n"
            "Example - All products EXCEPT semiconductors:\n"
            "  affected_products=[854110, 854121, 854129], keep_affected_products=False"
        )
    )

    keep_implementation_period_na: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether interventions with NO implementation date are included.\n\n"
            "• True (default): Include interventions with NULL/NA implementation dates\n"
            "• False: EXCLUDE interventions without implementation dates (show only dated measures)\n\n"
            "Example - Only interventions with known implementation dates:\n"
            "  keep_implementation_period_na=False\n\n"
            "Note: Works independently of implementation_period date range filter"
        )
    )

    keep_revocation_na: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether interventions with NO revocation date are included.\n\n"
            "• True (default): Include interventions with NULL/NA revocation dates\n"
            "• False: EXCLUDE interventions without revocation dates (show only revoked measures)\n\n"
            "Example - Only revoked measures with known revocation dates:\n"
            "  keep_revocation_na=False\n\n"
            "Note: Works independently of revocation_period date range filter"
        )
    )

    keep_intervention_id: Optional[bool] = Field(
        default=None,
        description=(
            "Control whether specified intervention IDs are INCLUDED or EXCLUDED.\n\n"
            "• True (default): Include only specified intervention IDs\n"
            "• False: EXCLUDE specified IDs, show all others\n\n"
            "Example - Exclude specific interventions from results:\n"
            "  intervention_id=[138295, 137842, 139103], keep_intervention_id=False"
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
