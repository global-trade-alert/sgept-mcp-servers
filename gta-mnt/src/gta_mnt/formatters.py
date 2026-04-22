"""Formatters for gta_mnt outputs (markdown formatting, comment structures)."""

from typing import Optional, Any


# Hard cap on tool-response size. LLM clients (including the MCP host that
# drives the Sancho review agent) start silently dropping or summarising
# oversized responses beyond ~100K characters. Producing a truncated
# response with an explicit pagination hint is strictly better than shipping
# a 400KB measure detail that the agent then misreads.
CHARACTER_LIMIT = 100_000


def _truncate(text: str, hint: str) -> str:
    """Cap `text` at CHARACTER_LIMIT. Append `hint` when truncation occurs."""
    if len(text) <= CHARACTER_LIMIT:
        return text
    marker = f"\n\n---\n[truncated: response exceeded {CHARACTER_LIMIT:,} characters. {hint}]"
    keep = CHARACTER_LIMIT - len(marker)
    return text[:keep] + marker


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

    return _truncate(
        "\n".join(lines),
        hint="use `limit` and `offset` to paginate further.",
    )


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

    # Canonical source citation text: api_state_act_source_log_new (StateActSource)
    # is what the admin dashboard displays. Legacy columns (source, source_markdown
    # on api_state_act_log) are retained only as a fallback for pre-migration entries.
    state_act_sources = measure.get("state_act_sources") or []
    if state_act_sources:
        source_content = '\n\n'.join(
            (s.get('source') or s.get('source_markdown') or '').strip()
            for s in state_act_sources
            if (s.get('source') or s.get('source_markdown'))
        )
    else:
        source_markdown = measure.get("source_markdown") or ""
        source_text = measure.get("source_text") or ""
        source_field = measure.get("source") or ""
        source_content = source_markdown or source_text or source_field

    author_id = measure.get("author_id")
    author_name = measure.get("author_name") or "Unknown"

    lines = [
        f"# StateAct {state_act_id}: {title}\n",
        f"**Author:** {author_name} (ID: {author_id})" if author_id else "**Author:** Unknown",
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
            # Intervention area (goods/services/procurement/migration)
            area_name = intervention.get("intervention_area_name")
            area_id = intervention.get("intervention_area_id")
            if area_name or area_id:
                lines.append(f"- **Intervention Area:** {area_name or 'N/A'} (ID: {area_id})")
            # Intervention-level default AJ/DM type + freeze flags (applied post-recalculation)
            default_aj = intervention.get("default_aj_type")
            default_dm = intervention.get("default_dm_type")
            freeze_aj = intervention.get("freeze_aj")
            freeze_dm = intervention.get("freeze_dm")
            _type_label = {1: "Inferred", 2: "Targeted", 3: "Excluded", 4: "Incidental"}
            if default_aj is not None:
                lines.append(
                    f"- **Default AJ Type:** {_type_label.get(default_aj, default_aj)} ({default_aj})"
                    + (f"  |  **Freeze AJ:** {'Yes' if freeze_aj else 'No'}" if freeze_aj is not None else "")
                )
            if default_dm is not None:
                lines.append(
                    f"- **Default DM Type:** {_type_label.get(default_dm, default_dm)} ({default_dm})"
                    + (f"  |  **Freeze DM:** {'Yes' if freeze_dm else 'No'}" if freeze_dm is not None else "")
                )
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

            # Products section (HS6) — ALWAYS rendered, with per-product tariff fields
            products = intervention.get("products", [])
            lines.append("#### Products (HS6)")
            if products:
                for prod in products:
                    pid = prod.get("product_id", "?")
                    pdesc = prod.get("product_description", "")
                    prior = prod.get("prior_level")
                    new = prod.get("new_level")
                    unit = prod.get("product_unit_name")
                    flags = []
                    if prod.get("is_tariff_peak"):
                        flags.append("tariff_peak")
                    if prod.get("is_tariff_line_official"):
                        flags.append("official")
                    if prod.get("is_positively_affected"):
                        flags.append("positively_affected")
                    if prod.get("is_investigated_only"):
                        flags.append("investigated_only")
                    suffix_parts = []
                    if prior is not None or new is not None:
                        prior_s = prior if prior is not None else "—"
                        new_s = new if new is not None else "—"
                        unit_s = f" {unit}" if unit else ""
                        suffix_parts.append(f"{prior_s} → {new_s}{unit_s}")
                    if flags:
                        suffix_parts.append(f"[{', '.join(flags)}]")
                    suffix = f"  |  {' '.join(suffix_parts)}" if suffix_parts else ""
                    lines.append(f"- HS {pid}: {pdesc}{suffix}")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Higher-level tariff lines (HS8/HS10/HS12/HS14)
            for level in (8, 10, 12, 14):
                key = f"products_level{level}"
                rows = intervention.get(key) or []
                if not rows:
                    continue
                lines.append(f"#### Products (HS{level} tariff lines)")
                for r in rows:
                    hs = r.get("hs_code") or r.get("composite_id")
                    jur = r.get("jurisdiction_suffix")
                    prior = r.get("prior_value")
                    new = r.get("new_value")
                    unit = r.get("unit_name")
                    prior_s = prior if prior is not None else "—"
                    new_s = new if new is not None else "—"
                    unit_s = f" {unit}" if unit else ""
                    jur_s = f" (jur {jur})" if jur else ""
                    lines.append(f"- HS{level} {hs}{jur_s}: {prior_s} → {new_s}{unit_s}")
                lines.append("")

            # Sectors section (CPC) — ALWAYS rendered
            # Type legend: N=Normal, A=Added, D=Deleted
            sectors = intervention.get("sectors", [])
            lines.append("#### Sectors")
            if sectors:
                _sector_type_label = {"N": "Normal", "A": "Added", "D": "Deleted"}
                for sec in sectors:
                    sid = sec.get("sector_id", "?")
                    sname = sec.get("sector_name", "")
                    stype = sec.get("sector_type", "")
                    type_readable = _sector_type_label.get(stype, stype)
                    type_label = f" [{type_readable}]" if stype else ""
                    if sec.get("is_investigated_only"):
                        type_label += " [investigated_only]"
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
                    jur_iso = loc.get("jurisdiction_iso") or ""
                    jur_name = loc.get("jurisdiction_name") or ""
                    jur_suffix = f" — {jur_name} ({jur_iso})" if jur_name else ""
                    if loc_type:
                        lines.append(f"- {loc_name} [{loc_type}]{jur_suffix}")
                    else:
                        lines.append(f"- {loc_name}{jur_suffix}")
            else:
                lines.append("*None recorded*")
            lines.append("")

            # Themes
            themes = intervention.get("themes") or []
            if themes:
                lines.append("#### Themes")
                for tid in themes:
                    lines.append(f"- theme_id {tid}")
                lines.append("")

            # Multi-date events (amendments, staged implementation)
            int_dates = intervention.get("intervention_dates") or []
            if int_dates:
                lines.append("#### Multi-date Events")
                for d in int_dates:
                    date_val = d.get("date")
                    dtn = d.get("date_type_name") or d.get("type_id")
                    lines.append(f"- {date_val}: {dtn}")
                lines.append("")

            # Investigation status history (trade-defence lifecycle)
            inv_hist = intervention.get("investigation_history") or []
            if inv_hist:
                lines.append("#### Investigation Status History")
                for h in inv_hist:
                    lines.append(f"- {h.get('date')}: status_id {h.get('investigation_status_id')}")
                lines.append("")

            # Description section — render per-update structure when the intervention
            # has multiple InterventionDescription rows in api_intervention_description_log.
            description_rows = intervention.get("description_rows") or []
            if len(description_rows) > 1:
                lines.append(f"#### Description ({len(description_rows)} updates)")
                lines.append("")
                for r in description_rows:
                    order_nr = r.get("order_nr")
                    r_status = r.get("status") or "?"
                    created = r.get("datetime_created")
                    modified = r.get("datetime_modified")
                    created_str = created.strftime("%Y-%m-%d") if hasattr(created, "strftime") else (str(created)[:10] if created else "?")
                    modified_str = modified.strftime("%Y-%m-%d") if hasattr(modified, "strftime") else (str(modified)[:10] if modified else "?")
                    lines.append(
                        f"**Update {order_nr}** · status: {r_status} · created: {created_str} · modified: {modified_str}"
                    )
                    for d in r.get("dates") or []:
                        d_date = d.get("date")
                        d_type = d.get("date_type_name") or d.get("date_type_id") or "?"
                        d_date_str = d_date.strftime("%Y-%m-%d") if hasattr(d_date, "strftime") else (str(d_date) if d_date else "?")
                        lines.append(f"- {d_date_str}: {d_type}")
                    body = r.get("description_markdown") or r.get("description") or ""
                    if body:
                        lines.append("")
                        lines.append(body)
                    lines.append("")
            elif int_description:
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
        ("evaluation_id (state act)", measure.get("evaluation_id") is not None),
        ("implementing_jurisdictions", bool(measure.get("implementing_jurisdictions"))),
        ("motive_quotes", bool(measure.get("motive_quotes"))),
        ("related_state_acts", bool(measure.get("related_state_acts"))),
        ("state_act_sources (citation text)", bool(measure.get("state_act_sources"))),
        ("source_citations (URL index)", bool(measure.get("source_citations"))),
        ("linked_sources (files)", bool(linked_sources)),
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
            ("intervention_area", sample.get("intervention_area_name") is not None),
            ("chapter_id/chapter_name", sample.get("chapter_id") is not None),
            ("subchapter_id/subchapter_name", sample.get("subchapter_id") is not None),
            ("announced_as_temporary", sample.get("announced_as_temporary") is not None),
            ("is_horizontal", sample.get("is_horizontal") is not None),
            ("freeze_aj", sample.get("freeze_aj") is not None),
            ("freeze_dm", sample.get("freeze_dm") is not None),
            ("default_aj_type", sample.get("default_aj_type") is not None),
            ("default_dm_type", sample.get("default_dm_type") is not None),
            ("description (from api_intervention_description_log)", bool(sample.get("description_rows"))),
            ("level_rows", bool(sample.get("level_rows"))),
            ("affected_jurisdictions", bool(sample.get("affected_jurisdictions"))),
            ("distorted_markets", bool(sample.get("distorted_markets"))),
            ("products (HS6 with per-product levels)", bool(sample.get("products"))),
            ("products_level8", bool(sample.get("products_level8"))),
            ("products_level10", bool(sample.get("products_level10"))),
            ("products_level12", bool(sample.get("products_level12"))),
            ("products_level14", bool(sample.get("products_level14"))),
            ("sectors", bool(sample.get("sectors"))),
            ("firms", bool(sample.get("firms"))),
            ("rationales", bool(sample.get("rationales"))),
            ("locations (with jurisdiction)", bool(sample.get("locations"))),
            ("themes", bool(sample.get("themes"))),
            ("intervention_dates (multi-date log)", bool(sample.get("intervention_dates"))),
            ("investigation_history", bool(sample.get("investigation_history"))),
        ]
        lines.append("\n**Intervention Level (sample from first intervention):**")
        for field_name, present in int_fields:
            lines.append(f"- `{field_name}`: {'PRESENT' if present else 'EMPTY'}")

    lines.append("\n**CONSTRAINT:** Sections marked `*None recorded*` mean the tool queried the database and found no data. You may flag genuinely missing data. But NEVER claim data exists when the section shows `*None recorded*` — that IS the database state.")

    return _truncate(
        "\n".join(lines),
        hint="re-call gta_mnt_get_measure with include_interventions=False or include_comments=False for a smaller payload.",
    )


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
        lines.append(source_result.content)
    else:
        lines.append("*Content not fetched (fetch_content=False)*")

    return _truncate(
        "\n".join(lines),
        hint="re-call gta_mnt_get_source with fetch_content=False, then read the archived file at the returned path.",
    )


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
