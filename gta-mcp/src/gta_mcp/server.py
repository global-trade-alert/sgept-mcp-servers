"""GTA MCP Server - Exposes Global Trade Alert database via MCP protocol."""

import os
import sys
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP

from .models import (
    GTASearchInput,
    GTAGetInterventionInput,
    GTATickerInput,
    GTAImpactChainInput,
    GTACountInput,
    ResponseFormat
)
from .api import GTAAPIClient, build_filters, build_count_filters
from .auth import JWTAuthManager
from .formatters import (
    format_interventions_markdown,
    format_interventions_json,
    format_interventions_overview,
    format_intervention_detail_markdown,
    format_ticker_markdown,
    format_counts_markdown,
    format_counts_json,
    CHARACTER_LIMIT
)
from .resources_loader import (
    load_jurisdictions_table,
    load_intervention_types,
    parse_jurisdiction_by_iso,
    parse_intervention_type,
    list_available_intervention_types,
    load_search_guide,
    load_date_fields_guide,
    load_sectors_table,
    load_cpc_vs_hs_guide,
    load_eligible_firms_table,
    load_implementation_levels_table,
    load_parameters_guide,
    load_query_examples,
    load_mast_chapters,
    load_query_syntax,
    load_exclusion_filters,
    load_data_model_guide,
    load_analytical_caveats,
    load_common_mistakes,
    load_glossary,
    load_search_strategy,
    load_jurisdiction_groups,
    load_query_intent_mapping,
    load_privacy_policy,
)
from .hs_lookup import search_hs_codes
from .sector_lookup import search_sectors


# Initialize MCP server
mcp = FastMCP("gta_mcp")


def get_api_client() -> GTAAPIClient:
    """Get initialized GTA API client with API key from environment."""
    api_key = os.getenv("GTA_API_KEY")
    if not api_key:
        raise ValueError(
            "GTA_API_KEY environment variable not set. "
            "Please set your API key: export GTA_API_KEY='your-key-here'"
        )
    return GTAAPIClient(api_key)


# Key profiles for show_keys — controls which fields the API returns per intervention.
# "overview" is compact (~0.3KB/record) for broad triage; "standard" is analysis-ready
# (~2-5KB/record); "full" returns everything including large product/description arrays.
KEY_PROFILES = {
    "overview": [
        "intervention_id", "state_act_title", "intervention_type",
        "gta_evaluation", "date_announced", "is_in_force",
        "implementing_jurisdictions", "intervention_url"
    ],
    "standard": [
        "intervention_id", "state_act_id", "state_act_title",
        "intervention_type", "mast_chapter", "gta_evaluation",
        "implementation_level", "eligible_firm",
        "date_announced", "date_implemented", "date_removed",
        "is_in_force",
        "implementing_jurisdictions", "affected_jurisdictions",
        "affected_sectors",
        "intervention_url", "state_act_url", "is_official_source"
    ],
    "full": None  # No show_keys = API returns everything
}


# JWT auth manager - DEPRECATED (kept for backward compatibility)
# As of API v0.3+, all endpoints including counts now support API key auth.
# JWT auth is no longer required or used.
_auth_manager: Optional[JWTAuthManager] = None


def get_auth_manager() -> JWTAuthManager:
    """[DEPRECATED] Get or create the JWT auth manager.

    This function is kept for backward compatibility but is no longer used.
    All GTA API endpoints now use API key authentication.

    Raises:
        ValueError: If GTA_AUTH_EMAIL or GTA_AUTH_PASSWORD not configured.
    """
    global _auth_manager
    if _auth_manager is None:
        email = os.getenv("GTA_AUTH_EMAIL")
        password = os.getenv("GTA_AUTH_PASSWORD")
        if not email or not password:
            raise ValueError(
                "[DEPRECATED] JWT authentication is no longer required.\n"
                "All GTA endpoints now use API key authentication via GTA_API_KEY.\n"
                "GTA_AUTH_EMAIL and GTA_AUTH_PASSWORD are optional and not needed."
            )
        _auth_manager = JWTAuthManager(email=email, password=password)
    return _auth_manager


