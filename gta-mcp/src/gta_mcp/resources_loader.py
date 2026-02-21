"""Resource loading and parsing utilities for GTA MCP server."""

import os
import re
from pathlib import Path
from typing import Dict, Optional


# Cache for loaded resources
_CACHE: Dict[str, str] = {}


def get_resources_dir() -> Path:
	"""Get the path to the resources directory.

	Supports two layouts:
	- Development: src/gta_mcp/resources_loader.py → ../../resources/
	- Installed (pip/uvx): gta_mcp/resources_loader.py → gta_mcp/resources/
	"""
	current_file = Path(__file__)

	# Installed layout: resources/ is a sibling directory inside the package
	installed_path = current_file.parent / "resources"
	if installed_path.is_dir():
		return installed_path

	# Development layout: resources/ is at the project root (3 levels up from src/gta_mcp/)
	project_root = current_file.parent.parent.parent
	dev_path = project_root / "resources"
	if dev_path.is_dir():
		return dev_path

	# Fallback to development path (will produce clear "file not found" errors)
	return dev_path


def load_jurisdictions_table() -> str:
	"""Load the complete jurisdictions table from markdown file.

	Returns:
		Complete markdown table content
	"""
	if "jurisdictions" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "gta_jurisdictions.md"

		if not file_path.exists():
			return "Error: Jurisdictions resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["jurisdictions"] = f.read()

	return _CACHE["jurisdictions"]


def load_intervention_types() -> str:
	"""Load the complete intervention types descriptions from markdown file.

	Returns:
		Complete markdown content with all intervention type descriptions
	"""
	if "intervention_types" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "GTA intervention type descriptions.md"

		if not file_path.exists():
			return "Error: Intervention types resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["intervention_types"] = f.read()

	return _CACHE["intervention_types"]


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
UN Code (jurisdiction_id): {jurisdiction_id}
ISO Code: {iso}
GTA Jurisdiction ID: {gta_jurisdiction_id}
Short Name: {jurisdiction_name_short}
Adjective Form: {jurisdiction_name_adj}"""

	return f"Jurisdiction with ISO code '{iso_code}' not found. Please use a valid ISO 3-letter code (e.g., USA, CHN, DEU, GBR)."


def parse_intervention_type(type_slug: str) -> Optional[str]:
	"""Parse intervention types and extract section for specific type.

	Args:
		type_slug: Slugified intervention type name (e.g., export-ban, import-tariff)

	Returns:
		Markdown section with intervention type details or None if not found
	"""
	content = load_intervention_types()

	if content.startswith("Error:"):
		return content

	# Normalize slug
	slug = type_slug.lower().strip().replace('_', '-')

	# Try to find the heading matching this slug
	# Intervention types are level 2 headings (##)
	lines = content.split('\n')

	# Common intervention type name variations
	search_patterns = [
		slug.replace('-', ' '),  # "export-ban" -> "export ban"
		slug.replace('-', ' ').title(),  # "export-ban" -> "Export Ban"
	]

	section_start = None
	section_heading = None

	for i, line in enumerate(lines):
		if line.startswith('## '):
			heading_text = line[3:].strip()
			heading_lower = heading_text.lower()

			# Check if this heading matches our search
			for pattern in search_patterns:
				if heading_lower == pattern:
					section_start = i
					section_heading = heading_text
					break

			if section_start is not None:
				break

	if section_start is None:
		# List available types (just the main headings)
		available = []
		for line in lines:
			if line.startswith('## ') and not line.startswith('# '):
				heading = line[3:].strip()
				available.append(heading)

		available_list = "\n- ".join(available[:20])  # Show first 20
		return f"""Intervention type '{type_slug}' not found.

Available intervention types:
- {available_list}

Tip: Use slugified names like 'export-ban', 'import-tariff', 'state-loan'"""

	# Extract section until next ## heading or end
	section_lines = [f"# {section_heading}\n"]
	for line in lines[section_start + 1:]:
		# Stop at next level 1 or 2 heading
		if line.startswith('## ') or line.startswith('# '):
			break
		section_lines.append(line)

	return '\n'.join(section_lines)


def list_available_intervention_types() -> str:
	"""Get a list of all available intervention types.

	Returns:
		Formatted list of intervention type names
	"""
	content = load_intervention_types()

	if content.startswith("Error:"):
		return content

	types = []
	lines = content.split('\n')

	for line in lines:
		if line.startswith('## '):
			heading = line[3:].strip()
			# Create slug
			slug = heading.lower().replace(' ', '-')
			types.append(f"- {heading} (slug: `{slug}`)")

	return f"""Available GTA Intervention Types:

{chr(10).join(types)}

