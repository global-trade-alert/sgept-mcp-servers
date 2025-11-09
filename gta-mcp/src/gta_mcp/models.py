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
            "List of CPC (Central Product Classification) sector codes or names. "
            "Provides broader product range coverage than HS codes.\n\n"
            "🔑 KEY DIFFERENCES:\n"
            "• CPC sectors: Broader categories, includes SERVICES (ID >= 500)\n"
            "• HS codes: Specific goods only, more restrictive\n\n"
            "⚠️ WHEN TO USE CPC SECTORS:\n"
            "• Services queries (financial, legal, transport, etc.) - REQUIRED\n"
            "• Broad product categories (e.g., 'cereals', 'textiles', 'machinery')\n"
            "• When you need comprehensive coverage of a product range\n\n"
            "💡 USAGE:\n"
            "• By ID: [11, 21, 711] - Cereals, Live animals, Financial services\n"
            "• By name: ['Cereals', 'Financial services', 'Textiles']\n"
            "• Mixed: [11, 'Financial services', 412]\n"
            "• Fuzzy matching supported (e.g., 'financial' matches 'Financial services')\n\n"
            "📋 EXAMPLES:\n"
            "Services (ID >= 500):\n"
            "• 711-717: Financial services\n"
            "• 721-722: Real estate\n"
            "• 841-846: Telecommunications\n"
            "• 921-929: Education\n\n"
            "Goods (ID < 500):\n"
            "• 11-19: Agricultural products\n"
            "• 211-239: Food products\n"
            "• 411-416: Metals\n"
            "• 491-499: Transport equipment\n\n"
            "Use gta://reference/sectors-list resource to see all available sectors."
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
            "Filter by UN MAST (Multi-Agency Support Team) chapter classifications.\n\n"
            "📊 WHEN TO USE:\n"
            "• Use mast_chapters for BROAD categorization (e.g., 'all subsidies', 'all import measures')\n"
            "• Use intervention_types for SPECIFIC measures (e.g., 'Import tariff', 'State aid')\n"
            "• For generic questions, MAST chapters provide more comprehensive coverage\n\n"
            "🔤 MAST CHAPTERS (A-P):\n\n"
            "TECHNICAL MEASURES:\n"
            "• A: Sanitary and phytosanitary measures (SPS)\n"
            "  - Food safety, animal/plant health standards, testing requirements\n"
            "  - Use for: health regulations, agricultural standards, biosecurity\n\n"
            "• B: Technical barriers to trade (TBT)\n"
            "  - Product standards, labeling, testing, certification requirements\n"
            "  - Use for: technical regulations, conformity assessments, quality standards\n\n"
            "• C: Pre-shipment inspection and other formalities\n"
            "  - Quality/quantity verification before shipment, customs formalities\n"
            "  - Use for: inspection requirements, customs procedures\n\n"
            "NON-TECHNICAL MEASURES:\n"
            "• D: Contingent trade-protective measures\n"
            "  - Anti-dumping, countervailing duties, safeguards\n"
            "  - Use for: trade defense instruments, emergency measures\n\n"
            "• E: Non-automatic licensing, quotas, prohibitions\n"
            "  - Import/export licenses, quantitative restrictions, bans\n"
            "  - Use for: licensing requirements, quotas, prohibitions\n\n"
            "• F: Price-control measures\n"
            "  - Minimum import prices, reference prices, variable charges\n"
            "  - Use for: price interventions, administrative pricing\n\n"
            "• G: Finance measures\n"
            "  - Payment terms, credit restrictions, advance payments\n"
            "  - Use for: financial conditions of trade\n\n"
            "• H: Anti-competitive measures\n"
            "  - State trading, monopolies, exclusive rights\n"
            "  - Use for: competition restrictions, state monopolies\n\n"
            "• I: Trade-related investment measures\n"
            "  - Local content requirements, trade balancing, foreign exchange\n"
            "  - Use for: investment conditions affecting trade\n\n"
            "• J: Distribution restrictions\n"
            "  - Geographic restrictions, authorized agents, resale limitations\n"
            "  - Use for: distribution controls, retail restrictions\n\n"
            "• K: Restrictions on post-sales services\n"
            "  - Warranty, repair, maintenance requirements\n"
            "  - Use for: after-sales service conditions\n\n"
            "• L: Subsidies and other forms of support\n"
            "  - Export subsidies, domestic support, state aid, grants, tax breaks\n"
            "  - Use for: ANY subsidy-related queries (most comprehensive)\n\n"
            "• M: Government procurement restrictions\n"
            "  - Local preferences, closed tenders, discriminatory bidding\n"
            "  - Use for: public procurement, Buy National policies\n\n"
            "• N: Intellectual property\n"
            "  - IP protection requirements, technology transfer rules\n"
            "  - Use for: patents, trademarks, copyrights, trade secrets\n\n"
            "• O: Rules of origin\n"
            "  - Criteria for determining product nationality\n"
            "  - Use for: origin requirements, local content rules\n\n"
            "• P: Export-related measures\n"
            "  - Export taxes, restrictions, licensing, prohibitions\n"
            "  - Use for: export controls, export duties\n\n"
            "💡 EXAMPLES:\n"
            "• Broad subsidy search: mast_chapters=['L']\n"
            "• Specific subsidy: intervention_types=['State aid']\n"
            "• All import barriers: mast_chapters=['E', 'F']\n"
            "• Specific tariff: intervention_types=['Import tariff']\n"
            "• Trade defense: mast_chapters=['D']\n"
            "• FDI measures: mast_chapters=['FDI measures']\n"
            "• Capital controls: mast_chapters=['Capital control measures']\n\n"
            "📋 ACCEPTED FORMATS:\n"
            "• Letters: ['A', 'B', 'L'] (recommended for standard chapters)\n"
            "• Integer IDs: ['1', '2', '10'] or [1, 2, 10] (API IDs 1-20)\n"
            "• Special categories: ['Capital control measures', 'FDI measures', 'Migration measures', 'Tariff measures']\n\n"
            "Note: Letters A-P map to specific IDs (e.g., A=1, L=10, C=17). See mast_chapters.md for full mapping."
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
            "Filter by types of firms eligible/targeted by the intervention.\n\n"
            "Valid types:\n"
            "• 'all' (ID: 1): Policy applies to all types of companies\n"
            "• 'SMEs' (ID: 2): Small and medium enterprises, entrepreneurs, start-ups\n"
            "• 'firm-specific' (ID: 3): Targeting a specific company or specific project\n"
            "• 'state-controlled' (ID: 4): Companies with >50% public ownership stake\n"
            "• 'state trading enterprise' (ID: 5): Majority publicly owned with monopoly privileges\n"
            "• 'sector-specific' (ID: 6): Firms in enumerated economic activity different from target\n"
            "• 'location-specific' (ID: 7): Firms in specific sub-national location\n"
            "• 'processing trade' (ID: 8): Firms that import, process, and export\n\n"
            "Examples:\n"
            "• SME-targeted subsidies: eligible_firms=['SMEs']\n"
            "• Tesla-specific incentives: eligible_firms=['firm-specific']\n"
            "• State enterprise requirements: eligible_firms=['state-controlled']\n"
            "• Regional development zones: eligible_firms=['location-specific']"
        )
    )

    implementation_levels: Optional[List[str | int]] = Field(
        default=None,
        description=(
            "Filter by government level implementing the intervention.\n\n"
            "Valid levels:\n"
            "• 'Supranational' (ID: 1): Supranational bodies (e.g., European Commission)\n"
            "• 'National' (ID: 2): Central government agencies, including central banks\n"
            "• 'Subnational' (ID: 3): Regional, state, provincial, or municipal governments\n"
            "• 'SEZ' (ID: 4): Special economic zones\n"
            "• 'IFI' (ID: 5): International financial institutions (multi-country ownership)\n"
            "• 'NFI' (ID: 6): National financial institutions (e.g., Export-Import banks)\n\n"
            "Examples:\n"
            "• EU-wide measures: implementation_levels=['Supranational']\n"
            "• National policies only: implementation_levels=['National']\n"
            "• State/provincial actions: implementation_levels=['Subnational']\n"
            "• Development bank programs: implementation_levels=['NFI']\n\n"
            "Note: Aliases supported - 'IFI', 'NFI', 'SEZ' match full names"
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
