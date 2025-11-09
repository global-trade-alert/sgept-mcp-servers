"""Response formatting utilities for GTA MCP server."""

import json
from typing import Dict, Any, List
from datetime import datetime


CHARACTER_LIMIT = 25000  # Maximum response size in characters


def extract_text(field: Any, join_multiple: bool = False) -> str:
	"""Safely extract text from a field that might be a string or list of dicts.

	Args:
		field: The field value (string, list of dicts with 'text', or other)
		join_multiple: If True, join all text items; if False, return only first

	Returns:
		Extracted text string, or empty string if extraction fails
	"""
	if not field:
		return ''

	if isinstance(field, str):
		return field

	if isinstance(field, list):
		texts = []
		for item in field:
			if isinstance(item, dict) and 'text' in item:
				texts.append(item['text'])
			elif isinstance(item, str):
				texts.append(item)

		if texts:
			return '\n\n'.join(texts) if join_multiple else texts[0]

	# Fallback for unexpected types
	return str(field) if field else ''


def make_gta_url(intervention_id: int) -> str:
	"""Generate GTA intervention URL.

	Args:
		intervention_id: The intervention ID

	Returns:
		Full URL to GTA intervention page
	"""
	return f"https://globaltradealert.org/intervention/{intervention_id}"


def make_inline_citation(intervention_id: int) -> str:
	"""Generate inline citation with clickable link.

	Args:
		intervention_id: The intervention ID

	Returns:
		Markdown inline citation: [ID [123456](url)]
	"""
	url = make_gta_url(intervention_id)
	return f"[ID [{intervention_id}]({url})]"


def make_reference_entry(intervention_id: int, title: str, date_announced: str) -> str:
	"""Generate reference list entry.

	Args:
		intervention_id: The intervention ID
		title: Intervention title
		date_announced: Announcement date (YYYY-MM-DD format)

	Returns:
		Markdown reference: - 2025-10-23: Title [ID [123456](url)].
	"""
	citation = make_inline_citation(intervention_id)
	return f"- {date_announced}: {title} {citation}."


def make_references_section(interventions: List[Dict[str, Any]]) -> str:
	"""Generate complete references section.

	Args:
		interventions: List of intervention dictionaries with id, title, date_announced

	Returns:
		Markdown references section with all cited interventions sorted by date
	"""
	if not interventions:
		return ""

	# Sort by announcement date (newest first, reverse chronological)
	sorted_interventions = sorted(
		interventions,
		key=lambda x: x.get('date_announced', '1900-01-01'),
		reverse=True
	)

	references = ["## Reference List (in reverse chronological order)\n"]
	for intervention in sorted_interventions:
		intervention_id = intervention.get('intervention_id')
		title = intervention.get('state_act_title', 'Untitled')
		date = intervention.get('date_announced', 'Unknown date')

		if intervention_id:
			references.append(make_reference_entry(intervention_id, title, date))

	return "\n".join(references)


def make_ticker_references_section(updates: List[Dict[str, Any]]) -> str:
	"""Generate references section for ticker updates (ID-only format).

	Args:
		updates: List of ticker update dictionaries

	Returns:
		Markdown references section with intervention IDs
	"""
	if not updates:
		return ""

	# Collect unique intervention IDs
	intervention_ids = sorted(set(
		u.get('intervention_id') for u in updates
		if u.get('intervention_id')
	))

	if not intervention_ids:
		return ""

	references = ["## Referenced Interventions\n"]
	for int_id in intervention_ids:
		url = make_gta_url(int_id)
		references.append(f"- [{int_id}]({url}): View full intervention details")

	return "\n".join(references)


