"""CPC sector lookup tool for searching sector codes by keyword or code prefix."""

import json
from pathlib import Path
from typing import Optional

# Lazy-loaded data cache
_CPC_DATA: Optional[dict] = None


def _get_data_dir() -> Path:
    """Get the path to the data directory."""
    current_file = Path(__file__)
    # Installed: src/gta_mcp/sector_lookup.py → gta_mcp/resources/data/
    installed_path = current_file.parent / "resources" / "data"
    if installed_path.is_dir():
        return installed_path
    # Development: src/gta_mcp/sector_lookup.py → ../../resources/data/
    dev_path = current_file.parent.parent.parent / "resources" / "data"
    if dev_path.is_dir():
        return dev_path
    return dev_path


def _load_cpc_data() -> dict:
    """Load CPC sector data from JSON file (lazy, cached)."""
    global _CPC_DATA
    if _CPC_DATA is None:
        data_path = _get_data_dir() / "cpc_sectors.json"
        if not data_path.exists():
            raise FileNotFoundError(
                f"CPC sectors data file not found at {data_path}. "
                "Run qa/extract_reference_data.py to generate it."
            )
        with open(data_path, "r", encoding="utf-8") as f:
            _CPC_DATA = json.load(f)
    return _CPC_DATA


def search_sectors(search_term: str, max_results: int = 50) -> str:
    """Search CPC sectors by keyword, division number, or code prefix.

    Args:
        search_term: Keyword (e.g., 'financial'), division number (e.g., '71'),
                     or code prefix (e.g., '711')
        max_results: Maximum results to return (default 50)

    Returns:
        Markdown-formatted table of matching CPC sectors with usage guidance.
    """
    data = _load_cpc_data()
    term_lower = search_term.strip().lower()

    is_numeric = term_lower.replace(" ", "").isdigit()
    numeric_term = term_lower.replace(" ", "") if is_numeric else None

    matches = []

    # Search divisions
    for div in data["divisions"]:
        if _matches(div["name"], div["code"], str(div["id"]), term_lower, numeric_term, is_numeric):
            matches.append({
                "code": div["code"],
                "id": div["id"],
                "name": div["name"],
                "level": "Division",
                "division": div["code"],
                "category": "Services" if div["id"] >= 500 else "Goods",
            })

    # Search groups
    for grp in data["groups"]:
        if _matches(grp["name"], grp["code"], str(grp["id"]), term_lower, numeric_term, is_numeric):
            # Find parent division name
            division_name = ""
            for div in data["divisions"]:
                if div["id"] == grp["division_id"]:
                    division_name = div["name"]
                    break
            matches.append({
                "code": grp["code"],
                "id": grp["id"],
                "name": grp["name"],
                "level": "Group",
                "division": str(grp["division_id"]),
                "category": "Services" if grp["id"] >= 500 else "Goods",
            })

    if not matches:
        return (
            f"No CPC sectors found matching '{search_term}'.\n\n"
            "Tips:\n"
            "- Try broader terms (e.g., 'financial' instead of 'banking services')\n"
            "- Try the division number (e.g., '71' for financial services)\n"
            "- Remember: ID >= 500 = services, ID < 500 = goods\n"
        )

    # Sort: divisions first, then groups
    level_order = {"Division": 0, "Group": 1}
    matches.sort(key=lambda m: (level_order[m["level"]], m["id"]))

    total = len(matches)
    matches = matches[:max_results]

    # Format as markdown table
    lines = [f"Found {total} CPC sectors matching \"{search_term}\""]
    if total > max_results:
        lines.append(f"(showing first {max_results})")
    lines.append("")
    lines.append("| Code | Name | Level | Division | Category |")
    lines.append("|------|------|-------|----------|----------|")
    for m in matches:
        name = m["name"][:70] + "..." if len(m["name"]) > 70 else m["name"]
        lines.append(f"| {m['code']} | {name} | {m['level']} | {m['division']} | {m['category']} |")

    # Add usage guidance
    group_ids = [m["id"] for m in matches if m["level"] == "Group"]
    division_ids = [m["id"] for m in matches if m["level"] == "Division"]

    lines.append("")
    if group_ids:
        ids_str = ", ".join(str(i) for i in group_ids[:15])
        if len(group_ids) > 15:
            ids_str += ", ..."
        lines.append(f"**Use with affected_sectors:** `[{ids_str}]`")
    elif division_ids:
        ids_str = ", ".join(str(i) for i in division_ids[:10])
        lines.append(f"**Division IDs:** `[{ids_str}]`")
        lines.append(
            "Note: Search again with a division code to find its groups for more "
            "specific filtering."
        )

    lines.append("")
    lines.append(
        "**Tip:** Use the numeric `id` values with `affected_sectors` in "
        "`gta_search_interventions`. Sector names with fuzzy matching also work."
    )

    return "\n".join(lines)


def _matches(
    name: str,
    code: str,
    id_str: str,
    term_lower: str,
    numeric_term: Optional[str],
    is_numeric: bool,
) -> bool:
    """Check if a CPC entry matches the search term."""
    if is_numeric and numeric_term:
        return code.startswith(numeric_term) or id_str.startswith(numeric_term)
    else:
        return term_lower in name.lower()
