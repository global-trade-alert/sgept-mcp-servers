"""Formatters for gta_mnt outputs (markdown formatting, comment structures)."""

from typing import Optional, Any


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

def format_step1_queue(data: dict, queue_label: str = "Step 1") -> str:
    """Format review queue results as markdown.

    Args:
        data: API response dict with 'results' and 'count'
        queue_label: Label for the queue (e.g., 'Step 1', 'Step 2')

    Returns:
        Markdown-formatted queue listing
    """
    results = data.get("results", [])
    count = data.get("count", 0)

    if count == 0:
        return f"# {queue_label} Review Queue\n\n*No measures awaiting {queue_label} review.*"

    lines = [
        f"# {queue_label} Review Queue ({count} measures)\n",
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

    # Get source info
    source_info = measure.get("source_info", {})

    # Primary citation: source_markdown contains the full formatted citation
    # (e.g. "Author (Date). TITLE. Publisher (Retrieved date): URL")
    source_markdown = measure.get("source_markdown") or ""
    source_text = measure.get("source_text") or ""
    source_field = measure.get("source") or ""
    source_content = source_markdown or source_text or source_field

    lines = [
        f"# StateAct {state_act_id}: {title}\n",
        f"**Implementing Jurisdiction:** {impl_jur_str}",
        f"**Status:** {status_name} (ID: {status_id})",
        f"**Official Source:** {'Yes' if is_official else 'No'}",
        f"**Announcement Date:** {announcement_date or 'N/A'}",
        "",
        "## Description",
        description,
        ""
    ]

    # Add source citations section
    if source_content:
        lines.append("\n## Source Citations\n")
        lines.append(source_content)
        lines.append("")

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
            # Levels: prefer level_rows (from api_intervention_level) over inline prior_level/new_level
            level_rows = intervention.get("level_rows", [])
            if level_rows:
                # Use first level row for primary display
                lr = level_rows[0]
                prior_level = lr.get("prior_level")
                new_level = lr.get("new_level")
                unit_id = lr.get("unit_id")
                unit_name = lr.get("unit_name")
            else:
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
            # MAST chapter/subchapter
            chapter_name = intervention.get("chapter_name") or "N/A"
            chapter_id = intervention.get("chapter_id")
            subchapter_name = intervention.get("subchapter_name") or "N/A"
            subchapter_id = intervention.get("subchapter_id")
            lines.append(f"- **MAST Chapter:** {chapter_name} (ID: {chapter_id})")
            if subchapter_id:
                lines.append(f"- **MAST Subchapter:** {subchapter_name} (ID: {subchapter_id})")
            # Announced as temporary
            announced_temp = intervention.get("announced_as_temporary")
            if announced_temp is not None:
                lines.append(f"- **Announced as Temporary:** {'Yes' if announced_temp else 'No'}")
            else:
                lines.append(f"- **Announced as Temporary:** N/A")
            # Horizontal flag
            is_horiz = intervention.get("is_horizontal")
            if is_horiz is not None:
                lines.append(f"- **Horizontal:** {'Yes' if is_horiz else 'No'}")
            else:
                lines.append(f"- **Horizontal:** N/A")
            lines.append(f"- **Inception Date:** {inception_date or 'N/A'}")
            lines.append(f"- **Removal Date:** {removal_date or 'N/A'}")
            if prior_level is not None or new_level is not None:
                lines.append(f"- **Prior Level:** {prior_level if prior_level is not None else 'N/A'}")
                lines.append(f"- **New Level:** {new_level if new_level is not None else 'N/A'}")
                lines.append(f"- **Unit:** {unit_str}")
                if level_rows:
                    level_type = level_rows[0].get("level_type_name")
                    if level_type:
                        lines.append(f"- **Level Type:** {level_type}")
                    if len(level_rows) > 1:
                        lines.append(f"- **Additional level rows:** {len(level_rows) - 1}")
            lines.append("")

            # Affected Jurisdictions section — ALWAYS rendered
            affected_jurs = intervention.get("affected_jurisdictions", [])
            lines.append("#### Affected Jurisdictions")
            if affected_jurs:
                for aj in affected_jurs:
                    name = aj.get("jurisdiction_name") or aj.get("iso_code") or "Unknown"
                    iso = aj.get("iso_code") or ""
                    type_name = aj.get("type_name")
                    if type_name:
                        lines.append(f"- {name} ({iso}) [{type_name}]")
                    else:
                        lines.append(f"- {name} ({iso})")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Distorted Markets section — ALWAYS rendered
            distorted_markets = intervention.get("distorted_markets", [])
            lines.append("#### Distorted Markets")
            if distorted_markets:
                for dm in distorted_markets:
                    name = dm.get("jurisdiction_name") or dm.get("iso_code") or "Unknown"
                    iso = dm.get("iso_code") or ""
                    type_name = dm.get("type_name")
                    if type_name:
                        lines.append(f"- {name} ({iso}) [{type_name}]")
                    else:
                        lines.append(f"- {name} ({iso})")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Products section (HS codes) — ALWAYS rendered
            products = intervention.get("products", [])
            lines.append("#### Products")
            if products:
                for prod in products:
                    pid = prod.get("product_id", "?")
                    pdesc = prod.get("product_description", "")
                    lines.append(f"- HS {pid}: {pdesc}")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Sectors section (CPC) — ALWAYS rendered
            sectors = intervention.get("sectors", [])
            lines.append("#### Sectors")
            if sectors:
                for sec in sectors:
                    sid = sec.get("sector_id", "?")
                    sname = sec.get("sector_name", "")
                    stype = sec.get("sector_type", "")
                    type_label = f" [{stype}]" if stype and stype != "N" else ""
                    lines.append(f"- {sid}: {sname}{type_label}")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Firms section — ALWAYS rendered
            firms = intervention.get("firms", [])
            lines.append("#### Firms")
            if firms:
                for firm in firms:
                    firm_name = firm.get("firm_name") or "Unknown"
                    role_name = firm.get("role_name")
                    if role_name:
                        lines.append(f"- {firm_name} [{role_name}]")
                    else:
                        lines.append(f"- {firm_name}")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Rationale Tags section — ALWAYS rendered
            rationales = intervention.get("rationales", [])
            lines.append("#### Rationale Tags")
            if rationales:
                for rat in rationales:
                    lines.append(f"- {rat.get('rationale_name', 'Unknown')} (ID: {rat.get('rationale_id')})")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Locations section (subnational taxonomy) — ALWAYS rendered
            locations = intervention.get("locations", [])
            lines.append("#### Locations")
            if locations:
                for loc in locations:
                    loc_name = loc.get("location_name") or "Unknown"
                    loc_type = loc.get("location_type_name")
                    if loc_type:
                        lines.append(f"- {loc_name} [{loc_type}]")
                    else:
                        lines.append(f"- {loc_name}")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Description section (full text, no truncation)
            if int_description:
                lines.append("#### Description")
                lines.append(int_description)
                lines.append("")

    # Motive quotes section (state act level)
    motive_quotes = measure.get("motive_quotes", [])
    if motive_quotes:
        lines.append(f"\n## Motive Quotes ({len(motive_quotes)})\n")
        for mq in motive_quotes:
            quote = mq.get("stated_motive_name", "")
            url = mq.get("stated_motive_url", "")
            lines.append(f"- \"{quote}\"")
            if url:
                lines.append(f"  Source: {url}")
        lines.append("")
    else:
        lines.append("\n## Motive Quotes\n")
        lines.append("*No motive quotes recorded*\n")

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
        for i, src in enumerate(linked_sources):
            url = src.get("source_url", "N/A")
            file_name = src.get("file_name")
            is_collected = src.get("is_collected")
            is_file = src.get("is_file")

            # Format source line with index and file name
            if file_name:
                lines.append(f"- **[{i}] {file_name}**: {url}")
            else:
                status_parts = []
                if is_collected or is_file:
                    status_parts.append("archived")
                status = f" ({', '.join(status_parts)})" if status_parts else ""
                lines.append(f"- **[{i}]** {url}{status}")
    else:
        lines.append("\n## Linked Sources\n")
        lines.append("*No linked sources found in database*")

    # Field Manifest — tells the reviewer exactly what data was returned
    lines.append("\n---\n## Field Manifest\n")
    lines.append("Fields returned by this tool (assess ONLY these):\n")

    sa_fields = [
        ("title", measure.get("title") is not None),
        ("announcement_description", measure.get("description") is not None),
        ("announcement_date", measure.get("announcement_date") is not None),
        ("is_source_official", measure.get("is_source_official") is not None),
        ("implementing_jurisdictions", bool(measure.get("implementing_jurisdictions"))),
        ("motive_quotes", bool(measure.get("motive_quotes"))),
        ("related_state_acts", bool(measure.get("related_state_acts"))),
        ("linked_sources", bool(linked_sources)),
    ]
    lines.append("**State Act Level:**")
    for field_name, present in sa_fields:
        lines.append(f"- `{field_name}`: {'PRESENT' if present else 'EMPTY'}")

    if interventions:
        sample = interventions[0]
        int_fields = [
            ("intervention_type", sample.get("type_name") is not None),
            ("evaluation", sample.get("evaluation_name") is not None),
            ("affected_flow", sample.get("affected_flow_name") is not None),
            ("eligible_firms", sample.get("eligible_firms_name") is not None),
            ("implementation_level", sample.get("implementation_level_name") is not None),
            ("chapter_id/chapter_name", sample.get("chapter_id") is not None),
            ("subchapter_id/subchapter_name", sample.get("subchapter_id") is not None),
            ("announced_as_temporary", sample.get("announced_as_temporary") is not None),
            ("is_horizontal", sample.get("is_horizontal") is not None),
            ("level_rows", bool(sample.get("level_rows"))),
            ("affected_jurisdictions", bool(sample.get("affected_jurisdictions"))),
            ("distorted_markets", bool(sample.get("distorted_markets"))),
            ("products", bool(sample.get("products"))),
            ("sectors", bool(sample.get("sectors"))),
            ("firms", bool(sample.get("firms"))),
            ("rationales", bool(sample.get("rationales"))),
            ("locations", bool(sample.get("locations"))),
        ]
        lines.append("\n**Intervention Level (sample from first intervention):**")
        for field_name, present in int_fields:
            lines.append(f"- `{field_name}`: {'PRESENT' if present else 'EMPTY'}")

    lines.append("\n**CONSTRAINT:** Sections marked `*None recorded*` mean the tool queried the database and found no data. You may flag genuinely missing data. But NEVER claim data exists when the section shows `*None recorded*` — that IS the database state.")

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

def format_guessed_hs_codes(data: Any) -> str:
    """Format Bastiat API HS code guess results as markdown.

    Args:
        data: Bastiat API response dict.

    Returns:
        Markdown-formatted HS code suggestions.
    """
    if not data:
        return "# HS Code Guess\n\n*No results returned from Bastiat API.*"

    # Handle various response shapes from the API
    hs_codes = data.get("hs_codes", data.get("results", []))

    if not hs_codes:
        return "# HS Code Guess\n\n*No HS codes identified for the given text.*"

    lines = [
        f"# AI-Guessed HS Codes ({len(hs_codes)} results)\n",
        "| HS Code | Description | Confidence | Level |",
        "|---------|-------------|------------|-------|",
    ]

    # Build ready-to-use product IDs list
    product_ids = []

    for code in hs_codes:
        hs_code = code.get("hs_code", code.get("code", "N/A"))
        description = code.get("description", code.get("name", "N/A"))
        confidence = code.get("confidence", code.get("score", "N/A"))
        level = code.get("level", code.get("hs_level", len(str(hs_code))))

        # Format confidence as percentage if numeric
        if isinstance(confidence, (int, float)):
            confidence_str = f"{confidence:.0%}" if confidence <= 1 else f"{confidence}%"
        else:
            confidence_str = str(confidence)

        lines.append(f"| {hs_code} | {description} | {confidence_str} | {level}-digit |")
        product_ids.append(str(hs_code))

    # Add ready-to-use lookup hint
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("Use `gta_mnt_lookup(table='product', query='<hs_code>')` to find the database product_id for each code.")
    lines.append("")
    lines.append(f"**Codes for lookup:** {', '.join(product_ids)}")

    return "\n".join(lines)


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