Use `gta://intervention-type/{{slug}}` to get details for a specific type."""


def load_search_guide() -> str:
	"""Load the search guide from markdown file.

	Returns:
		Complete markdown content with search best practices
	"""
	if "search_guide" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "search_guide.md"

		if not file_path.exists():
			return "Error: Search guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["search_guide"] = f.read()

	return _CACHE["search_guide"]


def load_date_fields_guide() -> str:
	"""Load the date fields guide from markdown file.

	Returns:
		Complete markdown content explaining GTA date fields
	"""
	if "date_fields_guide" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "date_fields_guide.md"

		if not file_path.exists():
			return "Error: Date fields guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["date_fields_guide"] = f.read()

	return _CACHE["date_fields_guide"]


def load_sectors_table() -> str:
	"""Load and format the CPC sectors table.

	Returns:
		Markdown-formatted table of all CPC sectors with IDs, names, and categories
	"""
	if "sectors_table" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "api_sector_list.md"

		if not file_path.exists():
			return "Error: Sectors list resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			content = f.read()

		# Add helpful header information
		header = """# CPC Sector Classification

## Overview
Central Product Classification (CPC) sectors provide broader product coverage than HS codes.

### Key Information:
- **Services**: Sectors with ID >= 500 (e.g., 711-717 Financial services)
- **Goods**: Sectors with ID < 500 (e.g., 11-49 Agricultural, 211-499 Manufactured goods)
- **Usage**: Can filter by sector ID (integer) or sector name (string with fuzzy matching)

### Categories:
- **1-49**: Raw materials (agriculture, livestock, forestry, aquatic, mining)
- **110-180**: Minerals, energy, water
- **211-389**: Manufactured goods (food, textiles, chemicals, metals, machinery)
- **391-399**: Wastes and scraps
- **411-499**: Metals and transport equipment
- **531-547**: Construction goods and services
- **611-698**: Trade and distribution services
- **711-733**: Financial and real estate services
- **811-839**: Professional, technical, and business services
- **841-889**: Telecommunications and support services
- **911-980**: Public services (government, education, health, environment)
- **990**: Extraterritorial services

---

"""
		_CACHE["sectors_table"] = header + content

	return _CACHE["sectors_table"]


def load_cpc_vs_hs_guide() -> str:
	"""Load the guide explaining when to use CPC sectors vs HS codes.

	Returns:
		Complete markdown content explaining the differences and usage
	"""
	if "cpc_vs_hs_guide" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "cpc_vs_hs_guide.md"

		if not file_path.exists():
			return "Error: CPC vs HS guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["cpc_vs_hs_guide"] = f.read()

	return _CACHE["cpc_vs_hs_guide"]


def load_eligible_firms_table() -> str:
	"""Load and format the eligible firms reference table.

	Returns:
		Markdown-formatted table of eligible firm types with IDs and descriptions
	"""
	if "eligible_firms_table" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "api_eligible_firm_list.md"

		if not file_path.exists():
			return "Error: Eligible firms list resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			content = f.read()

		# Add helpful header information
		header = """# Eligible Firms Classification

## Overview
The "eligible firms" parameter identifies which types of businesses are targeted or affected by a policy intervention.

### Key Information:
- Determines the scope and scale of policy impact
- Distinguishes universal policies from targeted interventions
- Essential for assessing market access implications

### Common Use Cases:
- **all**: General policies affecting all companies
- **SMEs**: Programs specifically for small/medium enterprises
- **firm-specific**: Company-specific incentives (e.g., Tesla subsidies)
- **state-controlled**: Policies targeting state-owned enterprises
- **location-specific**: Regional development programs

---

"""
		_CACHE["eligible_firms_table"] = header + content

	return _CACHE["eligible_firms_table"]


def load_implementation_levels_table() -> str:
	"""Load and format the implementation levels reference table.

	Returns:
		Markdown-formatted table of implementation levels with IDs and descriptions
	"""
	if "implementation_levels_table" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "api_implementation_level_list.md"

		if not file_path.exists():
			return "Error: Implementation levels list resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			content = f.read()

		# Add helpful header information
		header = """# Implementation Level Classification

## Overview
The "implementation level" parameter identifies which level of government or agency is implementing the policy intervention.

### Key Information:
- Identifies the governmental authority implementing the measure
- Ranges from supranational (EU Commission) to subnational (state/provincial)
- Includes financial institutions (IFI, NFI)

### Implementation Hierarchy:
1. **Supranational**: Regional bodies with binding authority (e.g., EU Commission)
2. **National**: Central government and central banks
3. **Subnational**: Regional, state, provincial, municipal governments
4. **SEZ**: Special economic zones
5. **IFI**: International financial institutions (multi-country)
6. **NFI**: National financial institutions (Export-Import banks, development banks)

### Important Notes:
- GTA always reports the final governmental implementer
- Example: If Ministry announces loan scheme via National Development Bank → NFI
- Central bank announcements are classified as National level
- Aliases supported: IFI, NFI, SEZ work alongside full names

---

