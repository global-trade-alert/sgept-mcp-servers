"""HS code lookup tool for searching product codes by keyword, chapter, or code prefix."""

import json
from pathlib import Path
from typing import Optional

# Lazy-loaded data cache
_HS_DATA: Optional[dict] = None


def _get_data_dir() -> Path:
    """Get the path to the data directory."""
    current_file = Path(__file__)
    # Installed: src/gta_mcp/hs_lookup.py → gta_mcp/resources/data/
    installed_path = current_file.parent / "resources" / "data"
    if installed_path.is_dir():
        return installed_path
    # Development: src/gta_mcp/hs_lookup.py → ../../resources/data/
    dev_path = current_file.parent.parent.parent / "resources" / "data"
    if dev_path.is_dir():
        return dev_path
    return dev_path


def _load_hs_data() -> dict:
    """Load HS code data from JSON file (lazy, cached)."""
    global _HS_DATA
    if _HS_DATA is None:
        data_path = _get_data_dir() / "hs_codes.json"
        if not data_path.exists():
            raise FileNotFoundError(
                f"HS codes data file not found at {data_path}. "
                "Run qa/extract_reference_data.py to generate it."
            )
        with open(data_path, "r", encoding="utf-8") as f:
            _HS_DATA = json.load(f)
    return _HS_DATA


def search_hs_codes(search_term: str, max_results: int = 50) -> str:
    """Search HS codes by keyword, chapter number, or code prefix.

    Args:
        search_term: Keyword (e.g., 'lithium'), chapter number (e.g., '28'),
                     or code prefix (e.g., '8541')
        max_results: Maximum results to return (default 50)

    Returns:
        Markdown-formatted table of matching HS codes with usage guidance.
    """
    data = _load_hs_data()
    term_lower = search_term.strip().lower()

    # Detect search mode
    is_numeric = term_lower.replace(" ", "").isdigit()
    numeric_term = term_lower.replace(" ", "") if is_numeric else None

    matches = []

    # Search chapters
    for ch in data["chapters"]:
        if _matches(ch["description"], ch["code"], str(ch["id"]), term_lower, numeric_term, is_numeric):
            matches.append({
                "code": ch["code"],
                "id": ch["id"],
                "description": ch["description"],
                "level": "Chapter",
                "chapter": ch["code"],
            })

    # Search headings
    for hd in data["headings"]:
        if _matches(hd["description"], hd["code"], str(hd["id"]), term_lower, numeric_term, is_numeric):
            matches.append({
                "code": hd["code"],
                "id": hd["id"],
                "description": hd["description"],
                "level": "Heading",
                "chapter": hd["chapter_code"],
            })

    # Search subheadings
    for sh in data["subheadings"]:
        if _matches(sh["description"], sh["code"], str(sh["id"]), term_lower, numeric_term, is_numeric):
            matches.append({
                "code": sh["code"],
                "id": sh["id"],
                "description": sh["description"],
                "level": "Subheading",
                "chapter": sh["chapter_code"],
            })

    if not matches:
        return (
            f"No HS codes found matching '{search_term}'.\n\n"
            "Tips:\n"
            "- Try broader terms (e.g., 'steel' instead of 'steel rod')\n"
            "- Try the chapter number (e.g., '72' for iron and steel)\n"
            "- Try a code prefix (e.g., '8541' for semiconductor devices)\n"
        )

    # Sort: chapters first, then headings, then subheadings
    level_order = {"Chapter": 0, "Heading": 1, "Subheading": 2}
    matches.sort(key=lambda m: (level_order[m["level"]], m["id"]))

    # Truncate to max_results
    total = len(matches)
    matches = matches[:max_results]

    # Format as markdown table
    lines = [f"Found {total} HS codes matching \"{search_term}\""]
    if total > max_results:
        lines.append(f"(showing first {max_results})")
    lines.append("")
    lines.append("| Code | Description | Level | Chapter |")
    lines.append("|------|-------------|-------|---------|")
    for m in matches:
        desc = m["description"][:80] + "..." if len(m["description"]) > 80 else m["description"]
        lines.append(f"| {m['code']} | {desc} | {m['level']} | {m['chapter']} |")

    # Add usage guidance
    subheading_ids = [m["id"] for m in matches if m["level"] == "Subheading"]
    heading_ids = [m["id"] for m in matches if m["level"] == "Heading"]

    lines.append("")
    if subheading_ids:
        ids_str = ", ".join(str(i) for i in subheading_ids[:10])
        if len(subheading_ids) > 10:
            ids_str += ", ..."
        lines.append(f"**Use with affected_products:** `[{ids_str}]`")
    elif heading_ids:
        ids_str = ", ".join(str(i) for i in heading_ids[:10])
        lines.append(f"**Heading IDs (4-digit):** `[{ids_str}]`")
        lines.append(
            "Note: Use subheading (6-digit) codes with `affected_products` for best precision. "
            "Search again with a heading code to find its subheadings."
        )

    lines.append("")
    lines.append(
        "**Tip:** Use the numeric `id` values (not zero-padded codes) with "
        "`affected_products` in `gta_search_interventions`."
    )

    return "\n".join(lines)


def _matches(
    description: str,
    code: str,
    id_str: str,
    term_lower: str,
    numeric_term: Optional[str],
    is_numeric: bool,
) -> bool:
    """Check if an HS entry matches the search term."""
    if is_numeric and numeric_term:
        # Numeric: match code prefix or ID prefix
        return code.startswith(numeric_term) or id_str.startswith(numeric_term)
    else:
        # Text: match description keywords
        return term_lower in description.lower()
