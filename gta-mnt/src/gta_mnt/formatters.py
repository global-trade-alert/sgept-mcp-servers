"""Formatters for gta_mnt outputs (markdown formatting, comment structures)."""

from typing import Optional


def format_issue_comment(
    field: str,
    criticality: str,
    current_value: str,
    suggested_value: str,
    rationale: str,
    source_quote: str,
    source_ref: str
) -> str:
    """Format an issue comment according to spec.

    Args:
        field: Field name (e.g., "intervention_type")
        criticality: "Critical" | "Important" | "Minor"
        current_value: Current value in entry
        suggested_value: Proposed new value
        rationale: 1-2 paragraph explanation
        source_quote: Exact quote from official source
        source_ref: Source reference (e.g., "Official Gazette, 15 Jan 2026")

    Returns:
        Markdown-formatted comment string.
    """
    return f"""## FIELD: {field}
**Criticality:** {criticality}
**Current Value:** {current_value}
**Suggested Value:** {suggested_value}

### Rationale
{rationale}

### Source Quote
> "{source_quote}"
> — {source_ref}
"""


def format_verification_comment(
    decision: str,
    source_quote: str,
    source_ref: str,
    explanation: str
) -> str:
    """Format a verification comment for correct critical decisions.

    Args:
        decision: What was decided in the entry
        source_quote: Quote confirming the interpretation
        source_ref: Source reference
        explanation: Why the interpretation is correct

    Returns:
        Markdown-formatted verification comment.
    """
    return f"""## VERIFIED: {decision}
**Decision:** {decision}

### Source Confirmation
> "{source_quote}"
> — {source_ref}

{explanation}
"""


def format_review_complete_comment(
    verified_fields: list[str],
    critical_decisions: Optional[list[str]] = None
) -> str:
    """Format a review complete comment (no issues found).

    Args:
        verified_fields: List of fields verified as correct
        critical_decisions: Optional list of critical decisions verified

    Returns:
        Markdown-formatted review complete comment.
    """
    import datetime

    fields_section = "\n".join([f"- {field}" for field in verified_fields])

    critical_section = ""
    if critical_decisions:
        critical_items = "\n".join([f"- {decision}" for decision in critical_decisions])
        critical_section = f"\n\n### Critical Decisions Verified\n{critical_items}"

    review_date = datetime.datetime.now().strftime("%Y-%m-%d")

    return f"""## REVIEW COMPLETE

Entry reviewed against official source. No substantive changes required.

### Verified Fields
{fields_section}{critical_section}

*Reviewed by Sancho Claudino automated review system on {review_date}.*
"""


def truncate_quote(quote: str, max_length: int = 500) -> str:
    """Truncate long quotes with ellipsis.

    Args:
        quote: Original quote text
        max_length: Maximum length before truncation

    Returns:
        Truncated quote with [...] if needed
    """
    if len(quote) <= max_length:
        return quote
    return quote[:max_length] + " [...]"


# ============================================================================
# WS2: List Step 1 Queue Formatter
# ============================================================================

def format_step1_queue(data: dict) -> str:
    """Format Step 1 queue results as markdown.

    Args:
        data: API response dict with 'results' and 'count'

    Returns:
        Markdown-formatted queue listing
    """
    results = data.get("results", [])
    count = data.get("count", 0)

    if count == 0:
        return "# Step 1 Review Queue\n\n*No measures awaiting Step 1 review.*"

    lines = [
        f"# Step 1 Review Queue ({count} measures)\n",
        "| ID | Title | Date Entered Review |",
        "|-----|-------|---------------------|"
    ]

    for measure in results:
        state_act_id = measure.get("id", "N/A")
        title = (measure.get("title") or "Untitled")[:60]  # Truncate long titles

        # Handle datetime object or string for status_time
        status_time = measure.get("status_time")
        if status_time is None:
            status_time = "N/A"
        elif hasattr(status_time, 'strftime'):
            status_time = status_time.strftime("%Y-%m-%d")
        else:
            status_time = str(status_time)[:10]

        lines.append(f"| {state_act_id} | {title} | {status_time} |")

    return "\n".join(lines)


# ============================================================================
# WS3: Get Measure Detail Formatter
# ============================================================================