"""
		_CACHE["implementation_levels_table"] = header + content

	return _CACHE["implementation_levels_table"]


def load_parameters_guide() -> str:
	"""Load the comprehensive parameters guide from markdown file.

	Returns:
		Complete markdown guide with parameter descriptions and usage guidance
	"""
	if "parameters_guide" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "guides" / "parameters.md"

		if not file_path.exists():
			return "Error: Parameters guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["parameters_guide"] = f.read()

	return _CACHE["parameters_guide"]


def load_query_examples() -> str:
	"""Load the comprehensive query examples library from markdown file.

	Returns:
		Complete markdown guide with categorized query examples
	"""
	if "query_examples" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "guides" / "query_examples.md"

		if not file_path.exists():
			return "Error: Query examples guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["query_examples"] = f.read()

	return _CACHE["query_examples"]


def load_mast_chapters() -> str:
	"""Load the MAST chapter taxonomy reference from markdown file.

	Returns:
		Complete markdown reference with A-P taxonomy, special categories, and usage guide
	"""
	if "mast_chapters" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "reference" / "mast_chapters.md"

		if not file_path.exists():
			return "Error: MAST chapters reference file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["mast_chapters"] = f.read()

	return _CACHE["mast_chapters"]


def load_query_syntax() -> str:
	"""Load the query syntax and strategy guide from markdown file.

	Returns:
		Complete markdown guide with query strategy cascade, syntax reference, and examples
	"""
	if "query_syntax" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "guides" / "query_syntax.md"

		if not file_path.exists():
			return "Error: Query syntax guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["query_syntax"] = f.read()

	return _CACHE["query_syntax"]


def load_exclusion_filters() -> str:
	"""Load the exclusion filters guide from markdown file.

	Returns:
		Complete markdown guide with keep_* parameter reference, patterns, and troubleshooting
	"""
	if "exclusion_filters" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "guides" / "exclusion_filters.md"

		if not file_path.exists():
			return "Error: Exclusion filters guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["exclusion_filters"] = f.read()

	return _CACHE["exclusion_filters"]


def load_data_model_guide() -> str:
	"""Load the data model guide from markdown file.

	Returns:
		Complete markdown guide explaining GTA data hierarchy and counting units
	"""
	if "data_model_guide" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "guides" / "data_model.md"

		if not file_path.exists():
			return "Error: Data model guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["data_model_guide"] = f.read()

	return _CACHE["data_model_guide"]


def load_common_mistakes() -> str:
	"""Load the common mistakes guide from markdown file.

	Returns:
		Complete markdown checklist of DO/DON'T for agents using GTA data
	"""
	if "common_mistakes" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "guides" / "common_mistakes.md"

		if not file_path.exists():
			return "Error: Common mistakes guide resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["common_mistakes"] = f.read()

	return _CACHE["common_mistakes"]


def load_glossary() -> str:
	"""Load the GTA glossary from markdown file.

	Returns:
		Complete markdown glossary defining key GTA terms for non-expert users
	"""
	if "glossary" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "reference" / "glossary.md"

		if not file_path.exists():
			return "Error: Glossary resource file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["glossary"] = f.read()

	return _CACHE["glossary"]


def load_jurisdiction_groups() -> str:
	"""Load the jurisdiction groups reference from markdown file.

	Returns:
		Markdown reference with G7/G20/EU/BRICS/ASEAN/CPTPP member codes
	"""
	if "jurisdiction_groups" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "reference" / "jurisdiction_groups.md"

		if not file_path.exists():
			return "Error: Jurisdiction groups reference file not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["jurisdiction_groups"] = f.read()

	return _CACHE["jurisdiction_groups"]


def load_query_intent_mapping() -> str:
	"""Load the query intent mapping guide from markdown file.

	Returns:
		Markdown guide mapping natural language terms to GTA structured filters
	"""
	if "query_intent_mapping" not in _CACHE:
		resources_dir = get_resources_dir()
		file_path = resources_dir / "guides" / "query_intent_mapping.md"

		if not file_path.exists():
			return "Error: Query intent mapping guide not found"

		with open(file_path, 'r', encoding='utf-8') as f:
			_CACHE["query_intent_mapping"] = f.read()

	return _CACHE["query_intent_mapping"]


def load_privacy_policy() -> str:
	"""Load the privacy policy from PRIVACY.md.

	Supports two layouts:
	- Installed (pip/uvx): gta_mcp/PRIVACY.md (force-included in wheel)
	- Development: ../../PRIVACY.md (project root)

	Returns:
		Complete privacy policy as markdown
	"""
	if "privacy_policy" not in _CACHE:
		current_file = Path(__file__)

		# Installed layout: PRIVACY.md is a sibling file inside the package
		installed_path = current_file.parent / "PRIVACY.md"
		if installed_path.exists():
			with open(installed_path, 'r', encoding='utf-8') as f:
				_CACHE["privacy_policy"] = f.read()
			return _CACHE["privacy_policy"]

		# Development layout: PRIVACY.md is at the project root
		project_root = current_file.parent.parent.parent
		dev_path = project_root / "PRIVACY.md"
		if dev_path.exists():
			with open(dev_path, 'r', encoding='utf-8') as f:
				_CACHE["privacy_policy"] = f.read()
			return _CACHE["privacy_policy"]

		return "Error: Privacy policy file not found"

	return _CACHE["privacy_policy"]
