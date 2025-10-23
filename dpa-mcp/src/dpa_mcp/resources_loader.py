"""Resource loading and parsing utilities for DPA MCP server."""

import os
import re
from pathlib import Path
from typing import Dict, Optional


# Cache for loaded resources
_CACHE: Dict[str, str] = {}


def get_resources_dir() -> Path:
	"""Get the path to the resources directory."""
	# Resources are in the project root, not in src/
	current_file = Path(__file__)
	project_root = current_file.parent.parent.parent
	return project_root / "resources"


def load_jurisdictions_table() -> str:
	"""Load the complete jurisdictions table from markdown file.

	Returns:
		Complete markdown table content
	"""
	if "jurisdictions" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "dpa_jurisdictions.md"

		if not file_path.exists():
			return "Error: Jurisdictions resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["jurisdictions"] = f.read()

	return _CACHE["jurisdictions"]


def load_economic_activities() -> str:
	"""Load the complete economic activities list from markdown file.

	Returns:
		Complete markdown content with all economic activities
	"""
	if "economic_activities" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "dpa_economic_activity_list.md"

		if not file_path.exists():
			return "Error: Economic activities resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["economic_activities"] = f.read()

	return _CACHE["economic_activities"]


def load_policy_areas() -> str:
	"""Load the complete policy areas list from markdown file.

	Returns:
		Complete markdown content with all policy areas
	"""
	if "policy_areas" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "dpa_policy_area_list.md"

		if not file_path.exists():
			return "Error: Policy areas resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["policy_areas"] = f.read()

	return _CACHE["policy_areas"]


def load_event_types() -> str:
	"""Load the complete event types list from markdown file.

	Returns:
		Complete markdown content with all event types
	"""
	if "event_types" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "dpa_event_type_list.md"

		if not file_path.exists():
			return "Error: Event types resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["event_types"] = f.read()

	return _CACHE["event_types"]


def load_action_types() -> str:
	"""Load the complete action types list from markdown file.

	Returns:
		Complete markdown content with all action types
	"""
	if "action_types" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "dpa_action_type_list.md"

		if not file_path.exists():
			return "Error: Action types resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["action_types"] = f.read()

	return _CACHE["action_types"]


def load_intervention_types() -> str:
	"""Load the complete intervention types (policy instruments) list from markdown file.

	Returns:
		Complete markdown content with all intervention types
	"""
	if "intervention_types" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "dpa_intervention_type_list.md"

		if not file_path.exists():
			return "Error: Intervention types resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["intervention_types"] = f.read()

	return _CACHE["intervention_types"]


def load_handbook() -> str:
	"""Load the DPA Activity Tracking Handbook from markdown file.

	Returns:
		Complete markdown content of the handbook
	"""
	if "handbook" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "dpa_activity_tracking_handbook.md"

		if not file_path.exists():
			return "Error: Handbook resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["handbook"] = f.read()

	return _CACHE["handbook"]


def parse_jurisdiction_by_iso(iso_code: str) -> Optional[str]:
	"""Parse jurisdiction table and find entry by ISO code.

	Args:
		iso_code: ISO 3-letter country code (e.g., USA, CHN, DEU)

	Returns:
		Formatted string with jurisdiction details or None if not found
	"""
	table = load_jurisdictions_table()

	if table.startswith("Error:"):
		return table

	# Normalize ISO code
	iso_upper = iso_code.upper().strip()

	# Parse table line by line
	lines = table.strip().split('\n')

	# Skip header and separator
	for line in lines[2:]:
		if not line.strip():
			continue

		# Split by pipe and clean
		parts = [p.strip() for p in line.split('|')]

		# Table format: |jurisdiction_id|jurisdiction_name|gta_jurisdiction_id|iso_code|...
		if len(parts) >= 10:
			jurisdiction_id = parts[1]
			jurisdiction_name = parts[2]
			gta_jurisdiction_id = parts[3]
			iso = parts[4]
			jurisdiction_name_short = parts[5]
			jurisdiction_name_adj = parts[6]

			if iso == iso_upper:
				return f"""Jurisdiction: {jurisdiction_name}
DPA Jurisdiction ID: {jurisdiction_id}
ISO Code: {iso}
GTA Jurisdiction ID: {gta_jurisdiction_id}
Short Name: {jurisdiction_name_short}
Adjective Form: {jurisdiction_name_adj}"""

	return f"Jurisdiction with ISO code '{iso_code}' not found. Please use a valid ISO 3-letter code (e.g., USA, CHN, DEU, GBR)."