def format_measure_detail(measure: dict) -> str:
    """Format complete measure details as markdown.

    Args:
        measure: Measure dict from API with interventions and comments

    Returns:
        Markdown-formatted measure details
    """
    # Handle error case
    if measure.get("error"):
        return f"# Error\n\n{measure['error']}"

    state_act_id = measure.get("id", "N/A")
    title = measure.get("title") or "Untitled"
    description = measure.get("description") or "No description"
    status_id = measure.get("status_id", "N/A")
    status_name = measure.get("status_name") or "Unknown"
    is_official = measure.get("is_source_official")
    announcement_date = measure.get("announcement_date")

    # Format implementing jurisdictions from list
    impl_jurisdictions = measure.get("implementing_jurisdictions", [])
    if impl_jurisdictions:
        impl_jur_str = ", ".join([j.get("jurisdiction_name", j.get("iso_code", "N/A")) for j in impl_jurisdictions])
    else:
        impl_jur_str = "N/A"

    # Get source URL from source_info or direct source field
    source_info = measure.get("source_info", {})
    primary_source = source_info.get("primary_source") or measure.get("source") or "N/A"

    lines = [
        f"# StateAct {state_act_id}: {title}\n",
        f"**Implementing Jurisdiction:** {impl_jur_str}",
        f"**Status:** {status_name} (ID: {status_id})",
        f"**Official Source:** {'Yes' if is_official else 'No'}",
        f"**Announcement Date:** {announcement_date or 'N/A'}",
        f"**Source:** {primary_source}\n",
        "## Description",
        description,
        ""
    ]

    # Interventions section
    interventions = measure.get("interventions", [])
    if interventions:
        lines.append(f"\n## Interventions ({len(interventions)})\n")
        for i, intervention in enumerate(interventions, 1):
            int_id = intervention.get("id", "N/A")
            int_type = intervention.get("type_name") or intervention.get("intervention_type") or "N/A"
            evaluation = intervention.get("evaluation_name") or "N/A"
            affected_flow = intervention.get("affected_flow_name") or "N/A"
            eligible_firms = intervention.get("eligible_firms_name") or "N/A"
            inception_date = intervention.get("inception_date")
            removal_date = intervention.get("removal_date")
            implementation_level_id = intervention.get("implementation_level_id")
            implementation_level_name = intervention.get("implementation_level_name")
            prior_level = intervention.get("prior_level")
            new_level = intervention.get("new_level")
            unit_id = intervention.get("unit_id")
            unit_name = intervention.get("unit_name")
            int_description = intervention.get("description") or ""

            # Format implementation level with name if available
            if implementation_level_name:
                impl_level_str = f"{implementation_level_name} (ID: {implementation_level_id})"
            elif implementation_level_id:
                impl_level_str = f"ID: {implementation_level_id}"
            else:
                impl_level_str = "N/A"

            # Format unit with name if available
            if unit_name:
                unit_str = unit_name
            elif unit_id:
                unit_str = f"ID: {unit_id}"
            else:
                unit_str = "N/A"

            lines.append(f"### {i}. INT-{int_id}: {int_type}")
            lines.append(f"- **Evaluation:** {evaluation}")
            lines.append(f"- **Affected Flow:** {affected_flow}")
            lines.append(f"- **Implementation Level:** {impl_level_str}")
            lines.append(f"- **Eligible Firms:** {eligible_firms}")
            lines.append(f"- **Inception Date:** {inception_date or 'N/A'}")
            lines.append(f"- **Removal Date:** {removal_date or 'N/A'}")
            if prior_level is not None or new_level is not None:
                lines.append(f"- **Prior Level:** {prior_level if prior_level is not None else 'N/A'}")
                lines.append(f"- **New Level:** {new_level if new_level is not None else 'N/A'}")
                lines.append(f"- **Unit:** {unit_str}")
            lines.append("")

            # Affected Jurisdictions section with type
            affected_jurs = intervention.get("affected_jurisdictions", [])
            if affected_jurs:
                lines.append("#### Affected Jurisdictions")
                for aj in affected_jurs:
                    name = aj.get("jurisdiction_name") or aj.get("iso_code") or "Unknown"
                    iso = aj.get("iso_code") or ""
                    type_name = aj.get("type_name")
                    if type_name:
                        lines.append(f"- {name} ({iso}) [{type_name}]")
                    else:
                        lines.append(f"- {name} ({iso})")
                lines.append("")

            # Distorted Markets section
            distorted_markets = intervention.get("distorted_markets", [])
            if distorted_markets:
                lines.append("#### Distorted Markets")
                for dm in distorted_markets:
                    name = dm.get("jurisdiction_name") or dm.get("iso_code") or "Unknown"
                    iso = dm.get("iso_code") or ""
                    type_name = dm.get("type_name")
                    if type_name:
                        lines.append(f"- {name} ({iso}) [{type_name}]")
                    else:
                        lines.append(f"- {name} ({iso})")
                lines.append("")

            # Firms section
            firms = intervention.get("firms", [])
            if firms:
                lines.append("#### Firms")
                for firm in firms:
                    firm_name = firm.get("firm_name") or "Unknown"
                    role_name = firm.get("role_name")
                    if role_name:
                        lines.append(f"- {firm_name} [{role_name}]")
                    else:
                        lines.append(f"- {firm_name}")
                lines.append("")

            # Description section (full text, no truncation)
            if int_description:
                lines.append("#### Description")
                lines.append(int_description)
                lines.append("")

    # Comments section
    comments = measure.get("comments", [])
    if comments:
        lines.append(f"\n## Comments ({len(comments)})\n")
        for comment in comments:
            author = comment.get("author_name") or comment.get("author") or "Unknown"
            # Handle datetime or string for creation_time
            created = comment.get("creation_time") or comment.get("created")
            if created is None:
                created = "N/A"
            elif hasattr(created, 'strftime'):
                created = created.strftime("%Y-%m-%d %H:%M")
            else:
                created = str(created)[:16]
            text = comment.get("comment_value") or comment.get("text") or ""
            text = text[:300]  # Truncate
            lines.append(f"### {author} ({created})")
            lines.append(f"{text}{'...' if len(text) >= 300 else ''}\n")

    # Linked sources section
    linked_sources = source_info.get("linked_sources", []) or measure.get("sources", [])
    if linked_sources:
        lines.append(f"\n## Linked Sources ({len(linked_sources)})\n")
        for src in linked_sources:
            url = src.get("source_url", "N/A")
            is_collected = src.get("is_collected")
            lines.append(f"- {url} {'(archived)' if is_collected else ''}")

    return "\n".join(lines)


