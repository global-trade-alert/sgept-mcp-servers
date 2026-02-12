"""One-time script to extract HS code and CPC sector reference data from GTA MySQL database.

Connects to the gtaapi MySQL database and pulls complete product (HS) and sector (CPC) tables.
Writes hierarchical JSON files to resources/data/ for use by the MCP server's lookup tools.

Usage:
    cd gta-mcp
    pip install pymysql python-dotenv  # if not already installed
    python qa/extract_reference_data.py
"""

import json
import os
import sys
from pathlib import Path

try:
    import pymysql
except ImportError:
    print("ERROR: pymysql not installed. Run: pip install pymysql")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)


# Load credentials from jf-thought data-queries .env
ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "jf-thought" / "sgept-analytics" / "data-queries" / ".env"

if not ENV_PATH.exists():
    print(f"ERROR: .env file not found at {ENV_PATH}")
    sys.exit(1)

load_dotenv(ENV_PATH)

DB_HOST = os.getenv("GTA_DB_HOST", "gtaapi.cp7esvs8xwum.eu-west-1.rds.amazonaws.com")
DB_PORT = int(os.getenv("GTA_DB_PORT", "3306"))
DB_USER = os.getenv("GTA_DB_USER", "gtaapi_read")
DB_PASSWORD = os.getenv("GTA_DB_PASSWORD", "")
DB_NAME = os.getenv("GTA_DB_NAME", "gtaapi")

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "resources" / "data"


def zero_pad_hs(code_id: int, level: str) -> str:
    """Zero-pad HS code IDs for display.

    The database stores numeric IDs without leading zeros:
    - Chapter: 2-digit (01-97), stored as 1-97
    - Heading: 4-digit (0101-9701), stored as 101-9701
    - Subheading: 6-digit (010100-970100), stored as 10100-970100
    """
    if level == "chapter":
        return str(code_id).zfill(2)
    elif level == "heading":
        return str(code_id).zfill(4)
    elif level == "subheading":
        return str(code_id).zfill(6)
    return str(code_id)


def zero_pad_cpc(code_id: int, level: str) -> str:
    """Zero-pad CPC sector IDs for display.

    CPC divisions are 2-digit, groups are 3-digit.
    """
    if level == "division":
        return str(code_id).zfill(2)
    elif level == "group":
        return str(code_id).zfill(3)
    return str(code_id)


def connect_db():
    """Connect to the GTA MySQL database."""
    print(f"Connecting to {DB_HOST}:{DB_PORT} as {DB_USER}...")
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30,
        read_timeout=60,
    )


def extract_hs_codes(conn) -> dict:
    """Extract complete HS code hierarchy from the database."""
    with conn.cursor() as cursor:
        # Level 2: HS chapters (2-digit)
        cursor.execute("SELECT product_level2_id, product_level2_description FROM api_product_level2_list ORDER BY product_level2_id")
        chapters_raw = cursor.fetchall()
        print(f"  HS chapters (level 2): {len(chapters_raw)} rows")

        # Level 4: HS headings (4-digit)
        cursor.execute("""
            SELECT product_level4_id, product_level4_description, product_level2_id
            FROM api_product_level4_list
            ORDER BY product_level4_id
        """)
        headings_raw = cursor.fetchall()
        print(f"  HS headings (level 4): {len(headings_raw)} rows")

        # Level 6: HS subheadings (6-digit)
        cursor.execute("""
            SELECT product_id, product_description, product_level2_id, product_level4_id
            FROM api_product_list
            ORDER BY product_id
        """)
        subheadings_raw = cursor.fetchall()
        print(f"  HS subheadings (level 6): {len(subheadings_raw)} rows")

    # Build hierarchical structure
    chapters = []
    for ch in chapters_raw:
        chapters.append({
            "id": ch["product_level2_id"],
            "code": zero_pad_hs(ch["product_level2_id"], "chapter"),
            "description": ch["product_level2_description"],
            "level": "chapter",
        })

    headings = []
    for hd in headings_raw:
        headings.append({
            "id": hd["product_level4_id"],
            "code": zero_pad_hs(hd["product_level4_id"], "heading"),
            "description": hd["product_level4_description"],
            "level": "heading",
            "chapter_id": hd["product_level2_id"],
            "chapter_code": zero_pad_hs(hd["product_level2_id"], "chapter"),
        })

    subheadings = []
    for sh in subheadings_raw:
        subheadings.append({
            "id": sh["product_id"],
            "code": zero_pad_hs(sh["product_id"], "subheading"),
            "description": sh["product_description"],
            "level": "subheading",
            "chapter_id": sh["product_level2_id"],
            "chapter_code": zero_pad_hs(sh["product_level2_id"], "chapter"),
            "heading_id": sh["product_level4_id"],
            "heading_code": zero_pad_hs(sh["product_level4_id"], "heading"),
        })

    return {
        "metadata": {
            "source": "gtaapi MySQL database",
            "tables": ["api_product_level2_list", "api_product_level4_list", "api_product_list"],
            "total_entries": len(chapters) + len(headings) + len(subheadings),
            "chapters": len(chapters),
            "headings": len(headings),
            "subheadings": len(subheadings),
        },
        "chapters": chapters,
        "headings": headings,
        "subheadings": subheadings,
    }


