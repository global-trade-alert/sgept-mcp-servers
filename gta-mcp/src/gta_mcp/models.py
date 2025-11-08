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
                   "Filter interventions affecting specific products."
    )
    
    intervention_types: Optional[List[str]] = Field(
        default=None,
        description="List of intervention types (e.g., ['Import tariff', 'Export subsidy', 'State aid']). "
                   "Filter by type of trade measure."
    )
    
    gta_evaluation: Optional[List[str]] = Field(
        default=None,
        description="GTA evaluation colors: 'Red' (harmful), 'Amber' (mixed), or 'Green' (liberalizing). "
                   "Filter by impact assessment."
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
            "Full-text search for ENTITY NAMES and SPECIFIC PRODUCTS only.\n\n"
            "⚠️ CRITICAL: Use query ONLY after exhausting structured filters!\n\n"
            "QUERY STRATEGY (FOLLOW THIS CASCADE):\n"
            "1. START with structured filters:\n"
            "   • intervention_types - For policy types (tariffs, subsidies, bans, etc.)\n"
            "   • implementing_jurisdictions/affected_jurisdictions - For countries\n"
            "   • affected_products - For HS product codes when known\n"
            "   • gta_evaluation - For impact assessment (Red/Amber/Green)\n"
            "   • date filters - For time periods\n\n"
            "2. THEN add query ONLY for:\n"
            "   • Company names: 'Tesla', 'Huawei', 'BYD', 'TSMC'\n"
            "   • Program names: 'Made in China 2025', 'Inflation Reduction Act'\n"
            "   • Technology/product names not in HS codes: 'ChatGPT', '5G', 'CRISPR'\n"
            "   • Specific named entities that cannot be filtered otherwise\n\n"
            "3. DO NOT use query for:\n"
            "   ✗ Intervention types (use intervention_types parameter)\n"
            "   ✗ Generic policy terms ('subsidy', 'tariff', 'ban')\n"
            "   ✗ Country names (use jurisdiction parameters)\n"
            "   ✗ Concepts already covered by structured filters\n\n"
            "✅ CORRECT EXAMPLES:\n"
            "• Tesla subsidies:\n"
            "  query='Tesla'\n"
            "  intervention_types=['State aid', 'Financial grant']\n"
            "  implementing_jurisdictions=['USA']\n\n"
            "• AI export controls:\n"
            "  query='artificial intelligence | AI'\n"
            "  intervention_types=['Export ban', 'Export licensing requirement']\n"
            "  date_announced_gte='2023-01-01'\n\n"
            "• Electric vehicle subsidies:\n"
            "  query='electric | EV'\n"
            "  intervention_types=['Subsidy', 'State aid', 'Tax-based export incentive']\n"
            "  affected_products=[870310, 870320, 870380]  # Car HS codes\n\n"
            "• Huawei sanctions:\n"
            "  query='Huawei'\n"
            "  intervention_types=['Import ban', 'Export ban']\n"
            "  affected_jurisdictions=['CHN']\n\n"
            "❌ INCORRECT (too much in query):\n"
            "✗ query='(AI | artificial intelligence) & export control'\n"
            "  → Use intervention_types=['Export ban', 'Export licensing requirement'] instead!\n\n"
            "✗ query='electric vehicles & subsid#'\n"
            "  → Use intervention_types for subsidies, query only for 'electric | EV'!\n\n"
            "✗ query='semiconductor & tariff'\n"
            "  → Use intervention_types=['Import tariff'], affected_products=[HS codes]!\n\n"
            "QUERY SYNTAX REFERENCE:\n"
            "When searching for entities, you can use these operators:\n\n"
            "SINGLE WORD SEARCHES:\n"
            "• Exact match: 'WTO' finds interventions containing 'WTO'\n"
            "• Spelling variations: Use '#' for variants\n"
            "  - 'utili#ation' matches both 'utilization' and 'utilisation'\n"
            "  - 'subsidi#' matches 'subsidy', 'subsidies', 'subsidize', 'subsidise'\n"
            "• Symbol handling: 'non-tariff', 'non+tariff', 'non*tariff' all treated as 'non#tariff'\n\n"
            "PHRASE & COMPLEX SEARCHES:\n"
            "• Exact phrase: 'electronic commerce' matches the complete phrase\n"
            "• OR logic: Use '|' to match either term\n"
            "  - 'Tesla | BYD | Volkswagen' - Match any company\n"
            "  - 'artificial intelligence | AI | machine learning'\n"
            "• AND logic: Use '&' to require both terms (use sparingly for entities)\n"
            "  - 'Made in China & 2025' - Both terms required\n"
            "  - '5G & Huawei'\n"
            "• Parentheses: Use '()' for complex logic\n"
            "  - '(Tesla | SpaceX) & Musk' - Complex hierarchy\n"
            "  - '(5G | sixth generation) & (Huawei | ZTE)'\n\n"
            "REMEMBER: Query searches intervention title, description, and sources. Keep it focused on entities!"
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