@mcp.tool(
    name="gta_search_interventions",
    annotations={
        "title": "Search GTA Trade Interventions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gta_search_interventions(params: GTASearchInput) -> str:
    """Search and retrieve trade policy interventions from the Global Trade Alert database.

    THIS IS THE PRIMARY TOOL for finding, listing, and reading interventions. Use it when the user
    wants to see, browse, find, or analyse actual intervention records — including their titles,
    descriptions, dates, types, evaluations, and affected parties.

    Do NOT use `gta_count_interventions` when the user asks to see or read interventions.
    `gta_count_interventions` only returns aggregate numbers, not intervention records.

    Use structured filters FIRST, then add 'query' ONLY for entity names not captured by filters.

    BEFORE calling this tool:
    - For commodity/product queries → use `gta_lookup_hs_codes` to find HS product codes
    - For service/sector queries → use `gta_lookup_sectors` to find CPC sector codes
    - For country groups (G20, EU, BRICS) → see gta://reference/jurisdiction-groups
    - For mapping concepts to filters → see gta://guide/query-intent-mapping

    Key filters: implementing_jurisdictions, affected_products, mast_chapters, intervention_types,
    gta_evaluation, date_announced_gte. Use 'query' ONLY for named entities (companies, programs).

    gta_evaluation: 'Red' (harmful), 'Amber' (likely harmful), 'Green' (liberalising).
    Use 'Harmful' as shorthand for Red+Amber.

    ⚠️ CRITICAL: Include the "Reference List" section from the response in your reply exactly
    as formatted. Do NOT modify or reformat — it provides clickable citations.

    Examples:
        - US tariffs on China: implementing_jurisdictions=['USA'], affected_jurisdictions=['CHN'],
          intervention_types=['Import tariff'], date_announced_gte='2024-01-01'
        - Subsidies: mast_chapters=['L']
        - Lithium export controls: First use gta_lookup_hs_codes('lithium') to get codes,
          then mast_chapters=['P'], affected_products=[282520, 283691, ...]

    Resources: gta://guide/parameters, gta://guide/query-intent-mapping,
    gta://reference/mast-chapters, gta://reference/jurisdiction-groups
    """
    try:
        client = get_api_client()

        # Build filter dictionary and get informational messages
        filters, filter_messages = build_filters(params.model_dump(exclude={
            'limit', 'offset', 'sorting', 'response_format',
            'detail_level', 'show_keys'
        }))

        # Resolve show_keys from detail_level or explicit show_keys
        #
        # Auto-detection logic (when user doesn't set detail_level):
        # - Specific intervention_id lookup → standard keys (detail pass)
        # - Broad search (no intervention_id) → overview keys + limit=500 (triage pass)
        #
        # This enables the multi-pass workflow automatically:
        # 1. Any broad search returns a compact overview table (up to 500 results)
        # 2. The LLM triages and identifies relevant interventions
        # 3. The LLM calls again with intervention_id=[...] for full detail
        show_keys = None
        effective_limit = params.limit
        use_overview_format = False

        if params.show_keys:
            # Explicit show_keys overrides everything
            show_keys = params.show_keys
        elif params.detail_level:
            show_keys = KEY_PROFILES.get(params.detail_level)
            if params.detail_level == "overview":
                use_overview_format = True
                if params.limit == 50:
                    effective_limit = 1000
            elif params.detail_level == "standard":
                pass  # standard keys, user's limit
            # detail_level="full" → show_keys=None (API returns everything)
        elif params.intervention_id:
            # Fetching specific IDs — use standard detail (this is the detail pass)
            show_keys = KEY_PROFILES["standard"]
        else:
            # Broad search with no explicit detail_level — auto-select overview
            # This ensures the LLM always sees the full picture before drilling down
            show_keys = KEY_PROFILES["overview"]
            use_overview_format = True
            if params.limit == 50:
                effective_limit = 1000

        # Make API request
        results = await client.search_interventions(
            filters=filters,
            limit=effective_limit,
            offset=params.offset,
            sorting=params.sorting,
            show_keys=show_keys
        )

        # Wrap list response in expected format for formatters
        data = {
            "results": results,
            "count": len(results),
            "next": None if len(results) < effective_limit else f"Use offset={params.offset + effective_limit}",
            "previous": None if params.offset == 0 else f"Use offset={max(0, params.offset - effective_limit)}"
        }

        # Format response — overview mode uses compact table
        if use_overview_format and params.response_format == ResponseFormat.MARKDOWN:
            formatted_response = format_interventions_overview(data)
            if filter_messages:
                message_section = "\n".join([f"ℹ️ {msg}" for msg in filter_messages])
                formatted_response = f"{message_section}\n\n{formatted_response}"
            return formatted_response
        elif params.response_format == ResponseFormat.MARKDOWN:
            formatted_response = format_interventions_markdown(data)
            if filter_messages:
                message_section = "\n".join([f"ℹ️ {msg}" for msg in filter_messages])
                formatted_response = f"{message_section}\n\n{formatted_response}"
            return formatted_response
        else:
            response_json = format_interventions_json(data)
            if filter_messages:
                response_json["filter_messages"] = filter_messages
            return response_json
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}\n\nPlease ensure GTA_API_KEY is set in your environment."
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return (
                "❌ Authentication Error: Invalid or expired API key.\n\n"
                "Please check your GTA_API_KEY environment variable."
            )
        elif "404" in error_msg:
            return "❌ API endpoint not found. The GTA API structure may have changed."
        elif "timeout" in error_msg.lower():
            return (
                "❌ Request timeout: The API took too long to respond.\n\n"
                "Try reducing the limit parameter or adding more specific filters."
            )
        else:
            return f"❌ API Error: {error_msg}\n\nTry adjusting your search parameters or contact support."


@mcp.tool(
    name="gta_get_intervention",
    annotations={
        "title": "Get Detailed GTA Intervention",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gta_get_intervention(params: GTAGetInterventionInput) -> str:
    """Fetch the FULL TEXT and complete details for a specific GTA intervention by ID.

    USE THIS TOOL when the user asks to read, fetch, or see the text/description of a specific
    intervention. This is the only tool that returns the full intervention description, source
    documents, and all metadata. `gta_search_interventions` returns summaries;
    `gta_count_interventions` returns only aggregate counts — neither provides full text.

    Returns comprehensive data including description, sources, all affected countries and products,
    implementation timeline, and evaluation details.

    Args:
        params (GTAGetInterventionInput): Parameters including:
            - intervention_id: The unique GTA intervention ID (required)
            - response_format: 'markdown' (default) or 'json'

    Returns:
        str: Complete intervention details with all metadata, formatted per response_format.
             Includes full description, all sources, jurisdictions, products, and timeline.

             ⚠️ CRITICAL: The response includes a "Reference List (in reverse chronological order)"
             section at the end. You MUST include this complete reference list in your response to
             the user EXACTLY as formatted. The reference list format is:
             - {date}: {title} [ID [{intervention_id}](url)].
             Do NOT modify or reformat the reference list. It provides essential clickable citations.

    Examples:
        - "Show me the text of intervention 138295" → use this tool
        - "What does intervention 138295 say?" → use this tool
        - Get full details for intervention 138295 (EU tariff changes)
        - Fetch complete source documentation for a specific measure
    """
    try:
        client = get_api_client()

        # Fetch intervention
        intervention = await client.get_intervention(params.intervention_id)

        # Wrap single intervention in expected format for formatters
        data = {"results": [intervention]}

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            return format_intervention_detail_markdown(data)
        else:
            return format_interventions_json(data)
            
    except ValueError as e:
        if "not found" in str(e):
            return f"❌ Intervention {params.intervention_id} not found in GTA database."
        return f"❌ Error: {str(e)}"
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return "❌ Authentication Error: Invalid or expired API key."
        else:
            return f"❌ API Error: {error_msg}"


@mcp.tool(
    name="gta_list_ticker_updates",
    annotations={
        "title": "List GTA Ticker Updates",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gta_list_ticker_updates(params: GTATickerInput) -> str:
    """Get recent text updates to existing GTA interventions via the ticker endpoint.

    The ticker provides updates when intervention descriptions or details are modified,
    showing what changed without needing to re-fetch full intervention data. Useful
    for monitoring policy evolution and tracking changes to existing measures.

    Args:
        params (GTATickerInput): Parameters including:
            - implementing_jurisdictions: Filter by implementing country ISO codes
            - intervention_types: Filter by intervention types
            - date_modified_gte: Updates modified on or after this date (YYYY-MM-DD)
            - limit: Max results (1-1000, default 50)
            - offset: Pagination offset (default 0)
            - response_format: 'markdown' (default) or 'json'

    Returns:
        str: List of ticker updates with modification dates, intervention IDs, and update text.

             ⚠️ CRITICAL: The response includes a "Referenced Interventions" section at the end.
             You MUST include this complete reference list in your response to the user EXACTLY
             as formatted. Do NOT modify or reformat the reference list. It provides essential
             clickable links to all mentioned interventions.

    Note: GTA entries are created by analysts after policy implementation. Recent entries may not
    yet appear. Use overlapping scan windows (e.g., 8-day window for weekly monitoring) to avoid gaps.

    Examples:
        - Get updates from the last week
        - Track changes to US trade measures
    """
    try:
        client = get_api_client()

        # Build filter dictionary and get informational messages
        filters, filter_messages = build_filters(params.model_dump(exclude={'limit', 'offset', 'response_format'}))

        # Make API request
        results = await client.get_ticker_updates(
            filters=filters,
            limit=params.limit,
            offset=params.offset
        )

        # Wrap response in expected format for formatters
        # Ticker API returns a list directly, not a dict
        if isinstance(results, list):
            data = {
                "results": results,
                "count": len(results),
                "next": None if len(results) < params.limit else f"Use offset={params.offset + params.limit}",
                "previous": None if params.offset == 0 else f"Use offset={max(0, params.offset - params.limit)}"
            }
        else:
            data = results

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            formatted_response = format_ticker_markdown(data)
            # Prepend filter messages if any
            if filter_messages:
                message_section = "\n".join([f"ℹ️ {msg}" for msg in filter_messages])
                formatted_response = f"{message_section}\n\n{formatted_response}"
            return formatted_response
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)
            
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return "❌ Authentication Error: Invalid or expired API key."
        else:
            return f"❌ API Error: {error_msg}"


@mcp.tool(
    name="gta_get_impact_chains",
    annotations={
        "title": "Get GTA Impact Chains",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gta_get_impact_chains(params: GTAImpactChainInput) -> str:
    """Extract granular impact chains showing implementing-product/sector-affected jurisdiction tuples.
    
    Unlike the main data endpoint which aggregates data, impact chains provide unaggregated
    relationships between implementing jurisdictions, affected products/sectors, and affected
    jurisdictions. Essential for bilateral trade flow analysis and detailed impact assessment.
    
    Args:
        params (GTAImpactChainInput): Parameters including:
            - granularity: 'product' for HS codes or 'sector' for broader categories (required)
            - implementing_jurisdictions: Filter by implementing country ISO codes
            - affected_jurisdictions: Filter by affected country ISO codes
            - limit: Max results (1-1000, default 50)
            - offset: Pagination offset (default 0)
            - response_format: 'markdown' (default) or 'json'
    
    Returns:
        str: Granular impact chain data showing specific jurisdiction-product-jurisdiction relationships.
    
    Examples:
        - Get product-level impact chains for US implementing jurisdictions
        - Analyze sector-level impacts on EU countries
    """
    try:
        client = get_api_client()

        # Build filter dictionary and get informational messages
        filters, filter_messages = build_filters(
            params.model_dump(exclude={'granularity', 'limit', 'offset', 'response_format'})
        )

        # Make API request
        data = await client.get_impact_chains(
            granularity=params.granularity,
            filters=filters,
            limit=params.limit,
            offset=params.offset
        )

        # Add filter messages to response if any
        if filter_messages:
            data["filter_messages"] = filter_messages

        # Format response (JSON is most useful for impact chains)
        return json.dumps(data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return "❌ Authentication Error: Invalid or expired API key."
        elif "404" in error_msg:
            return (
                f"❌ Endpoint not found for granularity '{params.granularity}'.\n\n"
                "Valid options: 'product' or 'sector'"
            )
        else:
            return f"❌ API Error: {error_msg}"


@mcp.tool(
    name="gta_count_interventions",
    annotations={
        "title": "Count/Aggregate GTA Trade Interventions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gta_count_interventions(params: GTACountInput) -> str:
    """Count and aggregate trade policy interventions by one or more dimensions.

    ONLY use this tool when the user explicitly asks for counts, totals, statistics, or
    numerical breakdowns. This tool returns ONLY aggregate numbers — it does NOT return
    intervention titles, descriptions, text, or any individual intervention data.

    ⚠️ Do NOT use this tool when the user asks to:
    - See, read, or fetch interventions → use `gta_search_interventions`
    - Read the text/description of a specific intervention → use `gta_get_intervention`
    - List or browse interventions → use `gta_search_interventions`
    - Analyse specific measures → use `gta_search_interventions` first, then `gta_get_intervention`

    Use this tool for summary statistics and breakdowns such as:
    - "How many harmful interventions has the US announced per year?"
    - "Count of subsidies by type and evaluation"
    - "What is the total number of interventions per MAST chapter?"

    Key parameters:
    - count_by: Dimensions to group by (e.g., ['date_announced_year', 'gta_evaluation'])
    - count_variable: What to count ('intervention_id' or 'state_act_id')
    - All standard filter parameters (jurisdictions, dates, types, etc.)

    Common count_by dimensions:
    - date_announced_year / date_implemented_year: Annual trends
    - gta_evaluation: Harmful vs liberalizing split
    - intervention_type: By specific measure type
    - implementer: By implementing country
    - mast_chapter: By broad policy category
    - affected: By affected country

    ⚠️ When counting by sector or product (count_by includes 'sector', 'product', etc.), results
    show intervention-sector/product COMBINATIONS, not unique interventions. A single intervention
    affecting 50 HS codes appears 50 times. To count unique interventions, use count_by dimensions
    that don't expand (e.g., 'implementer', 'date_announced_year', 'gta_evaluation').

    Examples:
        - US harmful interventions by year:
          count_by=['date_announced_year'], implementing_jurisdictions=['USA'],
          gta_evaluation=['Red']

        - Cross-tab of year vs evaluation for all countries:
          count_by=['date_announced_year', 'gta_evaluation']

        - Subsidies by implementing country:
          count_by=['implementer'], mast_chapters=['L']
    """
    try:
        # Get API client
        client = get_api_client()

        # Build count-specific filters
        filter_params = params.model_dump(
            exclude={'count_by', 'count_variable', 'response_format'}
        )
        filters, filter_messages = build_count_filters(filter_params)

        # Make API request (now uses API key auth via self.headers)
        data = await client.count_interventions(
            count_by=list(params.count_by),
            count_variable=params.count_variable,
            filters=filters,
        )

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            return format_counts_markdown(
                data=data,
                count_by=list(params.count_by),
                count_variable=params.count_variable,
                filter_messages=filter_messages,
            )
        else:
            return format_counts_json(
                data=data,
                count_by=list(params.count_by),
                count_variable=params.count_variable,
            )

    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return (
                "❌ Authentication Error: Invalid or expired API key.\n\n"
                "Please check your GTA_API_KEY environment variable."
            )
        elif "timeout" in error_msg.lower():
            return (
                "❌ Request timeout: The counts query took too long.\n\n"
                "Try adding more specific filters to reduce the data set."
            )
        else:
            return f"❌ API Error: {error_msg}\n\nTry adjusting your count parameters or filters."


# ============================================================================
# Lookup Tools - Product & Sector Code Discovery
# ============================================================================


@mcp.tool(
    name="gta_lookup_hs_codes",
    annotations={
        "title": "Look Up HS Product Codes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gta_lookup_hs_codes(search_term: str, max_results: int = 50) -> str:
    """Search HS (Harmonized System) product codes by keyword, chapter number, or code prefix.

    Use BEFORE gta_search_interventions when the user asks about specific commodities or products.
    Returns matching codes across all 3 levels (chapters, headings, subheadings) with the numeric
    IDs needed for the affected_products filter.

    Examples:
        - search_term='lithium' → finds HS 282520, 283691, etc.
        - search_term='28' → lists all codes in chapter 28 (inorganic chemicals)
        - search_term='8541' → lists subheadings under heading 8541 (semiconductors)
        - search_term='steel' → finds relevant iron/steel HS codes

    Returns a markdown table with codes and a ready-to-use affected_products list.
    """
    try:
        return search_hs_codes(search_term, max_results)
    except FileNotFoundError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ Error searching HS codes: {str(e)}"


@mcp.tool(
    name="gta_lookup_sectors",
    annotations={
        "title": "Look Up CPC Sector Codes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gta_lookup_sectors(search_term: str, max_results: int = 50) -> str:
    """Search CPC (Central Product Classification) sector codes by keyword or code prefix.

    Use BEFORE gta_search_interventions when the user asks about services or broad sector
    categories. Returns matching sectors with IDs for the affected_sectors filter.
    CPC ID >= 500 = services, ID < 500 = goods.

    Examples:
        - search_term='financial' → finds CPC 711, 715, 717
        - search_term='71' → lists all sectors in division 71 (financial services)
        - search_term='transport' → finds transport-related CPC sectors

    Returns a markdown table with codes and a ready-to-use affected_sectors list.
    """
    try:
        return search_sectors(search_term, max_results)
    except FileNotFoundError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ Error searching sectors: {str(e)}"


# ============================================================================
# MCP Prompts - Workflow Templates
# ============================================================================


@mcp.prompt(
    name="analyze_subsidies",
    description="Analyze government subsidies for a country and sector. Pre-configures MAST chapter L filter and structured search workflow."
)
def prompt_analyze_subsidies(country: str, sector: str) -> str:
    return (
        f"Analyze government subsidies by {country} in the {sector} sector.\n\n"
        "Follow this workflow:\n"
        f"1. Use `gta_lookup_hs_codes` or `gta_lookup_sectors` to find codes for '{sector}'\n"
        f"2. Use `gta_search_interventions` with:\n"
        f"   - implementing_jurisdictions=['{country}']\n"
        "   - mast_chapters=['L'] (subsidies)\n"
        "   - The product/sector codes from step 1\n"
        "   - gta_evaluation=['Harmful'] if focusing on discriminatory subsidies\n"
        "3. Triage the overview results and drill into the most relevant interventions\n"
        "4. Summarize: types of subsidies, scale, affected trading partners, timeline"
    )


@mcp.prompt(
    name="compare_trade_barriers",
    description="Compare trade barriers between two countries in a specific sector. Runs parallel searches for bilateral analysis."
)
def prompt_compare_trade_barriers(country_a: str, country_b: str, sector: str) -> str:
    return (
        f"Compare trade barriers between {country_a} and {country_b} in the {sector} sector.\n\n"
        "Follow this workflow:\n"
        f"1. Look up product/sector codes for '{sector}' using lookup tools\n"
        f"2. Search measures {country_a} implements affecting {country_b}:\n"
        f"   - implementing_jurisdictions=['{country_a}'], affected_jurisdictions=['{country_b}']\n"
        "   - gta_evaluation=['Harmful']\n"
        "   - The product/sector codes from step 1\n"
        f"3. Search measures {country_b} implements affecting {country_a}:\n"
        f"   - implementing_jurisdictions=['{country_b}'], affected_jurisdictions=['{country_a}']\n"
        "   - Same filters as above\n"
        "4. Compare: number of measures, types, severity, timeline\n"
        "5. Identify asymmetries and escalation patterns"
    )


@mcp.prompt(
    name="track_recent_changes",
    description="Monitor recent trade policy changes for a jurisdiction. Uses date_modified_gte for change tracking."
)
def prompt_track_recent_changes(days: str = "7", jurisdiction: str = "") -> str:
    jurisdiction_filter = f"\n   - implementing_jurisdictions=['{jurisdiction}']" if jurisdiction else ""
    return (
        f"Track trade policy changes from the last {days} days"
        f"{f' for {jurisdiction}' if jurisdiction else ' globally'}.\n\n"
        "Follow this workflow:\n"
        "1. Search for recently modified interventions:\n"
        f"   - date_modified_gte=(today minus {days} days, YYYY-MM-DD format)"
        f"{jurisdiction_filter}\n"
        "   - sorting='-last_updated'\n"
        "2. Also check the ticker for text updates:\n"
        f"   - Use `gta_list_ticker_updates` with date_modified_gte\n"
        "3. Categorize changes: new measures, modifications, removals\n"
        "4. Highlight the most significant changes by evaluation and type\n"
        "5. Note any patterns (escalation, liberalization trends)"
    )


@mcp.prompt(
    name="sector_impact_report",
    description="Generate a cross-country sector impact report. Analyzes which countries impose measures affecting a sector."
)
def prompt_sector_impact_report(sector: str, evaluation: str = "Harmful") -> str:
    return (
        f"Generate a sector impact report for '{sector}' focusing on {evaluation} measures.\n\n"
        "Follow this workflow:\n"
        f"1. Use lookup tools to find HS/CPC codes for '{sector}'\n"
        "2. Get aggregate counts by implementing country:\n"
        "   - Use `gta_count_interventions` with count_by=['implementer']\n"
        f"   - gta_evaluation=['{evaluation}']\n"
        "   - The product/sector codes from step 1\n"
        "3. Get aggregate counts by year:\n"
        "   - count_by=['date_announced_year']\n"
        "4. Search the most recent measures for context:\n"
        "   - Use `gta_search_interventions` with the same filters\n"
        "5. Summarize: top implementing countries, trend over time, measure types, "
        "key recent measures"
    )


@mcp.prompt(
    name="critical_minerals_tracker",
    description="Track trade measures affecting a specific critical mineral. Uses HS code lookup for precise product filtering."
)
def prompt_critical_minerals_tracker(mineral: str, evaluation: str = "Harmful") -> str:
    return (
        f"Track trade measures affecting {mineral}.\n\n"
        "Follow this workflow:\n"
        f"1. Use `gta_lookup_hs_codes` to find all HS codes related to '{mineral}'\n"
        "2. Search export restrictions:\n"
        "   - mast_chapters=['P'] (export measures)\n"
        "   - affected_products=[codes from step 1]\n"
        f"   - gta_evaluation=['{evaluation}']\n"
        "3. Search subsidies for domestic production:\n"
        "   - mast_chapters=['L'] (subsidies)\n"
        "   - affected_products=[same codes]\n"
        "4. Search import measures:\n"
        "   - mast_chapters=['D', 'E'] (trade defence, quotas)\n"
        "   - affected_products=[same codes]\n"
        "5. Summarize: which countries restrict exports, which subsidize production, "
        "which impose import barriers. Include timeline and current in-force status."
    )


@mcp.prompt(
    name="comprehensive_analysis",
    description="Produce a rich analysis combining quantitative trends (counts over time, by instrument, by direction) with qualitative evidence (what key interventions actually say). Use for policy briefs and analytical reports."
)
def prompt_comprehensive_analysis(topic: str, jurisdiction: str = "", since: str = "2020-01-01") -> str:
    jurisdiction_note = f" by or affecting {jurisdiction}" if jurisdiction else ""
    jurisdiction_filter = f"\n   - implementing_jurisdictions=['{jurisdiction}']" if jurisdiction else ""
    return (
        f"Produce a comprehensive analysis of {topic}{jurisdiction_note} since {since}.\n\n"
        "Combine quantitative trends with qualitative evidence from key interventions.\n\n"
        "## Part 1: Quantitative landscape\n\n"
        "Use `gta_count_interventions` to establish the statistical context:\n"
        f"1. Count by year: count_by=['date_announced_year'], date_announced_gte='{since}'"
        f"{jurisdiction_filter}\n"
        "   → Establishes the trend: growing, stable, or declining?\n"
        "2. Count by evaluation: count_by=['date_announced_year', 'gta_evaluation']\n"
        "   → What share is harmful vs liberalising?\n"
        "3. Count by instrument: count_by=['intervention_type'] or count_by=['mast_chapter']\n"
        "   → Which policy tools are used most?\n\n"
        "Summarise the numbers: total volume, direction of change, dominant instruments.\n\n"
        "## Part 2: Qualitative evidence\n\n"
        "Use `gta_search_interventions` to find the substantively important interventions:\n"
        f"4. Search with the same filters used above, sorted by most recent\n"
        "5. Triage the overview results — identify the most significant measures by:\n"
        "   - Scale (number of affected countries/products)\n"
        "   - Recency (most recent announcements)\n"
        "   - Significance (evaluation, instrument type)\n"
        "6. Use `gta_get_intervention` on 3-5 key interventions to read their full text\n"
        "7. Summarise what these interventions actually do — the substance, not just metadata\n\n"
        "## Part 3: Synthesis\n\n"
        "Combine both dimensions into a coherent analytical narrative:\n"
        "- Open with the quantitative picture (scale, trend, composition)\n"
        "- Ground it in the qualitative evidence (what the key measures say and do)\n"
        "- Note any patterns: escalation, retaliation, sectoral concentration\n"
        "- Flag data caveats (publication lag, overcounting risks)\n\n"
        "Include the Reference List from the search/get results at the end."
    )


# ============================================================================
# MCP Resources - Reference Data
# ============================================================================

@mcp.resource(
    "gta://reference/jurisdictions",
    name="GTA Jurisdictions Reference",
    description="Complete table of GTA jurisdictions with UN codes, ISO codes, and names. Use this to look up country codes and convert between ISO and UN formats.",
    mime_type="text/markdown"
)
def get_jurisdictions_reference() -> str:
	"""Return complete jurisdiction reference table.

	Returns:
		Markdown table with all jurisdictions, their UN codes, ISO codes, and names
	"""
	return load_jurisdictions_table()


@mcp.resource(
    "gta://reference/intervention-types",
    name="GTA Intervention Types Reference",
    description="Comprehensive descriptions of all GTA intervention types with examples, definitions, and MAST classifications. Use this to understand what different intervention types mean.",
    mime_type="text/markdown"
)
def get_intervention_types_reference() -> str:
	"""Return complete intervention type descriptions.

	Returns:
		Markdown document with all intervention type descriptions
	"""
	return load_intervention_types()


@mcp.resource(
    "gta://reference/intervention-types-list",
    name="List of Available Intervention Types",
    description="Quick reference list of all available intervention type names and their slugs. Use this to discover what intervention types exist.",
    mime_type="text/markdown"
)
def get_intervention_types_list() -> str:
	"""Return list of available intervention types.

	Returns:
		Formatted list of intervention type names with slugs
	"""
	return list_available_intervention_types()


@mcp.resource(
    "gta://jurisdiction/{iso_code}",
    name="Jurisdiction Lookup by ISO Code",
    description="Look up detailed information for a specific jurisdiction using its ISO 3-letter code (e.g., USA, CHN, DEU, GBR). Returns UN code, full name, short name, and adjective form.",
    mime_type="text/plain"
)
def get_jurisdiction(iso_code: str) -> str:
	"""Look up jurisdiction details by ISO code.

	Args:
		iso_code: ISO 3-letter country code (e.g., USA, CHN, DEU)

	Returns:
		Formatted jurisdiction details or error message
	"""
	result = parse_jurisdiction_by_iso(iso_code)
	return result if result else f"Jurisdiction '{iso_code}' not found"


@mcp.resource(
    "gta://intervention-type/{type_slug}",
    name="Intervention Type Details",
    description="Look up detailed information about a specific GTA intervention type using its slug (e.g., export-ban, import-tariff, state-loan). Returns description, examples, and MAST classification.",
    mime_type="text/markdown"
)
def get_intervention_type(type_slug: str) -> str:
	"""Look up intervention type details by slug.

	Args:
		type_slug: Slugified intervention type name (e.g., export-ban, import-tariff)

	Returns:
		Markdown section with intervention type details or error message
	"""
	result = parse_intervention_type(type_slug)
	return result if result else f"Intervention type '{type_slug}' not found"


@mcp.resource(
    "gta://guide/searching",
    name="Guide: How to Search the GTA Database",
    description="Comprehensive guide to searching the GTA database effectively. Explains default sorting behavior, how to find recent data, common search patterns, and troubleshooting tips. READ THIS if you're having trouble finding recent interventions or getting unexpected results.",
    mime_type="text/markdown"
)
def get_search_guide() -> str:
	"""Return complete search guide with best practices.

	Returns:
		Markdown document with search guidance and examples
	"""
	return load_search_guide()


@mcp.resource(
    "gta://guide/date-fields",
    name="Guide: Understanding GTA Date Fields",
    description="Detailed explanation of GTA date fields (announcement_date, inception_date, removal_date, last_update_date). Explains which date field to use for different types of searches and common mistakes to avoid. Essential for understanding the difference between when policies are announced vs. when they take effect.",
    mime_type="text/markdown"
)
def get_date_fields_guide() -> str:
	"""Return complete date fields guide.

	Returns:
		Markdown document explaining GTA date fields
	"""
	return load_date_fields_guide()


@mcp.resource(
    "gta://reference/sectors-list",
    name="Reference: CPC Sector Classification List",
    description="Complete list of all CPC (Central Product Classification) sectors with IDs and names. Includes goods (ID < 500) and services (ID >= 500). Use this to find sector codes for filtering interventions by broad product categories or services. Supports fuzzy name matching when used in queries.",
    mime_type="text/markdown"
)
def get_sectors_list() -> str:
	"""Return complete list of CPC sectors.

	Returns:
		Markdown table with all CPC sectors, IDs, and categories
	"""
	return load_sectors_table()


@mcp.resource(
    "gta://guide/cpc-vs-hs",
    name="Guide: CPC Sectors vs HS Codes - When to Use Which",
    description="Comprehensive guide explaining the difference between CPC sectors and HS codes, when to use each classification system, and practical examples. Essential for understanding how to query services (which REQUIRE CPC sectors) and when to use broad sector categories vs specific HS product codes.",
    mime_type="text/markdown"
)
def get_cpc_vs_hs_guide() -> str:
	"""Return guide comparing CPC sectors and HS codes.

	Returns:
		Markdown document explaining CPC vs HS classification
	"""
	return load_cpc_vs_hs_guide()


@mcp.resource(
    "gta://reference/eligible-firms",
    name="Reference: Eligible Firms Types",
    description="Complete list of eligible firm classifications with IDs and descriptions. Use this to filter interventions by target firms (all, SMEs, firm-specific, state-controlled, sector-specific, location-specific, processing trade). Essential for understanding policy scope and identifying SME-specific programs or company-targeted incentives.",
    mime_type="text/markdown"
)
def get_eligible_firms_list() -> str:
	"""Return complete list of eligible firm types.

	Returns:
		Markdown table with all eligible firm types, IDs, and descriptions
	"""
	return load_eligible_firms_table()


@mcp.resource(
    "gta://reference/implementation-levels",
    name="Reference: Implementation Levels",
    description="Complete list of implementation level classifications with IDs and descriptions. Use this to filter interventions by governmental authority level (Supranational, National, Subnational, SEZ, IFI, NFI). Essential for distinguishing EU-wide measures from national policies, or identifying development bank programs vs central government actions.",
    mime_type="text/markdown"
)
def get_implementation_levels_list() -> str:
	"""Return complete list of implementation levels.

	Returns:
		Markdown table with all implementation levels, IDs, and descriptions
	"""
	return load_implementation_levels_table()


@mcp.resource(
    "gta://guide/parameters",
    name="Guide: Search Parameters Reference",
    description="Comprehensive reference for all gta_search_interventions parameters. Explains each parameter's purpose, when to use it, format, and provides examples. Includes parameter selection strategy and common combinations. Essential for understanding filter options and constructing effective queries.",
    mime_type="text/markdown"
)
def get_parameters_guide() -> str:
	"""Return comprehensive parameters reference guide.

	Returns:
		Markdown document with all parameter descriptions and usage guidance
	"""
	return load_parameters_guide()


@mcp.resource(
    "gta://guide/query-examples",
    name="Guide: Query Examples Library",
    description="Comprehensive collection of 35+ real-world query examples organized by category (basic filtering, MAST chapters, entity searches, CPC sectors, firm targeting, negative queries, advanced combinations). Each example includes use case, explanation, and when to use it. Essential for learning query patterns and constructing effective searches.",
    mime_type="text/markdown"
)
def get_query_examples() -> str:
	"""Return comprehensive query examples library.

	Returns:
		Markdown document with categorized query examples and patterns
	"""
	return load_query_examples()


@mcp.resource(
	"gta://reference/mast-chapters",
	name="Reference: MAST Chapter Taxonomy",
	description="Complete UN MAST chapter classification (A-P) for non-tariff measures. Includes detailed descriptions, use cases, examples, and decision guidance for when to use MAST chapters vs intervention_types. Essential for understanding broad policy categorization from import quotas to subsidies, localization requirements, investment actions, and beyond.",
	mime_type="text/markdown"
)
def get_mast_chapters() -> str:
	"""Return comprehensive MAST chapter taxonomy and reference.

	Returns:
		Markdown document with complete A-P taxonomy, special categories, and usage guide
	"""
	return load_mast_chapters()


@mcp.resource(
	"gta://guide/query-syntax",
	name="Guide: Query Syntax and Strategy",
	description="Complete guide to query parameter usage including the 3-step strategy cascade, syntax reference (operators, wildcards, boolean logic), common mistakes and corrections, and advanced patterns. Essential for understanding when and how to use the query parameter effectively for entity searches.",
	mime_type="text/markdown"
)
def get_query_syntax() -> str:
	"""Return comprehensive query syntax and strategy guide.

	Returns:
		Markdown document with query strategy, syntax reference, examples, and best practices
	"""
	return load_query_syntax()


@mcp.resource(
	"gta://guide/exclusion-filters",
	name="Guide: Exclusion Filters (keep_* parameters)",
	description="Complete guide to GTA's inclusion/exclusion filter logic using keep_* parameters. Covers all 11 keep parameters, how True/False logic works, common patterns (exclude G7, non-tariff measures, universal policies), and troubleshooting. Essential for 'everything EXCEPT' queries.",
	mime_type="text/markdown"
)
def get_exclusion_filters() -> str:
	"""Return comprehensive exclusion filters guide.

	Returns:
		Markdown document with keep_* parameter reference, patterns, and examples
	"""
	return load_exclusion_filters()


@mcp.resource(
	"gta://guide/data-model",
	name="Guide: GTA Data Model",
	description="Explains the GTA data hierarchy: State Acts (government announcements) contain one or more Interventions (specific policy measures). Covers counting units (intervention_id vs state_act_id) and the product/sector relationship. Essential for understanding what you're counting and avoiding overcounting.",
	mime_type="text/markdown"
)
def get_data_model_guide() -> str:
	"""Return data model guide explaining GTA hierarchy and counting units.

	Returns:
		Markdown document with data model explanation
	"""
	return load_data_model_guide()


@mcp.resource(
	"gta://guide/analytical-caveats",
	name="Guide: Analytical Caveats (Critical)",
	description="15 critical caveats distilled from the GTA analytical configuration (549 rules). Covers: evaluation filter-only values (4/5 are groupings), Amber = likely harmful, India code 699 anomaly, MAST non-alphabetical IDs, what's NOT in the database, overcounting by sector/product, date semantics, publication lag, EU jurisdiction complexity, trade defence lifecycle, and more. READ THIS before interpreting GTA results.",
	mime_type="text/markdown"
)
def get_analytical_caveats() -> str:
	"""Return analytical caveats guide with critical interpretation rules.

	Returns:
		Markdown document with 15 critical caveats
	"""
	return load_analytical_caveats()


@mcp.resource(
	"gta://guide/common-mistakes",
	name="Guide: Common Mistakes When Using GTA Data",
	description="Quick-reference DO/DON'T checklist for agents. Covers evaluation filter usage, date field selection, counting pitfalls, database scope limitations, and data quality caveats. Consult before making analytical claims.",
	mime_type="text/markdown"
)
def get_common_mistakes() -> str:
	"""Return common mistakes checklist for GTA data analysis.

	Returns:
		Markdown document with DO/DON'T checklist
	"""
	return load_common_mistakes()


@mcp.resource(
	"gta://reference/glossary",
	name="Reference: GTA Glossary",
	description="Definitions of key GTA terminology for non-expert users. Covers: Red/Amber/Green evaluations, interventions vs state acts, MAST chapters, HS codes vs CPC sectors, implementation levels, eligible firms, publication lag, date semantics, and more. Essential for understanding GTA data without prior trade policy expertise.",
	mime_type="text/markdown"
)
def get_glossary() -> str:
	"""Return GTA glossary for non-expert users.

	Returns:
		Markdown document defining key GTA terms
	"""
	return load_glossary()


@mcp.resource(
	"gta://guide/search-strategy",
	name="Guide: Multi-Pass Search Strategy",
	description="How to use detail_level and show_keys for efficient searching. Explains the overview→triage→detail workflow for handling large result sets, monitoring with update_period, and choosing the right detail level for different query types.",
	mime_type="text/markdown"
)
def get_search_strategy() -> str:
	"""Return search strategy guide for multi-pass workflow.

	Returns:
		Markdown guide explaining detail levels and search workflow
	"""
	return load_search_strategy()


@mcp.resource(
	"gta://reference/jurisdiction-groups",
	name="Reference: Jurisdiction Groups (G7, G20, EU, BRICS, ASEAN, CPTPP)",
	description="ISO and UN codes for major country groups. Use when a query mentions G7, G20, EU-27, BRICS, ASEAN, CPTPP, or RCEP to get the correct implementing_jurisdictions or affected_jurisdictions list. Includes ready-to-use ISO code arrays.",
	mime_type="text/markdown"
)
def get_jurisdiction_groups() -> str:
	"""Return jurisdiction groups reference with member codes.

	Returns:
		Markdown reference with ISO/UN codes for G7, G20, EU-27, BRICS, ASEAN, CPTPP, RCEP
	"""
	return load_jurisdiction_groups()


@mcp.resource(
	"gta://guide/query-intent-mapping",
	name="Guide: Natural Language to Structured Filters",
	description="Maps analytical concepts from natural language queries to GTA structured filters. Covers: policy types to MAST chapters (subsidies→L, export controls→P), evaluation terms (harmful→Red+Amber), commodity terms to HS code lookup, service terms to CPC sector lookup, geographic groups to jurisdiction codes, and temporal terms to date filters. READ THIS before translating user questions into API calls.",
	mime_type="text/markdown"
)
def get_query_intent_mapping() -> str:
	"""Return query intent mapping guide for translating NL to structured filters.

	Returns:
		Markdown guide mapping natural language terms to GTA structured filters
	"""
	return load_query_intent_mapping()


@mcp.resource(
	"gta://legal/privacy",
	name="Privacy Policy",
	description="Privacy policy for the GTA MCP server. Explains what data is collected, how it is used, and your rights. Reference this when users ask about data handling, privacy, or security.",
	mime_type="text/markdown"
)
def get_privacy_policy() -> str:
	"""Return the GTA MCP server privacy policy.

	Returns:
		Complete privacy policy as markdown
	"""
	return load_privacy_policy()


def main():
    """Entry point for running the GTA MCP server."""
    # Check for API key
    if not os.getenv("GTA_API_KEY"):
        print(
            "ERROR: GTA_API_KEY environment variable not set.\n"
            "Please set your API key before starting the server:\n"
            "  export GTA_API_KEY='your-key-here'\n"
            "  gta-mcp",
            file=sys.stderr
        )
        sys.exit(1)
    
    # Run the server with stdio transport (default for MCP)
    mcp.run()


if __name__ == "__main__":
    main()