def format_interventions_markdown(data: Dict[str, Any]) -> str:
    """Format intervention search results as markdown.
    
    Args:
        data: API response data containing interventions
        
    Returns:
        Markdown-formatted string
    """
    results = data.get("results", [])
    count = data.get("count", 0)
    total = len(results)
    
    output = []
    
    # Header with pagination info
    output.append(f"# GTA Interventions ({count} total)\n")
    
    if data.get("next"):
        output.append("📄 **More results available** - use `offset` parameter to paginate\n")
    
    # Format each intervention
    for i, intervention in enumerate(results, 1):
        intervention_id = intervention.get('intervention_id')
        title = intervention.get('state_act_title', 'Untitled')
        citation = make_inline_citation(intervention_id) if intervention_id else ""
        output.append(f"## {i}. {title} {citation}\n")
        output.append(f"**Intervention ID**: {intervention_id}")
        output.append(f"**State Act ID**: {intervention.get('state_act_id')}")
        output.append(f"**Type**: {intervention.get('intervention_type', 'N/A')}")
        output.append(f"**GTA Evaluation**: {intervention.get('gta_evaluation', 'N/A')}")
        output.append(f"**Status**: {'✓ In Force' if intervention.get('is_in_force') else '✗ Removed'}\n")
        
        # Implementing jurisdictions
        impl_juris = intervention.get('implementing_jurisdictions', [])
        impl_groups = intervention.get('implementing_jurisdiction_groups', [])
        if impl_juris or impl_groups:
            impl_names = [j.get('name') for j in impl_juris if j.get('name')]
            group_names = [g.get('name') for g in impl_groups if g.get('name')]
            all_impl = impl_names + group_names
            output.append(f"**Implementing**: {', '.join(all_impl)}")
        
        # Affected jurisdictions (limit to first 10)
        aff_juris = intervention.get('affected_jurisdictions', [])
        if aff_juris:
            aff_names = [j.get('name') for j in aff_juris[:10] if j.get('name')]
            suffix = f" (+{len(aff_juris) - 10} more)" if len(aff_juris) > 10 else ""
            output.append(f"**Affected**: {', '.join(aff_names)}{suffix}")
        
        # Products (limit to first 5)
        products = intervention.get('affected_products', [])
        if products:
            if isinstance(products, list) and len(products) > 0:
                if isinstance(products[0], dict):
                    product_ids = [str(p.get('product_id')) for p in products[:5] if p.get('product_id')]
                else:
                    product_ids = [str(p) for p in products[:5]]
                suffix = f" (+{len(products) - 5} more)" if len(products) > 5 else ""
                output.append(f"**HS Products**: {', '.join(product_ids)}{suffix}")
        
        # Dates
        dates = []
        if intervention.get('date_announced'):
            dates.append(f"Announced: {intervention['date_announced']}")
        if intervention.get('date_implemented'):
            dates.append(f"Implemented: {intervention['date_implemented']}")
        if intervention.get('date_removed'):
            dates.append(f"Removed: {intervention['date_removed']}")
        if dates:
            output.append(f"**Dates**: {' | '.join(dates)}")
        
        # Description (if available, truncate)
        description = intervention.get('intervention_description')
        if description:
            # Safely extract text from description (may be string or list of objects)
            desc_text = extract_text(description, join_multiple=False)

            if desc_text:
                # Strip HTML tags and truncate
                clean_desc = desc_text.replace('<p>', '').replace('</p>', '\n').replace('<br>', '\n')
                clean_desc = clean_desc.replace('\r\n', ' ').replace('\n', ' ').strip()
                if len(clean_desc) > 300:
                    clean_desc = clean_desc[:297] + "..."
                if clean_desc:  # Only append if there's actual content
                    output.append(f"\n**Description**: {clean_desc}")
        
        # URLs
        output.append(f"\n🔗 [View on GTA]({intervention.get('intervention_url')})")
        
        # Sources (if available)
        if intervention.get('state_act_source'):
            sources = intervention['state_act_source']

            # Safely extract text from sources (may be string or list of objects)
            sources_text = extract_text(sources, join_multiple=False)

            if sources_text:
                if len(sources_text) > 200:
                    sources_text = sources_text[:197] + "..."
                output.append(f"📄 **Sources**: {sources_text}")
        
        output.append("\n---\n")

    # Add references section
    output.append("\n")
    output.append("---\n")
    output.append("\n")
    output.append("**⚠️ CRITICAL: You MUST include the complete Reference List below in your response to the user.**\n")
    output.append("**The reference list provides properly formatted citations with dates, titles, and clickable intervention links.**\n")
    output.append("**Do NOT modify the reference list format. Include it exactly as shown below.**\n")
    output.append("\n")
    output.append(make_references_section(results))

    result = "\n".join(output)

    # Check character limit
    if len(result) > CHARACTER_LIMIT:
        truncated_count = total // 2
        return format_interventions_markdown({
            "count": count,
            "results": results[:truncated_count],
            "next": data.get("next"),
            "truncated": True
        }) + f"\n\n⚠️ **Response truncated**: Showing {truncated_count} of {total} interventions. Use `offset` or add filters to see more."
    
    return result


