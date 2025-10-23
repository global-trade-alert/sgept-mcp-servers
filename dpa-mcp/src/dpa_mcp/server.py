"""DPA MCP Server - Exposes Digital Policy Alert database via MCP protocol."""

import os
import sys
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP

from .models import (
	DPASearchInput,
	DPAGetEventInput,
	ResponseFormat
)
from .api import DPAAPIClient, build_filters
from .formatters import (
	format_events_markdown,
	format_events_json,
	format_event_detail_markdown,
	CHARACTER_LIMIT
)
from .resources_loader import (
	load_jurisdictions_table,
	load_economic_activities,
	load_policy_areas,
	load_event_types,
	load_action_types,
	load_intervention_types,
	load_handbook,
	parse_jurisdiction_by_iso,
	parse_economic_activity,
	list_available_economic_activities,
	list_available_policy_areas,
	list_available_event_types,
	list_available_action_types
)


# Initialize MCP server
mcp = FastMCP("dpa_mcp")


def get_api_client() -> DPAAPIClient:
	"""Get initialized DPA API client with API key from environment."""
	api_key = os.getenv("DPA_API_KEY")
	if not api_key:
		raise ValueError(
			"DPA_API_KEY environment variable not set. "
			"Please set your API key: export DPA_API_KEY='your-key-here'"
		)
	return DPAAPIClient(api_key)


