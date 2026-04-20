"""Formatters for dpa_mnt outputs (markdown formatting, comment structures)."""

from typing import Optional


# ============================================================================
# Comment Formatters (shared with GTA)
# ============================================================================

def format_issue_comment(
    field: str,
    criticality: str,
    current_value: str,
    suggested_value: str,
    rationale: str,
    source_quote: str,
    source_ref: str
) -> str:
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

*Reviewed by Buzessa Claudini automated review system on {review_date}.*
"""


def truncate_quote(quote: str, max_length: int = 500) -> str:
    if len(quote) <= max_length:
        return quote
    return quote[:max_length] + " [...]"


# ============================================================================
# Review Queue Formatter
# ============================================================================

def format_review_queue(data: dict) -> str:
    """Format review queue results as markdown."""
    results = data.get("results", [])
    count = data.get("count", 0)

    if count == 0:
        return "# DPA Review Queue\n\n*No events awaiting review.*"

    lines = [
        f"# DPA Review Queue ({count} events)\n",
        "| Event ID | Title | Event Type | Action Type | Date Entered Review |",
        "|----------|-------|------------|-------------|---------------------|"
    ]

    for event in results:
        event_id = event.get("event_id", "N/A")
        title = (event.get("event_title") or "Untitled")[:50]
        event_type = (event.get("event_type_name") or "N/A")[:25]
        action_type = (event.get("action_type_name") or "N/A")[:25]

        status_time = event.get("status_time")
        if status_time is None:
            status_time = "N/A"
        elif hasattr(status_time, 'strftime'):
            status_time = status_time.strftime("%Y-%m-%d")
        else:
            status_time = str(status_time)[:10]

        lines.append(f"| {event_id} | {title} | {event_type} | {action_type} | {status_time} |")

    return "\n".join(lines)


# ============================================================================
# Event Detail Formatter
# ============================================================================

def format_event_detail(event_data: dict) -> str:
    """Format complete event details as markdown."""
    if event_data.get("error"):
        return f"# Error\n\n{event_data['error']}"

    event = event_data.get("event", {})
    intervention = event_data.get("intervention", {})
    development = event_data.get("development", {})
    econ_activities = event_data.get("economic_activities", [])
    implementers = event_data.get("implementing_jurisdictions", [])
    policy_areas = event_data.get("policy_areas", [])
    related = event_data.get("related_interventions", [])
    sources = event_data.get("sources", [])
    comments = event_data.get("comments", [])

    event_id = event.get("event_id", "N/A")
    title = event.get("event_title") or "Untitled"

    lines = [
        f"# Event {event_id}: {title}\n",
        f"**Event Type:** {event.get('event_type_name') or 'N/A'}",
        f"**Action Type:** {event.get('action_type_name') or 'N/A'}",
        f"**Government:** {event.get('gov_branch_name') or 'N/A'} / {event.get('gov_body_name') or 'N/A'}",
        f"**Event Date:** {event.get('event_date') or 'N/A'}",
        f"**Status:** {event.get('status_name') or 'N/A'} (ID: {event.get('status_id', 'N/A')})",
        f"**Is Case:** {'Yes' if event.get('is_case') else 'No'}",
        f"**Is Current:** {'Yes' if event.get('is_current') else 'No'}",
        ""
    ]

    # Description
    description = event.get("event_description")
    if description:
        lines.append("## Description\n")
        lines.append(description)
        lines.append("")

    # Intervention details
    if intervention:
        int_title = intervention.get("intervention_title") or "N/A"
        lines.append(f"## Intervention: {int_title}\n")
        lines.append(f"- **Policy Area:** {intervention.get('policy_area_name') or 'N/A'}")
        lines.append(f"- **Instrument:** {intervention.get('intervention_type_name') or 'N/A'}")
        lines.append(f"- **Implementation Level:** {intervention.get('implementation_level_name') or 'N/A'}")
        lines.append(f"- **Current Status:** {intervention.get('current_status_name') or 'N/A'}")

        if econ_activities:
            activities_str = ", ".join(a.get("economic_activity_name", "N/A") for a in econ_activities)
            lines.append(f"- **Economic Activities:** {activities_str}")

        if implementers:
            impl_str = ", ".join(
                f"{j.get('jurisdiction_name', 'N/A')} ({j.get('iso_code', '')})"
                for j in implementers
            )
            lines.append(f"- **Implementing Jurisdictions:** {impl_str}")

        if policy_areas:
            pa_str = ", ".join(p.get("policy_area_name", "N/A") for p in policy_areas)
            lines.append(f"- **Additional Policy Areas:** {pa_str}")

        issues = event_data.get("issues", [])
        if issues:
            issue_str = ", ".join(i.get("issue_name", "N/A") for i in issues)
            lines.append(f"- **Thematic Issues:** {issue_str}")

        rationales = event_data.get("rationales", [])
        if rationales:
            rat_str = ", ".join(r.get("rationale_name", "N/A") for r in rationales)
            lines.append(f"- **Stated Rationales:** {rat_str}")

        lines.append("")

    # Development
    if development:
        dev_name = development.get("development_name") or "N/A"
        lines.append(f"## Development\n")
        lines.append(f"**Name:** {dev_name}")
        lines.append("")

    # Related interventions
    if related:
        lines.append(f"## Related Interventions ({len(related)})\n")
        for rel in related:
            rel_id = rel.get("related_intervention_id", "N/A")
            rel_title = rel.get("intervention_title") or "N/A"
            rel_type = rel.get("relationship_name") or "N/A"
            lines.append(f"- INT-{rel_id}: {rel_title} [{rel_type}]")
        lines.append("")

    # Agents/Firms
    agents = event_data.get("agents", [])
    if agents:
        lines.append(f"## Agents/Firms ({len(agents)})\n")
        for agent in agents:
            atype = agent.get("agent_type_name") or "Unknown type"
            role = agent.get("role_name") or ""
            firm = agent.get("firm_name")
            parts = [f"**{atype}**"]
            if firm:
                parts.append(f"({firm})")
            if role:
                parts.append(f"[{role}]")
            lines.append(f"- {' '.join(parts)}")
        lines.append("")

    # Sources
    if sources:
        lines.append(f"## Sources ({len(sources)})\n")
        for i, src in enumerate(sources):
            name = src.get("source_name") or "Unnamed"
            url = src.get("source_url") or "N/A"
            institution = src.get("institution_name") or ""
            source_date = src.get("source_date")
            date_str = ""
            if source_date:
                if hasattr(source_date, 'strftime'):
                    date_str = f" ({source_date.strftime('%Y-%m-%d')})"
                else:
                    date_str = f" ({str(source_date)[:10]})"

            inst_str = f" - {institution}" if institution else ""
            lines.append(f"- **[{i}]** {name}{inst_str}{date_str}")
            lines.append(f"  URL: {url}")
            if src.get("file_url"):
                lines.append(f"  File: {src['file_url']}")
        lines.append("")
    else:
        lines.append("## Sources\n")
        lines.append("*No sources linked*")
        lines.append("")

    # Comments
    if comments:
        lines.append(f"## Comments ({len(comments)})\n")
        for comment in comments:
            author = comment.get("author_name") or "Unknown"
            created = comment.get("creation_time")
            if created is None:
                created = "N/A"
            elif hasattr(created, 'strftime'):
                created = created.strftime("%Y-%m-%d %H:%M")
            else:
                created = str(created)[:16]
            text = comment.get("comment_value") or ""
            text = text[:300]
            lines.append(f"### {author} ({created})")
            lines.append(f"{text}{'...' if len(text) >= 300 else ''}\n")

    return "\n".join(lines)


# ============================================================================
# Intervention Context Formatter
# ============================================================================

def format_intervention_context(data: dict) -> str:
    """Format intervention context with all sibling events for Gate 0 review."""
    if data.get("error"):
        return f"# Error\n\n{data['error']}"

    intervention = data.get("intervention", {})
    development = data.get("development", {})
    implementers = data.get("implementing_jurisdictions", [])
    econ_activities = data.get("economic_activities", [])
    events = data.get("events", [])
    related = data.get("related_interventions", [])

    int_id = intervention.get("intervention_id", "N/A")
    int_title = intervention.get("intervention_title") or "Untitled"

    lines = [
        f"# Intervention Context: {int_title} (INT-{int_id})\n",
        f"**Policy Area:** {intervention.get('policy_area_name') or 'N/A'}",
        f"**Instrument:** {intervention.get('intervention_type_name') or 'N/A'}",
        f"**Implementation Level:** {intervention.get('implementation_level_name') or 'N/A'}",
        f"**Current Status:** {intervention.get('current_status_name') or 'N/A'}",
    ]

    if implementers:
        impl_str = ", ".join(
            f"{j.get('jurisdiction_name', 'N/A')} ({j.get('iso_code', '')})"
            for j in implementers
        )
        lines.append(f"**Implementing Jurisdictions:** {impl_str}")

    if econ_activities:
        activities_str = ", ".join(a.get("economic_activity_name", "N/A") for a in econ_activities)
        lines.append(f"**Economic Activities:** {activities_str}")

    if development:
        lines.append(f"**Development:** {development.get('development_name') or 'N/A'}")

    lines.append("")

    # Events timeline
    published = [e for e in events if e.get("status_id") == 7]
    in_review = [e for e in events if e.get("status_id") == 2]
    other = [e for e in events if e.get("status_id") not in (7, 2)]

    lines.append(f"## Event Timeline ({len(events)} events)\n")
    lines.append("| Event ID | Date | Action Type | Event Type | Status | Title |")
    lines.append("|----------|------|-------------|------------|--------|-------|")

    for event in events:
        eid = event.get("event_id", "N/A")
        date = event.get("event_date")
        if date and hasattr(date, 'strftime'):
            date = date.strftime("%Y-%m-%d")
        elif date:
            date = str(date)[:10]
        else:
            date = "N/A"

        action = (event.get("action_type_name") or "N/A")[:25]
        etype = (event.get("event_type_name") or "N/A")[:20]
        status = event.get("status_name") or "N/A"
        title = (event.get("event_title") or "Untitled")[:50]

        # Mark published events as verified context
        marker = ""
        if event.get("status_id") == 7:
            marker = " [PUBLISHED]"
        elif event.get("status_id") == 2:
            marker = " [IN REVIEW]"

        lines.append(f"| {eid} | {date} | {action} | {etype} | {status}{marker} | {title} |")

    lines.append("")

    # Summary counts
    lines.append(f"**Published (verified context):** {len(published)} events")
    lines.append(f"**In review:** {len(in_review)} events")
    if other:
        lines.append(f"**Other status:** {len(other)} events")
    lines.append("")

    # Published event descriptions (verified context for the reviewer)
    if published:
        lines.append("## Published Events (Verified Context)\n")
        lines.append("These events have been reviewed and published. Use them as ground truth for consistency checks.\n")
        for event in published:
            eid = event.get("event_id", "N/A")
            title = event.get("event_title") or "Untitled"
            desc = event.get("event_description") or "*No description*"
            action = event.get("action_type_name") or "N/A"
            date = event.get("event_date")
            if date and hasattr(date, 'strftime'):
                date = date.strftime("%Y-%m-%d")
            elif date:
                date = str(date)[:10]
            else:
                date = "N/A"

            lines.append(f"### Event {eid}: {title}")
            lines.append(f"**Action Type:** {action} | **Date:** {date}\n")
            lines.append(desc)
            lines.append("")

    # Related interventions
    if related:
        lines.append(f"## Related Interventions ({len(related)})\n")
        for rel in related:
            rel_id = rel.get("related_intervention_id", "N/A")
            rel_title = rel.get("intervention_title") or "N/A"
            rel_type = rel.get("relationship_name") or "N/A"
            lines.append(f"- INT-{rel_id}: {rel_title} [{rel_type}]")
        lines.append("")

    # Development siblings (other interventions sharing same development_id)
    dev_siblings = data.get("development_siblings", [])
    if dev_siblings:
        lines.append(f"## Development Siblings ({len(dev_siblings)} other interventions in same development)\n")
        for sib in dev_siblings:
            sid = sib.get("intervention_id", "N/A")
            stitle = sib.get("intervention_title") or "N/A"
            spa = sib.get("policy_area_name") or "N/A"
            sinst = sib.get("intervention_type_name") or "N/A"
            sstatus = sib.get("current_status_name") or "N/A"
            lines.append(f"- INT-{sid}: {stitle} | {spa} | {sinst} | {sstatus}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# Source Result Formatter
# ============================================================================

def format_source_result(source_result) -> str:
    """Format source retrieval result as markdown."""
    lines = [
        f"# Official Source\n",
        f"**Type:** {source_result.source_type}",
        f"**URL:** {source_result.source_url}",
        f"**Content Type:** {source_result.content_type}\n"
    ]

    if source_result.content:
        lines.append("## Extracted Content\n")
        content = source_result.content
        if len(content) > 50000:
            content = content[:50000] + "\n\n[... content truncated for brevity ...]"
        lines.append(content)
    else:
        lines.append("*Content not fetched (fetch_content=False)*")

    return "\n".join(lines)


# ============================================================================
# Templates Formatter
# ============================================================================

def format_templates(data: dict) -> str:
    """Format comment templates as markdown."""
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
        name = template.get("template_name") or "Untitled"
        is_checklist = "Yes" if template.get("is_checklist") else "No"
        text = template.get("template_text") or ""
        preview = text[:50].replace("\n", " ")
        lines.append(f"| {template_id} | {name} | {is_checklist} | {preview}... |")

    return "\n".join(lines)
