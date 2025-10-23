"""Response formatting utilities for DPA MCP server."""

import json
from typing import Dict, Any, List


CHARACTER_LIMIT = 25000  # Maximum response size in characters


def extract_text(field: Any) -> str:
	"""Safely extract text from a field that might be a string or other type.

	Args:
		field: The field value (string or other)

	Returns:
		Extracted text string, or empty string if extraction fails
	"""
	if not field:
		return ''

	if isinstance(field, str):
		return field

	# Fallback for unexpected types
	return str(field) if field else ''


def make_dpa_url(event_id: int) -> str:
	"""Generate DPA event URL.

	Args:
		event_id: The event ID

	Returns:
		Full URL to DPA event page
	"""
	return f"https://digitalpolicyalert.org/event/{event_id}"


def make_inline_citation(event_id: int) -> str:
	"""Generate inline citation with clickable link.

	Args:
		event_id: The event ID

	Returns:
		Markdown inline citation: [ID [12345](url)]
	"""
	url = make_dpa_url(event_id)
	return f"[ID [{event_id}]({url})]"


def make_reference_entry(event_id: int, title: str, date: str) -> str:
	"""Generate reference list entry.

	Args:
		event_id: The event ID
		title: Event title
		date: Event date (YYYY-MM-DD format)

	Returns:
		Markdown reference: - 2024-10-23: Title [ID [12345](url)].
	"""
	citation = make_inline_citation(event_id)
	return f"- {date}: {title} {citation}."


def make_references_section(events: List[Dict[str, Any]]) -> str:
	"""Generate complete references section.

	Args:
		events: List of event dictionaries with id, title, date

	Returns:
		Markdown references section with all cited events sorted by date
	"""
	if not events:
		return ""

	# Sort by date (newest first, reverse chronological)
	sorted_events = sorted(
		events,
		key=lambda x: x.get('date', '2000-01-01'),
		reverse=True
	)

	references = ["## Reference List (in reverse chronological order)\n"]
	for event in sorted_events:
		event_id = event.get('id')
		title = event.get('title', 'Untitled')
		date = event.get('date', 'Unknown date')

		if event_id:
			references.append(make_reference_entry(event_id, title, date))

	return "\n".join(references)


def format_events_markdown(data: Dict[str, Any]) -> str:
	"""Format digital policy event search results as markdown.

	Args:
		data: API response data containing events

	Returns:
		Markdown-formatted string
	"""
	results = data.get("results", [])
	count = data.get("count", 0)
	total = len(results)

	output = []

	# Header with pagination info
	output.append(f"# DPA Digital Policy Events ({count} total)\n")

	if data.get("next"):
		output.append("📄 **More results available** - use `offset` parameter to paginate\n")

	# Format each event
	for i, event in enumerate(results, 1):
		event_id = event.get('id')
		title = event.get('title', 'Untitled')
		citation = make_inline_citation(event_id) if event_id else ""
		output.append(f"## {i}. {title} {citation}\n")
		output.append(f"**Event ID**: {event_id}")
		output.append(f"**Date**: {event.get('date', 'N/A')}")
		output.append(f"**Status**: {event.get('status', 'N/A')}")
		output.append(f"**Event Type**: {event.get('event_type', 'N/A')}")
		output.append(f"**Action Type**: {event.get('action_type', 'N/A')}\n")

		# Implementers
		implementers = event.get('implementers', [])
		if implementers:
			impl_names = [impl.get('name') for impl in implementers if impl.get('name')]
			output.append(f"**Implementers**: {', '.join(impl_names)}")

		# Implementer groups
		implementer_groups = event.get('implementer_groups', [])
		if implementer_groups:
			group_names = [g.get('name') for g in implementer_groups if g.get('name')]
			output.append(f"**Implementer Groups**: {', '.join(group_names)}")

		# Policy area and instrument
		policy_area = event.get('policy_area', 'N/A')
		policy_instrument = event.get('policy_instrument', 'N/A')
		output.append(f"**Policy Area**: {policy_area}")
		output.append(f"**Policy Instrument**: {policy_instrument}")

		# Economic activities (limit to first 5)
		economic_activities = event.get('economic_activities', [])
		if economic_activities:
			activity_names = [act.get('name') for act in economic_activities[:5] if act.get('name')]
			suffix = f" (+{len(economic_activities) - 5} more)" if len(economic_activities) > 5 else ""
			output.append(f"**Economic Activities**: {', '.join(activity_names)}{suffix}")

		# Implementation level
		impl_level = event.get('implementation_level', 'N/A')
		output.append(f"**Implementation Level**: {impl_level}")

		# Description (truncate)
		description = event.get('description')
		if description:
			desc_text = extract_text(description)
			if desc_text:
				# Truncate long descriptions
				if len(desc_text) > 300:
					desc_text = desc_text[:297] + "..."
				output.append(f"\n**Description**: {desc_text}")

		# URLs
		output.append(f"\n🔗 [View on DPA]({event.get('url')})")

		output.append("\n---\n")

	# Add references section
	output.append("\n")
	output.append("---\n")
	output.append("**Note:** The reference list below MUST be included in your response to provide clickable links for verification.\n")
	output.append(make_references_section(results))

	result = "\n".join(output)

	# Check character limit
	if len(result) > CHARACTER_LIMIT:
		truncated_count = total // 2
		return format_events_markdown({
			"count": count,
			"results": results[:truncated_count],
			"next": data.get("next"),
			"truncated": True
		}) + f"\n\n⚠️ **Response truncated**: Showing {truncated_count} of {total} events. Use `offset` or add filters to see more."

	return result


