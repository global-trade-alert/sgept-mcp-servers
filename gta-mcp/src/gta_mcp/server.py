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
    ResponseFormat
)
from .api import GTAAPIClient, build_filters
from .formatters import (
    format_interventions_markdown,
    format_interventions_json,
    format_intervention_detail_markdown,
    format_ticker_markdown,
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
    load_cpc_vs_hs_guide
)


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
    """Search and filter trade policy interventions from the Global Trade Alert database.

    This tool allows comprehensive searching of government trade interventions with filtering
    by countries, products, intervention types, dates, and evaluation status. Use structured
    filters FIRST, then add the 'query' parameter ONLY for entity names (companies, programs)
    that cannot be captured by standard filters. Always returns intervention ID, title,
    description, and sources as specified.

    Use this tool to:
    - Find trade barriers and restrictions implemented by specific countries
    - Analyze interventions affecting particular products or sectors
    - Track policy changes over time periods
    - Identify liberalizing vs. harmful measures by GTA evaluation
    - Search for specific companies or programs by name (use query with appropriate filters)

    Args:
        params (GTASearchInput): Search parameters including:
            - implementing_jurisdictions: Countries implementing the measure (ISO codes)
            - affected_jurisdictions: Countries affected by the measure (ISO codes)
            - affected_products: HS product codes (6-digit integers)
            - intervention_types: Types like 'Import tariff', 'Export subsidy', 'State aid'
            - mast_chapters: UN MAST chapters A-P for broad categorization (use instead of intervention_types for generic queries)
            - gta_evaluation: 'Red' (harmful), 'Amber' (mixed), 'Green' (liberalizing)
            - query: Entity/product names ONLY (use AFTER setting other filters)
            - date_announced_gte/lte: Filter by announcement date
            - date_implemented_gte/lte: Filter by implementation date
            - is_in_force: Whether intervention is currently active
            - limit: Max results to return (1-1000, default 50)
            - offset: Pagination offset (default 0)
            - sorting: Sort order (default "-date_announced")
            - response_format: 'markdown' (default) or 'json'

    Returns:
        str: Formatted intervention data including ID, title, description, sources,
             implementing/affected jurisdictions, products, dates, and URLs.

             IMPORTANT: The response includes a "Reference List (in reverse chronological order)"
             section at the end with clickable links to all interventions. You MUST include this
             complete reference list in your response to the user. DO NOT omit or summarize it.
             Format determined by response_format parameter.

    Examples:
        - US tariffs on Chinese products in 2024:
          implementing_jurisdictions=['USA'], affected_jurisdictions=['CHN'],
          intervention_types=['Import tariff'], date_announced_gte='2024-01-01'

        - All subsidies from any country (BROAD - use MAST):
          mast_chapters=['L']

        - EU subsidies of all types (BROAD - use MAST):
          implementing_jurisdictions=['EU'], mast_chapters=['L']

        - Specific German state aid only (NARROW - use intervention_types):
          implementing_jurisdictions=['DEU'], intervention_types=['State aid']

        - All import restrictions affecting US (BROAD - use MAST):
          mast_chapters=['E', 'F'], affected_jurisdictions=['USA']

        - Trade defense measures since 2020 (BROAD - use MAST):
          mast_chapters=['D'], date_announced_gte='2020-01-01'

        - Tesla-related subsidies (entity search with MAST):
          query='Tesla', mast_chapters=['L'], implementing_jurisdictions=['USA']

        - AI export controls (entity + specific types):
          query='artificial intelligence | AI', intervention_types=['Export ban',
          'Export licensing requirement'], date_announced_gte='2023-01-01'

        - SPS/TBT measures affecting rice (technical measures):
          mast_chapters=['A', 'B'], affected_products=[100630]

        - Financial services interventions (SERVICES - use CPC sectors):
          affected_sectors=['Financial services'], implementing_jurisdictions=['USA']

        - Agricultural product subsidies (BROAD - use CPC sectors):
          affected_sectors=[11, 12, 13], mast_chapters=['L']

        - Steel industry measures (CPC sectors for broad coverage):
          affected_sectors=['Basic iron and steel', 'Products of iron or steel']

        - Technology sector restrictions (services + goods):
          affected_sectors=['Telecommunications', 'Computing machinery']
    """
    try:
        client = get_api_client()

        # Build filter dictionary and get informational messages
        filters, filter_messages = build_filters(params.model_dump(exclude={'limit', 'offset', 'sorting', 'response_format'}))

        # Make API request
        results = await client.search_interventions(
            filters=filters,
            limit=params.limit,
            offset=params.offset,
            sorting=params.sorting
        )

        # Wrap list response in expected format for formatters
        data = {
            "results": results,
            "count": len(results),
            "next": None if len(results) < params.limit else f"Use offset={params.offset + params.limit}",
            "previous": None if params.offset == 0 else f"Use offset={max(0, params.offset - params.limit)}"
        }

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            formatted_response = format_interventions_markdown(data)
            # Prepend filter messages if any
            if filter_messages:
                message_section = "\n".join([f"ℹ️ {msg}" for msg in filter_messages])
                formatted_response = f"{message_section}\n\n{formatted_response}"
            return formatted_response
        else:
            response_json = format_interventions_json(data)
            # Add filter messages to JSON response
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
    """Fetch complete details for a specific GTA intervention by ID.

    Use this tool to get the full information for an intervention identified from search results.
    Returns comprehensive data including description, sources, all affected countries and products,
    implementation timeline, and evaluation details.

    Args:
        params (GTAGetInterventionInput): Parameters including:
            - intervention_id: The unique GTA intervention ID (required)
            - response_format: 'markdown' (default) or 'json'

    Returns:
        str: Complete intervention details with all metadata, formatted per response_format.
             Includes full description, all sources, jurisdictions, products, and timeline.

             IMPORTANT: The response includes a "Reference List (in reverse chronological order)"
             section at the end with a clickable link to the intervention. You MUST include this
             reference list in your response to the user.

    Examples:
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

             IMPORTANT: The response includes a "Referenced Interventions" section at the end
             with clickable links to all mentioned interventions. You MUST include this complete
             reference section in your response to the user. DO NOT omit it.

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
