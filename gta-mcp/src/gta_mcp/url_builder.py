"""URL builder for GTA Activity Tracker and Data Centre deep links.

Constructs filtered URLs that let users browse the full dataset matching
their MCP query, not just the cited interventions. Appended to tool
responses by server.py after formatting.

URL parameter spec: gta-website/utils/const.js FIELDS object.
"""

from datetime import date
from typing import Any, Dict, List, Optional


BASE_AT_URL = "https://globaltradealert.org/activity-tracker"
BASE_DC_URL = "https://globaltradealert.org/data-center"

# Sentinel announcement period that means "no date filter applied"
SENTINEL_ANNOUNCEMENT = ["1900-01-01", "2099-12-31"]

# Maximum HS codes in URL to stay under ~8KB URL length limit
MAX_HS_CODES = 100


def _fixed_defaults() -> str:
    """Return the fixed default query string with current year.

    These are display/aggregation defaults that ensure the AT/DC page loads
    correctly. They cover parameters not exposed in the MCP server (importer,
    exporter, thread, framework, commercial flow, etc.).
    """
    year = date.today().year
    return (
        f"na=0,999&ast=oneplus&nai=all&kim=1&iis=oneplus&ni=1,999"
        f"&ke=1&ies=oneplus&nei=all&ky=1"
        f"&cp=2020,{year}&tp=2022,2022&td=current&cytd=1&iyd=1"
        f"&cv=intervention_id&ct=sum&apit=tree&ij=any&ih=any&type=entries"
    )


def _join_ints(values: List[Any]) -> str:
    """Comma-join a list of values as integers."""
    return ",".join(str(int(v)) for v in values)