def format_events_json(data: Dict[str, Any]) -> str:
	"""Format digital policy event search results as JSON.

	Args:
		data: API response data containing events

	Returns:
		JSON-formatted string
	"""
	# Return full API response
	result = json.dumps(data, indent=2, ensure_ascii=False)

	# Check character limit
	if len(result) > CHARACTER_LIMIT:
		# Truncate results array
		truncated_data = data.copy()
		original_count = len(data.get("results", []))
		truncated_count = original_count // 2
		truncated_data["results"] = data["results"][:truncated_count]
		truncated_data["truncated"] = True
		truncated_data["truncation_message"] = (
			f"Response truncated from {original_count} to {truncated_count} items. "
			f"Use 'offset' parameter or add filters to see more results."
		)
		result = json.dumps(truncated_data, indent=2, ensure_ascii=False)

	return result


def format_event_detail_markdown(data: Dict[str, Any]) -> str:
	"""Format single event detail as markdown.

	Args:
		data: API response containing single event

	Returns:
		Markdown-formatted string
	"""
	results = data.get("results", [])
	if not results:
		return "❌ Event not found"

	event = results[0]

	output = []
	event_id = event.get('id')
	title = event.get('title', 'Untitled')
	citation = make_inline_citation(event_id) if event_id else ""
	output.append(f"# {title} {citation}\n")
	output.append(f"**Event ID**: {event_id}")
	output.append(f"**Date**: {event.get('date', 'N/A')}")
	output.append(f"**Status**: {event.get('status', 'N/A')}")
	output.append(f"**Event Type**: {event.get('event_type', 'N/A')}")
	output.append(f"**Action Type**: {event.get('action_type', 'N/A')}")
	output.append(f"**Implementation Level**: {event.get('implementation_level', 'N/A')}\n")

	# Implementers
	output.append("## Implementers\n")
	implementers = event.get('implementers', [])
	implementer_groups = event.get('implementer_groups', [])

	if implementers:
		for impl in implementers:
			output.append(f"- {impl.get('name')} ({impl.get('id')})")
	if implementer_groups:
		for group in implementer_groups:
			output.append(f"- **{group.get('name')}** (group)")
	if not implementers and not implementer_groups:
		output.append("- Not specified")
	output.append("")

	# Policy Classification
	output.append("## Policy Classification\n")
	output.append(f"**Policy Area**: {event.get('policy_area', 'N/A')}")
	output.append(f"**Policy Instrument**: {event.get('policy_instrument', 'N/A')}\n")

	# Economic Activities
	economic_activities = event.get('economic_activities', [])
	if economic_activities:
		output.append("## Economic Activities\n")
		for activity in economic_activities:
			output.append(f"- {activity.get('name')} (ID: {activity.get('id')})")
		output.append("")

	# Description
	description = event.get('description')
	if description:
		output.append("## Description\n")
		desc_text = extract_text(description)
		if desc_text:
			output.append(desc_text)
			output.append("")

	# URLs
	output.append("## Links\n")
	output.append(f"- [View on DPA]({event.get('url')})")

	# Add references section
	output.append("\n")
	output.append("---\n")
	output.append("**Note:** The reference list below MUST be included in your response to provide clickable links for verification.\n")
	output.append(make_references_section([event]))

	return "\n".join(output)