def parse_economic_activity(activity_slug: str) -> Optional[str]:
	"""Parse economic activities and extract section for specific activity.

	Args:
		activity_slug: Slugified economic activity name (e.g., ml-and-ai-development)

	Returns:
		Formatted string with economic activity details or None if not found
	"""
	content = load_economic_activities()

	if content.startswith("Error:"):
		return content

	# Normalize slug
	slug = activity_slug.lower().strip().replace('_', '-')

	# Parse table line by line
	lines = content.strip().split('\n')

	# Skip header and separator
	for line in lines[2:]:
		if not line.strip():
			continue

		# Split by pipe and clean
		parts = [p.strip() for p in line.split('|')]

		# Table format: |economic_activity_id|economic_activity_name|slug|...
		if len(parts) >= 5:
			activity_id = parts[1]
			activity_name = parts[2]
			activity_slug_table = parts[3]
			activity_description = parts[5]

			if activity_slug_table == slug:
				return f"""Economic Activity: {activity_name}
ID: {activity_id}
Slug: {activity_slug_table}
Description: {activity_description}"""

	return f"Economic activity with slug '{activity_slug}' not found. Use dpa://reference/economic-activities to see available activities."


def list_available_economic_activities() -> str:
	"""Get a list of all available economic activities.

	Returns:
		Formatted list of economic activity names with slugs
	"""
	content = load_economic_activities()

	if content.startswith("Error:"):
		return content

	activities = []
	lines = content.split('\n')

	# Skip header and separator
	for line in lines[2:]:
		if not line.strip():
			continue

		# Split by pipe and clean
		parts = [p.strip() for p in line.split('|')]

		if len(parts) >= 3:
			activity_name = parts[2]
			activity_slug = parts[3]
			if activity_name and activity_slug:
				activities.append(f"- {activity_name} (slug: `{activity_slug}`)")

	return f"""Available DPA Economic Activities:

{chr(10).join(activities)}

Use `dpa://economic-activity/{{slug}}` to get details for a specific activity."""


def list_available_policy_areas() -> str:
	"""Get a list of all available policy areas.

	Returns:
		Formatted list of policy area names
	"""
	content = load_policy_areas()

	if content.startswith("Error:"):
		return content

	policy_areas = []
	lines = content.split('\n')

	# Skip header and separator
	for line in lines[2:]:
		if not line.strip():
			continue

		# Split by pipe and clean
		parts = [p.strip() for p in line.split('|')]

		if len(parts) >= 3:
			policy_area_id = parts[1]
			policy_area_name = parts[2]
			if policy_area_name:
				policy_areas.append(f"- {policy_area_name} (ID: {policy_area_id})")

	return f"""Available DPA Policy Areas:

{chr(10).join(policy_areas)}"""


def list_available_event_types() -> str:
	"""Get a list of all available event types.

	Returns:
		Formatted list of event type names
	"""
	content = load_event_types()

	if content.startswith("Error:"):
		return content

	event_types = []
	lines = content.split('\n')

	# Skip header and separator
	for line in lines[2:]:
		if not line.strip():
			continue

		# Split by pipe and clean
		parts = [p.strip() for p in line.split('|')]

		if len(parts) >= 5:
			event_type_id = parts[1]
			event_type_name = parts[4]
			is_binding = parts[3]
			if event_type_name:
				binding_status = "Binding" if is_binding == "1" else "Non-binding"
				event_types.append(f"- {event_type_name} (ID: {event_type_id}, {binding_status})")

	return f"""Available DPA Event Types:

{chr(10).join(event_types)}"""


def list_available_action_types() -> str:
	"""Get a list of all available action types.

	Returns:
		Formatted list of action type names
	"""
	content = load_action_types()

	if content.startswith("Error:"):
		return content

	action_types = []
	lines = content.split('\n')

	# Skip header and separator
	for line in lines[2:]:
		if not line.strip():
			continue

		# Split by pipe and clean
		parts = [p.strip() for p in line.split('|')]

		if len(parts) >= 3:
			action_type_id = parts[1]
			action_type_name = parts[2]
			if action_type_name:
				action_types.append(f"- {action_type_name} (ID: {action_type_id})")

	return f"""Available DPA Action Types:

{chr(10).join(action_types)}"""
