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
        "| ID | Title | Implementing Jurisdiction | Date Entered Review |",
        "|-----|-------|--------------------------|---------------------|"
    ]

    for measure in results:
        state_act_id = measure.get("id", "N/A")
        title = measure.get("title", "Untitled")[:60]  # Truncate long titles
        jurisdiction = measure.get("implementing_jurisdiction", "N/A")
        status_time = measure.get("status_time", "N/A")[:10]  # Date only

        lines.append(f"| {state_act_id} | {title} | {jurisdiction} | {status_time} |")

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
    state_act_id = measure.get("id", "N/A")
    title = measure.get("title", "Untitled")
    description = measure.get("description", "No description")
    implementing_jurisdiction = measure.get("implementing_jurisdiction", "N/A")
    status_id = measure.get("status_id", "N/A")
    source_url = measure.get("source_url", "N/A")

    lines = [
        f"# StateAct {state_act_id}: {title}\n",
        f"**Implementing Jurisdiction:** {implementing_jurisdiction}",
        f"**Status ID:** {status_id}",
        f"**Source:** {source_url}\n",
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
            int_type = intervention.get("intervention_type", "N/A")
            affected_jur = intervention.get("affected_jurisdiction", "N/A")
            lines.append(f"{i}. **INT-{int_id}**: {int_type} affecting {affected_jur}")

    # Comments section
    comments = measure.get("comments", [])
    if comments:
        lines.append(f"\n## Comments ({len(comments)})\n")
        for comment in comments:
            author = comment.get("author", "Unknown")
            created = comment.get("created", "N/A")[:10]
            text = comment.get("text", "")[:200]  # Truncate
            lines.append(f"- **{author}** ({created}): {text}...")

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
        "| ID | Name | Type | Description |",
        "|-----|------|------|-------------|"
    ]

    for template in results:
        template_id = template.get("id", "N/A")
        name = template.get("name", "Untitled")
        template_type = template.get("type", "N/A")
        description = template.get("description", "")[:60]  # Truncate

        lines.append(f"| {template_id} | {name} | {template_type} | {description} |")

    return "\n".join(lines)