def build_dataset_urls(
    filters: Dict[str, Any],
    original_params: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """Build Activity Tracker and Data Centre URLs from API filters.

    Maps the internal filters dict (UN M49 codes, type IDs, HS codes, eval IDs,
    date periods, MAST chapter IDs, sector IDs, etc.) to URL query parameters
    matching the GTA website's const.js FIELDS spec.

    Args:
        filters: The filters dict produced by build_filters() or build_count_filters().
        original_params: The original user params (before ID conversion).

    Returns:
        Dict with 'activity_tracker' and 'data_centre' URL strings,
        or None if no meaningful structured filters exist (e.g., text-only query).
    """
    parts: List[str] = []
    has_meaningful_filter = False

    # --- List params (comma-joined integers) ---
    # Includes both 'implementation_level' (from build_filters / search)
    # and 'implementation_levels' (from build_count_filters / counts).
    list_mappings = [
        ("implementer", "i"),
        ("affected", "a"),
        ("intervention_types", "it"),
        ("gta_evaluation", "ge"),
        ("affected_flow", "af"),
        ("mast_chapters", "mc"),
        ("implementation_level", "il"),
        ("implementation_levels", "il"),
        ("eligible_firms", "ef"),
        ("affected_sectors", "as"),
        ("intervention_id", "id"),
    ]

    seen_url_params: set = set()
    for filters_key, url_param in list_mappings:
        if url_param in seen_url_params:
            continue
        value = filters.get(filters_key)
        if isinstance(value, list) and value:
            parts.append(f"{url_param}={_join_ints(value)}")
            has_meaningful_filter = True
            seen_url_params.add(url_param)

    # --- HS codes (capped at MAX_HS_CODES) ---
    products = filters.get("affected_products")
    if isinstance(products, list) and products:
        codes = products[:MAX_HS_CODES]
        parts.append(f"ap={_join_ints(codes)}")
        has_meaningful_filter = True

    # --- Period params ---
    # Announcement period: skip if sentinel (means "no filter")
    ann_period = filters.get("announcement_period")
    if ann_period and ann_period != SENTINEL_ANNOUNCEMENT:
        parts.append(f"anp={ann_period[0]},{ann_period[1]}")
        has_meaningful_filter = True

    # Implementation period: only present when user explicitly filtered
    impl_period = filters.get("implementation_period")
    if impl_period:
        parts.append(f"ip={impl_period[0]},{impl_period[1]}")
        has_meaningful_filter = True

    # --- In-force date ---
    ifd = filters.get("in_force_on_date")
    if ifd:
        parts.append(f"ifd={ifd}")
        has_meaningful_filter = True

    # If no structured filters were applied, don't generate URLs
    # (e.g., text-only query='Tesla' with no jurisdiction/type/product filters)
    if not has_meaningful_filter:
        return None

    # --- Keep flags ---
    # Default is 1 (include) for all; set to 0 when user explicitly excludes.
    keep_mappings = [
        ("keep_implementer", "ki", 1),
        ("keep_affected", "ka", 1),
        ("keep_intervention_types", "kit", 1),
        ("keep_mast_chapters", "kmc", 1),
        ("keep_implementation_level", "kil", 1),
        ("keep_eligible_firms", "kef", 1),
        ("keep_affected_sectors", "kas", 1),
        ("keep_affected_products", "kap", 1),
        ("keep_intervention_id", "kid", 1),
        ("keep_in_force_on_date", "kifd", 1),
        ("keep_implementation_period_na", "kin", 1),
        ("keep_revocation_na", "krn", 1),
    ]

    for filters_key, url_param, default in keep_mappings:
        value = filters.get(filters_key)
        flag = int(value) if value is not None else default
        parts.append(f"{url_param}={flag}")

    # ko (keep_others) is always 0
    parts.append("ko=0")

    # Append fixed display/aggregation defaults
    parts.append(_fixed_defaults())

    query_string = "&".join(parts)

    return {
        "activity_tracker": f"{BASE_AT_URL}?{query_string}",
        "data_centre": f"{BASE_DC_URL}?{query_string}",
    }


def build_dataset_label(original_params: Dict[str, Any]) -> str:
    """Build a human-readable label from original user params.

    Uses ISO codes and type names directly from the original params
    (before ID conversion) for readability.

    Args:
        original_params: The original user params dict.

    Returns:
        Descriptive label like "USA import tariffs affecting CHN since 2024".
    """
    fragments: List[str] = []

    # Implementing jurisdictions
    impl = original_params.get("implementing_jurisdictions")
    if impl:
        label = ", ".join(impl[:3])
        if len(impl) > 3:
            label += f" +{len(impl) - 3} more"
        fragments.append(label)

    # Intervention types
    types = original_params.get("intervention_types")
    if types:
        label = ", ".join(t.lower() for t in types[:2])
        if len(types) > 2:
            label += f" +{len(types) - 2} more"
        fragments.append(label)

    # MAST chapters (only if no specific intervention types)
    mast = original_params.get("mast_chapters")
    if mast and not types:
        fragments.append(f"MAST {', '.join(str(m) for m in mast)}")

    # GTA evaluation
    evals = original_params.get("gta_evaluation")
    if evals:
        fragments.append("/".join(str(e).lower() for e in evals))

    # Affected jurisdictions
    affected = original_params.get("affected_jurisdictions")
    if affected:
        label = "affecting " + ", ".join(affected[:3])
        if len(affected) > 3:
            label += f" +{len(affected) - 3} more"
        fragments.append(label)

    # Date range
    date_gte = original_params.get("date_announced_gte")
    date_lte = original_params.get("date_announced_lte")
    if date_gte and date_lte:
        fragments.append(f"{date_gte} to {date_lte}")
    elif date_gte:
        fragments.append(f"since {date_gte[:4]}")
    elif date_lte:
        fragments.append(f"until {date_lte}")

    # HS codes count
    products = original_params.get("affected_products")
    if products:
        n = len(products)
        fragments.append(f"{n} HS code{'s' if n != 1 else ''}")

    # Sectors count
    sectors = original_params.get("affected_sectors")
    if sectors:
        fragments.append(f"{len(sectors)} sector{'s' if len(sectors) != 1 else ''}")

    return " | ".join(fragments) if fragments else "matching interventions"


def make_dataset_links_section(
    filters: Dict[str, Any],
    original_params: Dict[str, Any],
) -> str:
    """Build markdown section with Activity Tracker and Data Centre links.

    Each tool call produces ONE labeled link set for its exact filters.
    The label describes what filters are applied so the LLM can present
    multiple links from different tool calls, each clearly identified.

    Args:
        filters: The filters dict produced by build_filters() or build_count_filters().
        original_params: The original user params (before conversion).

    Returns:
        Formatted markdown section, or empty string if no URLs can be built.
    """
    urls = build_dataset_urls(filters, original_params)
    if not urls:
        return ""

    label = build_dataset_label(original_params)

    # Note if HS codes were truncated
    products = filters.get("affected_products")
    truncation = ""
    if products and len(products) > MAX_HS_CODES:
        truncation = f" (top {MAX_HS_CODES} of {len(products)} products shown)"

    return (
        f"\n## Explore Dataset: {label}{truncation}\n\n"
        f"- [Activity Tracker]({urls['activity_tracker']}) — interactive timeline\n"
        f"- [Data Centre]({urls['data_centre']}) — aggregated statistics"
    )


def make_dataset_links_header(
    filters: Dict[str, Any],
    original_params: Dict[str, Any],
) -> str:
    """Build compact labeled dataset link for the TOP of tool responses.

    Each tool call produces ONE labeled link line for its exact filters.
    The label describes what this specific query covers (e.g., "MAST L |
    2026-02-01 to 2026-02-28" or "2026-02-01 to 2026-02-28").

    When the LLM makes multiple tool calls with different filters, each
    response has its own labeled link. The docstring instructs the LLM to
    include ALL unique links — the broadest one as the primary dataset link
    and narrower ones as filtered views.

    Args:
        filters: The filters dict produced by build_filters() or build_count_filters().
        original_params: The original user params (before conversion).

    Returns:
        Single labeled markdown link line, or empty string if no URLs can be built.
    """
    urls = build_dataset_urls(filters, original_params)
    if not urls:
        return ""

    label = build_dataset_label(original_params)

    return (
        f"📊 **Dataset — {label}:** "
        f"[Activity Tracker]({urls['activity_tracker']}) | "
        f"[Data Centre]({urls['data_centre']})"
    )