# ============================================================================
# WS4: Get Source Formatter
# ============================================================================

def format_source_result(source_result) -> str:
    """Format source retrieval result as markdown.

    Args:
        source_result: SourceResult object

    Returns:
        Markdown-formatted source content
    """
    lines = [
        f"# Official Source\n",
        f"**Type:** {source_result.source_type}",
        f"**URL:** {source_result.source_url}",
        f"**Content Type:** {source_result.content_type}\n"
    ]

    if source_result.content:
        lines.append("## Extracted Content\n")
        # Truncate very long content
        content = source_result.content
        if len(content) > 50000:
            content = content[:50000] + "\n\n[... content truncated for brevity ...]"
        lines.append(content)
    else:
        lines.append("*Content not fetched (fetch_content=False)*")

    return "\n".join(lines)


# ============================================================================
# WS10: List Templates Formatter
# ============================================================================

def format_templates(data: dict) -> str:
    """Format comment templates as markdown.

    Args:
        data: API response dict with 'results'

    Returns:
        Markdown-formatted template list
    """
    results = data.get("results", [])

    if not results:
        return "# Comment Templates\n\n*No templates available.*"

    lines = [
        f"# Comment Templates ({len(results)})\n",
        "| ID | Name | Checklist | Preview |",
        "|-----|------|-----------|---------|"
    ]

    for template in results:
        template_id = template.get("id", "N/A")
        name = template.get("template_name") or template.get("name") or "Untitled"
        is_checklist = "Yes" if template.get("is_checklist") else "No"
        text = template.get("template_text") or template.get("description") or ""
        preview = text[:50].replace("\n", " ")  # Truncate and remove newlines

        lines.append(f"| {template_id} | {name} | {is_checklist} | {preview}... |")

    return "\n".join(lines)