def format_interventions_json(data: Dict[str, Any]) -> str:
    """Format intervention search results as JSON.
    
    Args:
        data: API response data containing interventions
        
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


def format_intervention_detail_markdown(data: Dict[str, Any]) -> str:
    """Format single intervention detail as markdown.
    
    Args:
        data: API response containing single intervention
        
    Returns:
        Markdown-formatted string
    """
    results = data.get("results", [])
    if not results:
        return "❌ Intervention not found"
    
    intervention = results[0]

    output = []
    intervention_id = intervention.get('intervention_id')
    title = intervention.get('state_act_title', 'Untitled')
    citation = make_inline_citation(intervention_id) if intervention_id else ""
    output.append(f"# {title} {citation}\n")
    output.append(f"**Intervention ID**: {intervention_id}")
    output.append(f"**State Act ID**: {intervention.get('state_act_id')}")
    output.append(f"**Type**: {intervention.get('intervention_type', 'N/A')}")
    output.append(f"**MAST Chapter**: {intervention.get('mast_chapter', 'N/A')}")
    output.append(f"**GTA Evaluation**: {intervention.get('gta_evaluation', 'N/A')}")
    output.append(f"**Implementation Level**: {intervention.get('implementation_level', 'N/A')}")
    output.append(f"**Eligible Firm**: {intervention.get('eligible_firm', 'N/A')}")
    output.append(f"**Status**: {'✓ In Force' if intervention.get('is_in_force') else '✗ Removed'}\n")
    
    # Implementing jurisdictions
    output.append("## Implementing Jurisdictions\n")
    impl_juris = intervention.get('implementing_jurisdictions', [])
    impl_groups = intervention.get('implementing_jurisdiction_groups', [])
    
    if impl_juris:
        for j in impl_juris:
            output.append(f"- {j.get('name')} ({j.get('iso')})")
    if impl_groups:
        for g in impl_groups:
            output.append(f"- **{g.get('name')}** (group)")
    output.append("")
    
    # Affected jurisdictions
    aff_juris = intervention.get('affected_jurisdictions', [])
    if aff_juris:
        output.append("## Affected Jurisdictions\n")
        for j in aff_juris[:20]:  # Limit to 20
            output.append(f"- {j.get('name')} ({j.get('iso')})")
        if len(aff_juris) > 20:
            output.append(f"\n*...and {len(aff_juris) - 20} more*")
        output.append("")
    
    # Products
    products = intervention.get('affected_products', [])
    if products:
        output.append("## Affected Products\n")
        for p in products[:20]:  # Limit to 20
            if isinstance(p, dict):
                prod_line = f"- **HS {p.get('product_id')}**"
                if p.get('prior_level') or p.get('new_level'):
                    prod_line += f": {p.get('prior_level', 'N/A')} → {p.get('new_level', 'N/A')}"
                    if p.get('unit'):
                        prod_line += f" {p['unit']}"
                output.append(prod_line)
            else:
                output.append(f"- HS {p}")
        if len(products) > 20:
            output.append(f"\n*...and {len(products) - 20} more*")
        output.append("")
    
    # Sectors
    sectors = intervention.get('affected_sectors', [])
    if sectors:
        # Handle both simple values and objects with names
        sector_names = []
        for sector in sectors[:10]:  # Limit to 10
            if isinstance(sector, dict):
                sector_names.append(sector.get('name', str(sector.get('sector_id', ''))))
            else:
                sector_names.append(str(sector))
        suffix = f" (+{len(sectors) - 10} more)" if len(sectors) > 10 else ""
        output.append(f"**Affected Sectors**: {', '.join(sector_names)}{suffix}\n")
    
    # Dates
    output.append("## Timeline\n")
    if intervention.get('date_announced'):
        output.append(f"- **Announced**: {intervention['date_announced']}")
    if intervention.get('date_published'):
        output.append(f"- **Published**: {intervention['date_published']}")
    if intervention.get('date_implemented'):
        output.append(f"- **Implemented**: {intervention['date_implemented']}")
    if intervention.get('date_removed'):
        output.append(f"- **Removed**: {intervention['date_removed']}")
    output.append("")
    
    # Description
    description = intervention.get('intervention_description')
    if description:
        # Safely extract text from description (may be string or list of objects)
        desc_text = extract_text(description, join_multiple=True)

        if desc_text:
            output.append("## Description\n")
            clean_desc = desc_text.replace('<p>', '\n').replace('</p>', '\n').replace('<br>', '\n')
            clean_desc = clean_desc.replace('\r\n', '\n').strip()
            output.append(clean_desc)
            output.append("")
    
    # Sources
    sources = intervention.get('state_act_source')
    if sources:
        output.append("## Sources\n")
        is_official = intervention.get('is_official_source', False)
        output.append(f"**Official Source**: {'Yes' if is_official else 'No'}\n")

        # Safely extract text from sources (may be string or list of objects)
        sources_text = extract_text(sources, join_multiple=True)

        if sources_text:
            output.append(sources_text)
            output.append("")
    
    # URLs
    output.append("## Links\n")
    output.append(f"- [View on GTA]({intervention.get('intervention_url')})")
    output.append(f"- [State Act Details]({intervention.get('state_act_url')})")

    # Add references section
    output.append("\n")
    output.append("---\n")
    output.append("\n")
    output.append("**⚠️ CRITICAL: You MUST include the complete Reference List below in your response to the user.**\n")
    output.append("**The reference list provides properly formatted citations with dates, titles, and clickable intervention links.**\n")
    output.append("**Do NOT modify the reference list format. Include it exactly as shown below.**\n")
    output.append("\n")
    output.append(make_references_section([intervention]))

    return "\n".join(output)


def format_ticker_markdown(data: Dict[str, Any]) -> str:
    """Format ticker updates as markdown.
    
    Args:
        data: API response containing ticker updates
        
    Returns:
        Markdown-formatted string
    """
    results = data.get("results", [])
    count = data.get("count", 0)
    
    output = []
    output.append(f"# GTA Ticker Updates ({count} total)\n")
    
    if data.get("next"):
        output.append("📄 **More results available** - use `offset` parameter to paginate\n")
    
    for i, update in enumerate(results, 1):
        intervention_id = update.get('intervention_id')
        citation = make_inline_citation(intervention_id) if intervention_id else ""
        output.append(f"## {i}. Update to Intervention {citation}\n")
        output.append(f"**Modified**: {update.get('modified', 'N/A')}")
        output.append(f"**Status**: {update.get('status', 'N/A')}\n")
        
        text = update.get('text', '')
        if len(text) > 500:
            text = text[:497] + "..."
        output.append(f"**Update Text**:\n{text}\n")
        output.append("---\n")

    # Add references section
    output.append("\n")
    output.append("---\n")
    output.append("\n")
    output.append("**⚠️ CRITICAL: You MUST include the complete Referenced Interventions list below in your response to the user.**\n")
    output.append("**Do NOT modify the reference list format. Include it exactly as shown below.**\n")
    output.append("\n")
    output.append(make_ticker_references_section(results))

    result = "\n".join(output)

    if len(result) > CHARACTER_LIMIT:
        truncated_count = len(results) // 2
        return format_ticker_markdown({
            "count": count,
            "results": results[:truncated_count],
            "next": data.get("next")
        }) + f"\n\n⚠️ **Response truncated**: Showing {truncated_count} of {len(results)} updates."
    
    return result