def extract_cpc_sectors(conn) -> dict:
    """Extract complete CPC sector hierarchy from the database."""
    with conn.cursor() as cursor:
        # Level 2: CPC divisions (2-digit)
        cursor.execute("SELECT sector_level2_id, sector_level2_name FROM api_sector_level2_list ORDER BY sector_level2_id")
        divisions_raw = cursor.fetchall()
        print(f"  CPC divisions (level 2): {len(divisions_raw)} rows")

        # Full list: CPC groups (3-digit)
        cursor.execute("""
            SELECT sector_id, sector_name, sector_level2_id
            FROM api_sector_list
            ORDER BY sector_id
        """)
        groups_raw = cursor.fetchall()
        print(f"  CPC groups: {len(groups_raw)} rows")

    divisions = []
    for div in divisions_raw:
        divisions.append({
            "id": div["sector_level2_id"],
            "code": str(div["sector_level2_id"]),
            "name": div["sector_level2_name"],
            "level": "division",
        })

    groups = []
    for grp in groups_raw:
        groups.append({
            "id": grp["sector_id"],
            "code": str(grp["sector_id"]),
            "name": grp["sector_name"],
            "level": "group",
            "division_id": grp["sector_level2_id"],
        })

    return {
        "metadata": {
            "source": "gtaapi MySQL database",
            "tables": ["api_sector_level2_list", "api_sector_list"],
            "total_entries": len(divisions) + len(groups),
            "divisions": len(divisions),
            "groups": len(groups),
        },
        "divisions": divisions,
        "groups": groups,
    }


def extract_product_sector_mapping(conn) -> dict:
    """Extract HS product to CPC sector mapping."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT product_id, sector_id FROM api_product_sector ORDER BY product_id, sector_id")
        mappings_raw = cursor.fetchall()
        print(f"  Product-sector mappings: {len(mappings_raw)} rows")

    # Group by product
    by_product = {}
    for m in mappings_raw:
        pid = m["product_id"]
        sid = m["sector_id"]
        if pid not in by_product:
            by_product[pid] = []
        by_product[pid].append(sid)

    return {
        "metadata": {
            "source": "gtaapi MySQL database",
            "table": "api_product_sector",
            "total_mappings": len(mappings_raw),
            "unique_products": len(by_product),
        },
        "product_to_sectors": by_product,
    }


def spot_check(hs_data: dict, cpc_data: dict):
    """Verify known commodities exist in the extracted data."""
    checks = {
        "lithium oxide (282520)": any(s["id"] == 282520 for s in hs_data["subheadings"]),
        "lithium carbonate (283691)": any(s["id"] == 283691 for s in hs_data["subheadings"]),
        "cobalt mattes (810520)": any(s["id"] == 810520 for s in hs_data["subheadings"]),
        "photovoltaic cells (854140)": any(s["id"] == 854140 for s in hs_data["subheadings"]),
        "semiconductor devices (854121)": any(s["id"] == 854121 for s in hs_data["subheadings"]),
        "live animals chapter (01)": any(c["id"] == 1 for c in hs_data["chapters"]),
        "vehicles chapter (87)": any(c["id"] == 87 for c in hs_data["chapters"]),
        "financial services CPC (71)": any(d["id"] == 71 for d in cpc_data["divisions"]),
    }

    print("\nSpot checks:")
    all_pass = True
    for name, found in checks.items():
        status = "PASS" if found else "FAIL"
        if not found:
            all_pass = False
        print(f"  {status}: {name}")

    return all_pass


def main():
    """Extract all reference data and write JSON files."""
    print("=" * 60)
    print("GTA Reference Data Extraction")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = connect_db()
    try:
        print("\nExtracting HS codes...")
        hs_data = extract_hs_codes(conn)

        print("\nExtracting CPC sectors...")
        cpc_data = extract_cpc_sectors(conn)

        print("\nExtracting product-sector mappings...")
        mapping_data = extract_product_sector_mapping(conn)

    finally:
        conn.close()
        print("\nDatabase connection closed.")

    # Spot-check known commodities
    if not spot_check(hs_data, cpc_data):
        print("\nWARNING: Some spot checks failed. Review the data.")

    # Write HS codes
    hs_path = OUTPUT_DIR / "hs_codes.json"
    with open(hs_path, "w", encoding="utf-8") as f:
        json.dump(hs_data, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {hs_path} ({hs_path.stat().st_size / 1024:.1f} KB)")

    # Write CPC sectors
    cpc_path = OUTPUT_DIR / "cpc_sectors.json"
    with open(cpc_path, "w", encoding="utf-8") as f:
        json.dump(cpc_data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {cpc_path} ({cpc_path.stat().st_size / 1024:.1f} KB)")

    # Write product-sector mapping
    mapping_path = OUTPUT_DIR / "product_sector_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping_data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {mapping_path} ({mapping_path.stat().st_size / 1024:.1f} KB)")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"HS codes:  {hs_data['metadata']['total_entries']} entries "
          f"({hs_data['metadata']['chapters']} chapters, "
          f"{hs_data['metadata']['headings']} headings, "
          f"{hs_data['metadata']['subheadings']} subheadings)")
    print(f"CPC sectors: {cpc_data['metadata']['total_entries']} entries "
          f"({cpc_data['metadata']['divisions']} divisions, "
          f"{cpc_data['metadata']['groups']} groups)")
    print(f"Mappings:  {mapping_data['metadata']['total_mappings']} product-sector links")


if __name__ == "__main__":
    main()