@mcp.tool(
	name="dpa_search_events",
	annotations={
		"title": "Search DPA Digital Policy Events",
		"readOnlyHint": True,
		"destructiveHint": False,
		"idempotentHint": True,
		"openWorldHint": True
	}
)
async def dpa_search_events(params: DPASearchInput) -> str:
	"""Search and filter digital policy events from the Digital Policy Alert database.

	This tool allows comprehensive searching of government digital policy events with filtering
	by countries, economic activities, policy areas, event types, dates, and more. Always returns
	event ID, title, description, and details as specified.

	Use this tool to:
	- Find digital policy regulations and laws by specific countries
	- Analyze policies affecting particular economic activities or sectors
	- Track policy changes over time periods
	- Identify binding vs. non-binding regulatory measures

	Args:
		params (DPASearchInput): Search parameters including:
			- implementing_jurisdictions: Countries implementing the policy (ISO codes)
			- economic_activities: Digital sectors affected (e.g., 'ML and AI development', 'platform intermediary: user-generated content')
			- policy_areas: Policy domains (e.g., 'Data governance', 'Content moderation', 'Competition')
			- event_types: Types like 'law', 'order', 'decision', 'investigation'
			- government_branch: Branch responsible ('legislature', 'executive', 'judiciary')
			- dpa_implementation_level: Scope of implementation
			- event_period_start/end: Filter by event date
			- limit: Max results to return (1-1000, default 50)
			- offset: Pagination offset (default 0)
			- response_format: 'markdown' (default) or 'json'

	Returns:
		str: Formatted event data including ID, title, description, implementers,
			 policy classification, economic activities, dates, and URLs.

			 IMPORTANT: The response includes a "Reference List (in reverse chronological order)"
			 section at the end with clickable links to all events. You MUST include this
			 complete reference list in your response to the user. DO NOT omit or summarize it.
			 Format determined by response_format parameter.

	Examples:
		- Search for EU AI regulations announced in 2024
		- Find all data governance policies affecting cloud computing
		- Track recent content moderation laws from the US
	"""
	try:
		client = get_api_client()

		# Build filter dictionary
		filters = build_filters(params.model_dump(exclude={'limit', 'offset', 'sorting', 'response_format'}))

		# Make API request
		results = await client.search_events(
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
			return format_events_markdown(data)
		else:
			return format_events_json(data)

	except ValueError as e:
		return f"❌ Configuration Error: {str(e)}\n\nPlease ensure DPA_API_KEY is set in your environment."
	except Exception as e:
		error_msg = str(e)
		if "401" in error_msg or "403" in error_msg:
			return (
				"❌ Authentication Error: Invalid or expired API key.\n\n"
				"Please check your DPA_API_KEY environment variable."
			)
		elif "404" in error_msg:
			return "❌ API endpoint not found. The DPA API structure may have changed."
		elif "timeout" in error_msg.lower():
			return (
				"❌ Request timeout: The API took too long to respond.\n\n"
				"Try reducing the limit parameter or adding more specific filters."
			)
		else:
			return f"❌ API Error: {error_msg}\n\nTry adjusting your search parameters or contact support."


@mcp.tool(
	name="dpa_get_event",
	annotations={
		"title": "Get Detailed DPA Event",
		"readOnlyHint": True,
		"destructiveHint": False,
		"idempotentHint": True,
		"openWorldHint": True
	}
)
async def dpa_get_event(params: DPAGetEventInput) -> str:
	"""Fetch complete details for a specific DPA event by ID.

	Use this tool to get the full information for an event identified from search results.
	Returns comprehensive data including description, implementers, policy classification,
	economic activities, and timeline.

	Args:
		params (DPAGetEventInput): Parameters including:
			- event_id: The unique DPA event ID (required)
			- response_format: 'markdown' (default) or 'json'

	Returns:
		str: Complete event details with all metadata, formatted per response_format.
			 Includes full description, implementers, policy classification, and timeline.

			 IMPORTANT: The response includes a "Reference List (in reverse chronological order)"
			 section at the end with a clickable link to the event. You MUST include this
			 reference list in your response to the user.

	Examples:
		- Get full details for event 20442 (Singapore AI Governance Framework)
		- Fetch complete information for a specific digital policy measure
	"""
	try:
		client = get_api_client()

		# Fetch event
		event = await client.get_event(params.event_id)

		# Wrap single event in expected format for formatters
		data = {"results": [event]}

		# Format response
		if params.response_format == ResponseFormat.MARKDOWN:
			return format_event_detail_markdown(data)
		else:
			return format_events_json(data)

	except ValueError as e:
		if "not found" in str(e):
			return f"❌ Event {params.event_id} not found in DPA database."
		return f"❌ Error: {str(e)}"
	except Exception as e:
		error_msg = str(e)
		if "401" in error_msg or "403" in error_msg:
			return "❌ Authentication Error: Invalid or expired API key."
		else:
			return f"❌ API Error: {error_msg}"


# ============================================================================
# MCP Resources - Reference Data
# ============================================================================

@mcp.resource(
	"dpa://reference/jurisdictions",
	name="DPA Jurisdictions Reference",
	description="Complete table of DPA jurisdictions with jurisdiction IDs, ISO codes, and names. Use this to look up country codes and convert between ISO and DPA ID formats.",
	mime_type="text/markdown"
)
def get_jurisdictions_reference() -> str:
	"""Return complete jurisdiction reference table.

	Returns:
		Markdown table with all jurisdictions, their IDs, ISO codes, and names
	"""
	return load_jurisdictions_table()


@mcp.resource(
	"dpa://reference/economic-activities",
	name="DPA Economic Activities Reference",
	description="Complete list of digital economic activities tracked by DPA with descriptions. Use this to understand what economic sectors are covered.",
	mime_type="text/markdown"
)
def get_economic_activities_reference() -> str:
	"""Return complete economic activities list.

	Returns:
		Markdown table with all economic activities
	"""
	return load_economic_activities()


@mcp.resource(
	"dpa://reference/policy-areas",
	name="DPA Policy Areas Reference",
	description="Complete list of policy areas (legal domains) tracked by DPA. Use this to understand the different areas of digital policy.",
	mime_type="text/markdown"
)
def get_policy_areas_reference() -> str:
	"""Return complete policy areas list.

	Returns:
		Markdown table with all policy areas
	"""
	return load_policy_areas()


@mcp.resource(
	"dpa://reference/event-types",
	name="DPA Event Types Reference",
	description="Complete list of event types with binding/non-binding status. Use this to understand different types of regulatory actions.",
	mime_type="text/markdown"
)
def get_event_types_reference() -> str:
	"""Return complete event types list.

	Returns:
		Markdown table with all event types
	"""
	return load_event_types()


@mcp.resource(
	"dpa://reference/action-types",
	name="DPA Action Types Reference",
	description="Complete list of action types representing policy lifecycle stages. Use this to understand the progression of regulatory changes.",
	mime_type="text/markdown"
)
def get_action_types_reference() -> str:
	"""Return complete action types list.

	Returns:
		Markdown table with all action types
	"""
	return load_action_types()


@mcp.resource(
	"dpa://reference/intervention-types",
	name="DPA Policy Instruments Reference",
	description="Complete list of policy instruments (intervention types) with descriptions. Use this to understand different regulatory tools used in digital policy.",
	mime_type="text/markdown"
)
def get_intervention_types_reference() -> str:
	"""Return complete intervention types (policy instruments) list.

	Returns:
		Markdown table with all intervention types
	"""
	return load_intervention_types()


@mcp.resource(
	"dpa://reference/economic-activities-list",
	name="List of Available Economic Activities",
	description="Quick reference list of all available economic activity names and slugs. Use this to discover what economic activities exist.",
	mime_type="text/markdown"
)
def get_economic_activities_list() -> str:
	"""Return list of available economic activities.

	Returns:
		Formatted list of economic activity names with slugs
	"""
	return list_available_economic_activities()


@mcp.resource(
	"dpa://reference/policy-areas-list",
	name="List of Available Policy Areas",
	description="Quick reference list of all available policy area names. Use this to discover what policy areas exist.",
	mime_type="text/markdown"
)
def get_policy_areas_list() -> str:
	"""Return list of available policy areas.

	Returns:
		Formatted list of policy area names
	"""
	return list_available_policy_areas()


@mcp.resource(
	"dpa://reference/event-types-list",
	name="List of Available Event Types",
	description="Quick reference list of all available event type names. Use this to discover what event types exist.",
	mime_type="text/markdown"
)
def get_event_types_list() -> str:
	"""Return list of available event types.

	Returns:
		Formatted list of event type names
	"""
	return list_available_event_types()


@mcp.resource(
	"dpa://reference/action-types-list",
	name="List of Available Action Types",
	description="Quick reference list of all available action type names. Use this to discover what action types exist.",
	mime_type="text/markdown"
)
def get_action_types_list() -> str:
	"""Return list of available action types.

	Returns:
		Formatted list of action type names
	"""
	return list_available_action_types()


@mcp.resource(
	"dpa://guide/handbook",
	name="DPA Activity Tracking Handbook",
	description="Complete DPA Activity Tracking Handbook explaining the methodology, taxonomy, and best practices for using DPA data. Essential reading for understanding DPA's approach to digital policy tracking.",
	mime_type="text/markdown"
)
def get_handbook() -> str:
	"""Return complete DPA Activity Tracking Handbook.

	Returns:
		Markdown document with handbook content
	"""
	return load_handbook()


@mcp.resource(
	"dpa://jurisdiction/{iso_code}",
	name="Jurisdiction Lookup by ISO Code",
	description="Look up detailed information for a specific jurisdiction using its ISO 3-letter code (e.g., USA, CHN, DEU, GBR). Returns DPA ID, full name, short name, and adjective form.",
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
	"dpa://economic-activity/{activity_slug}",
	name="Economic Activity Details",
	description="Look up detailed information about a specific economic activity using its slug (e.g., ml-and-ai-development, platform-intermediary-user-generated-content). Returns ID, name, and description.",
	mime_type="text/plain"
)
def get_economic_activity(activity_slug: str) -> str:
	"""Look up economic activity details by slug.

	Args:
		activity_slug: Slugified economic activity name (e.g., ml-and-ai-development)

	Returns:
		Formatted economic activity details or error message
	"""
	result = parse_economic_activity(activity_slug)
	return result if result else f"Economic activity '{activity_slug}' not found"


def main():
	"""Entry point for running the DPA MCP server."""
	# Check for API key
	if not os.getenv("DPA_API_KEY"):
		print(
			"ERROR: DPA_API_KEY environment variable not set.\n"
			"Please set your API key before starting the server:\n"
			"  export DPA_API_KEY='your-key-here'\n"
			"  dpa-mcp",
			file=sys.stderr
		)
		sys.exit(1)

	# Run the server with stdio transport (default for MCP)
	mcp.run()


if __name__ == "__main__":
	main()
