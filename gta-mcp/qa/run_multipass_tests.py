"""Multi-pass workflow evaluation for the GTA MCP server's 20 sample prompts.

Tests the automatic detection logic:
- Broad search (no intervention_id) -> overview keys + limit=500
- Specific ID lookup (intervention_id) -> standard keys

For each prompt, runs:
  Pass 1: Overview (broad search with overview keys, limit=500)
  Pass 2: Detail (pick 5 IDs from Pass 1, fetch with standard keys)
  Count queries: Direct count calls (no multi-pass needed)

Outputs:
  qa/multipass-test-results.json   - Raw data
  qa/multipass-evaluation-report.md - Markdown report
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import date, datetime

import httpx

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

API_KEY = os.environ["GTA_API_KEY"]
HEADERS = {"Authorization": f"APIKey {API_KEY}", "Content-Type": "application/json"}
BASE_URL = "https://api.globaltradealert.org"
DATA_ENDPOINT = f"{BASE_URL}/api/v2/gta/data/"
COUNT_ENDPOINT = f"{BASE_URL}/api/v1/gta/data-counts/"

OVERVIEW_KEYS = [
    "intervention_id", "state_act_title", "intervention_type",
    "gta_evaluation", "date_announced", "is_in_force",
    "implementing_jurisdictions", "intervention_url"
]

STANDARD_KEYS = [
    "intervention_id", "state_act_id", "state_act_title",
    "intervention_type", "mast_chapter", "gta_evaluation",
    "implementation_level", "eligible_firm",
    "date_announced", "date_implemented", "date_removed",
    "is_in_force",
    "implementing_jurisdictions", "affected_jurisdictions",
    "affected_sectors",
    "intervention_url", "state_act_url", "is_official_source"
]

TODAY = date.today().isoformat()  # 2026-02-12

# --------------------------------------------------------------------------- #
# Prompt definitions (20 prompts from the evaluation spec)
# --------------------------------------------------------------------------- #

PROMPTS = [
    # 1
    {
        "id": 1,
        "prompt": "What tariffs has the US imposed on China since Jan 2025?",
        "type": "search",
        "request_data": {
            "implementer": [840], "affected": [156],
            "intervention_types": [47],
            "announcement_period": ["2025-01-01", "2099-12-31"]
        }
    },
    # 2
    {
        "id": 2,
        "prompt": "Which countries have imposed tariffs affecting US exports in 2025?",
        "type": "search",
        "request_data": {
            "affected": [840], "intervention_types": [47],
            "announcement_period": ["2025-01-01", "2025-12-31"]
        }
    },
    # 3
    {
        "id": 3,
        "prompt": "What export controls has China imposed on rare earth elements?",
        "type": "search",
        "request_data": {
            "implementer": [156], "mast_chapters": [14],
            "query": "rare earth",
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 4
    {
        "id": 4,
        "prompt": "Which countries have restricted exports of lithium or cobalt since 2022?",
        "type": "search",
        "request_data": {
            "mast_chapters": [14], "query": "lithium cobalt",
            "announcement_period": ["2022-01-01", "2099-12-31"]
        }
    },
    # 5
    {
        "id": 5,
        "prompt": "What measures currently affect semiconductor manufacturing equipment trade?",
        "type": "search",
        "request_data": {
            "query": "semiconductor",
            "in_force_on_date": TODAY, "keep_in_force_on_date": True,
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 6
    {
        "id": 6,
        "prompt": "What subsidies are governments providing for critical mineral processing?",
        "type": "search",
        "request_data": {
            "mast_chapters": [10], "query": "critical mineral",
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 7
    {
        "id": 7,
        "prompt": "Which countries subsidise their domestic semiconductor industry?",
        "type": "search",
        "request_data": {
            "query": "semiconductor",
            "in_force_on_date": TODAY, "keep_in_force_on_date": True,
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 8
    {
        "id": 8,
        "prompt": "Which G20 countries have increased state aid to EV manufacturers since 2022?",
        "type": "search",
        "request_data": {
            "mast_chapters": [10], "query": "electric vehicle",
            "announcement_period": ["2022-01-01", "2099-12-31"]
        }
    },
    # 9
    {
        "id": 9,
        "prompt": "What harmful measures has the EU imposed on US exports since 2024?",
        "type": "search",
        "request_data": {
            "implementer": [1049], "affected": [840],
            "gta_evaluation": [4],
            "announcement_period": ["2024-01-01", "2099-12-31"]
        }
    },
    # 10
    {
        "id": 10,
        "prompt": "What measures has Brazil implemented affecting US agricultural exports?",
        "type": "search",
        "request_data": {
            "implementer": [76], "affected": [840],
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 11
    {
        "id": 11,
        "prompt": "Find all anti-dumping investigations targeting Chinese steel since 2020",
        "type": "search",
        "request_data": {
            "affected": [156], "intervention_types": [51],
            "query": "steel",
            "announcement_period": ["2020-01-01", "2099-12-31"]
        }
    },
    # 12
    {
        "id": 12,
        "prompt": "What safeguard measures are currently in force on solar panels?",
        "type": "search",
        "request_data": {
            "intervention_types": [52], "query": "solar",
            "in_force_on_date": TODAY, "keep_in_force_on_date": True,
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 13
    {
        "id": 13,
        "prompt": "What local content requirements affect automotive production in Southeast Asia?",
        "type": "search",
        "request_data": {
            "implementer": [360, 764, 704, 458, 608],
            "intervention_types": [28],
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 14
    {
        "id": 14,
        "prompt": "What import licensing requirements affect pharmaceutical products in India?",
        "type": "search",
        "request_data": {
            "implementer": [699], "intervention_types": [36],
            "query": "pharmaceutical",
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 15 — COUNT
    {
        "id": 15,
        "prompt": "Has the use of export restrictions increased since 2020?",
        "type": "count",
        "request_data": {"mast_chapters": [14]},
        "count_by": "date_announced_year",
        "count_variable": "intervention_id"
    },
    # 16 — COUNT (two calls)
    {
        "id": 16,
        "prompt": "How many harmful interventions were implemented globally in 2025 versus 2024?",
        "type": "count_pair",
        "calls": [
            {
                "label": "2025",
                "request_data": {
                    "gta_evaluation": [4],
                    "implementation_period": ["2025-01-01", "2025-12-31"]
                },
                "count_by": "date_implemented_year",
                "count_variable": "intervention_id"
            },
            {
                "label": "2024",
                "request_data": {
                    "gta_evaluation": [4],
                    "implementation_period": ["2024-01-01", "2024-12-31"]
                },
                "count_by": "date_implemented_year",
                "count_variable": "intervention_id"
            }
        ]
    },
    # 17
    {
        "id": 17,
        "prompt": "Which interventions target state-owned enterprises specifically?",
        "type": "search",
        "request_data": {
            "eligible_firms": [4],
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 18
    {
        "id": 18,
        "prompt": "What subnational measures has the US implemented since 2023?",
        "type": "search",
        "request_data": {
            "implementer": [840], "implementation_level": [3],
            "announcement_period": ["2023-01-01", "2099-12-31"]
        }
    },
    # 19
    {
        "id": 19,
        "prompt": "What FDI screening measures target Chinese investments in European technology sectors?",
        "type": "search",
        "request_data": {
            "affected": [156], "intervention_types": [25],
            "query": "technology",
            "announcement_period": ["1900-01-01", "2099-12-31"]
        }
    },
    # 20
    {
        "id": 20,
        "prompt": "What measures have G7 countries coordinated against Russia since February 2022?",
        "type": "search",
        "request_data": {
            "implementer": [840, 826, 251, 276, 381, 392, 124],
            "affected": [643],
            "announcement_period": ["2022-02-01", "2099-12-31"]
        }
    },
]


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #

async def api_post(client: httpx.AsyncClient, url: str, body: dict) -> tuple:
    """POST to API, return (status_code, parsed_json_or_text, elapsed_ms)."""
    t0 = time.monotonic()
    resp = await client.post(url, json=body, headers=HEADERS)
    elapsed = round((time.monotonic() - t0) * 1000)
    if resp.status_code == 200:
        return resp.status_code, resp.json(), elapsed
    else:
        return resp.status_code, resp.text, elapsed


# --------------------------------------------------------------------------- #
# Pass 1: Overview query
# --------------------------------------------------------------------------- #

async def run_overview_pass(client: httpx.AsyncClient, request_data: dict) -> dict:
    """Run a broad search with overview keys and limit=500."""
    body = {
        "limit": 500,
        "offset": 0,
        "sorting": "-date_announced",
        "request_data": request_data,
        "show_keys": OVERVIEW_KEYS
    }
    status, data, elapsed_ms = await api_post(client, DATA_ENDPOINT, body)

    result = {
        "status": status,
        "elapsed_ms": elapsed_ms,
        "body_sent": body,
    }

    if status == 200 and isinstance(data, list):
        result["total_results"] = len(data)
        result["response_size_bytes"] = len(json.dumps(data))
        result["response_size_kb"] = round(result["response_size_bytes"] / 1024, 1)
        # Extract sample titles
        result["sample_titles"] = [
            item.get("state_act_title", "No title") for item in data[:5]
        ]
        # Extract all intervention_ids for pass 2
        result["all_ids"] = [
            item.get("intervention_id") for item in data if item.get("intervention_id")
        ]
        # Keys actually returned
        if data:
            result["keys_returned"] = sorted(data[0].keys())
        else:
            result["keys_returned"] = []
        result["error"] = None
    else:
        result["total_results"] = 0
        result["response_size_bytes"] = 0
        result["response_size_kb"] = 0
        result["sample_titles"] = []
        result["all_ids"] = []
        result["keys_returned"] = []
        result["error"] = str(data)[:500] if status != 200 else None

    return result


# --------------------------------------------------------------------------- #
# Pass 2: Detail query (specific IDs)
# --------------------------------------------------------------------------- #

async def run_detail_pass(client: httpx.AsyncClient, intervention_ids: list) -> dict:
    """Fetch up to 5 specific interventions with standard keys."""
    ids_to_fetch = intervention_ids[:5]
    body = {
        "limit": 10,
        "offset": 0,
        "request_data": {
            "intervention_id": ids_to_fetch,
            "announcement_period": ["1900-01-01", "2099-12-31"]
        },
        "show_keys": STANDARD_KEYS
    }
    status, data, elapsed_ms = await api_post(client, DATA_ENDPOINT, body)

    result = {
        "status": status,
        "elapsed_ms": elapsed_ms,
        "ids_requested": ids_to_fetch,
        "body_sent": body,
    }

    if status == 200 and isinstance(data, list):
        returned_ids = [item.get("intervention_id") for item in data]
        result["ids_returned"] = returned_ids
        result["all_ids_present"] = all(rid in returned_ids for rid in ids_to_fetch)
        result["num_returned"] = len(data)
        result["response_size_bytes"] = len(json.dumps(data))
        result["response_size_kb"] = round(result["response_size_bytes"] / 1024, 1)
        if data:
            result["keys_returned"] = sorted(data[0].keys())
            # Include one sample record (first)
            result["sample_record"] = data[0]
        else:
            result["keys_returned"] = []
            result["sample_record"] = None
        result["error"] = None
    else:
        result["ids_returned"] = []
        result["all_ids_present"] = False
        result["num_returned"] = 0
        result["response_size_bytes"] = 0
        result["response_size_kb"] = 0
        result["keys_returned"] = []
        result["sample_record"] = None
        result["error"] = str(data)[:500] if status != 200 else None

    return result


# --------------------------------------------------------------------------- #
# Count queries
# --------------------------------------------------------------------------- #

async def run_count_query(client: httpx.AsyncClient, request_data: dict,
                          count_by: str, count_variable: str) -> dict:
    """Run a count query."""
    payload_request_data = dict(request_data)
    payload_request_data["count_by"] = [count_by]
    payload_request_data["count_variable"] = count_variable

    body = {"request_data": payload_request_data}
    status, data, elapsed_ms = await api_post(client, COUNT_ENDPOINT, body)

    result = {
        "status": status,
        "elapsed_ms": elapsed_ms,
        "body_sent": body,
    }

    if status == 200:
        if isinstance(data, dict):
            results_list = data.get("results", [])
            result["count_data"] = results_list
            result["total_count"] = data.get("count", sum(
                r.get("count", 0) for r in results_list
            ))
        elif isinstance(data, list):
            result["count_data"] = data
            result["total_count"] = sum(r.get("count", 0) for r in data)
        else:
            result["count_data"] = []
            result["total_count"] = 0
        result["error"] = None
    else:
        result["count_data"] = []
        result["total_count"] = 0
        result["error"] = str(data)[:500]

    return result


# --------------------------------------------------------------------------- #
# Main runner
# --------------------------------------------------------------------------- #

async def run_all():
    all_results = []

    async with httpx.AsyncClient(timeout=90.0) as client:
        for p in PROMPTS:
            pid = p["id"]
            prompt_text = p["prompt"]
            query_type = p["type"]

            print(f"\n{'='*70}")
            print(f"Prompt {pid}: {prompt_text}")
            print(f"{'='*70}")

            entry = {
                "id": pid,
                "prompt": prompt_text,
                "type": query_type,
            }

            try:
                # ----------------------------------------------------------
                # SEARCH prompts: Pass 1 (overview) + Pass 2 (detail)
                # ----------------------------------------------------------
                if query_type == "search":
                    # Pass 1: Overview
                    print(f"  Pass 1 (Overview, limit=500)...")
                    pass1 = await run_overview_pass(client, p["request_data"])
                    entry["pass1_overview"] = pass1
                    print(f"    -> {pass1['total_results']} results, "
                          f"{pass1['response_size_kb']} KB, "
                          f"{pass1['elapsed_ms']}ms")
                    if pass1["sample_titles"]:
                        for t in pass1["sample_titles"][:3]:
                            print(f"       - {t[:80]}")

                    # Pass 2: Detail (only if >0 results)
                    if pass1["total_results"] > 0 and pass1["all_ids"]:
                        # Pick up to 5 IDs spread across the result set
                        all_ids = pass1["all_ids"]
                        n = len(all_ids)
                        if n <= 5:
                            selected_ids = all_ids
                        else:
                            # Pick evenly spaced: first, 25%, 50%, 75%, last
                            indices = [0, n // 4, n // 2, 3 * n // 4, n - 1]
                            selected_ids = [all_ids[i] for i in indices]

                        print(f"  Pass 2 (Detail, {len(selected_ids)} IDs)...")
                        pass2 = await run_detail_pass(client, selected_ids)
                        entry["pass2_detail"] = pass2
                        print(f"    -> {pass2['num_returned']} returned, "
                              f"all present: {pass2['all_ids_present']}, "
                              f"{pass2['response_size_kb']} KB, "
                              f"{pass2['elapsed_ms']}ms")
                    else:
                        entry["pass2_detail"] = None
                        print("  Pass 2: Skipped (no results from Pass 1)")

                # ----------------------------------------------------------
                # SINGLE COUNT prompt
                # ----------------------------------------------------------
                elif query_type == "count":
                    print(f"  Count query...")
                    count_result = await run_count_query(
                        client, p["request_data"],
                        p["count_by"], p["count_variable"]
                    )
                    entry["count_result"] = count_result
                    print(f"    -> {len(count_result['count_data'])} groups, "
                          f"total: {count_result['total_count']}, "
                          f"{count_result['elapsed_ms']}ms")
                    if count_result["count_data"]:
                        for row in count_result["count_data"][:5]:
                            print(f"       {row}")

                # ----------------------------------------------------------
                # PAIRED COUNT (prompt 16)
                # ----------------------------------------------------------
                elif query_type == "count_pair":
                    entry["count_results"] = []
                    for call in p["calls"]:
                        print(f"  Count query ({call['label']})...")
                        count_result = await run_count_query(
                            client, call["request_data"],
                            call["count_by"], call["count_variable"]
                        )
                        count_result["label"] = call["label"]
                        entry["count_results"].append(count_result)
                        print(f"    -> {len(count_result['count_data'])} groups, "
                              f"total: {count_result['total_count']}, "
                              f"{count_result['elapsed_ms']}ms")
                        if count_result["count_data"]:
                            for row in count_result["count_data"][:3]:
                                print(f"       {row}")

            except Exception as e:
                traceback.print_exc()
                entry["error"] = str(e)
                print(f"  ERROR: {e}")

            all_results.append(entry)
            # Throttle to avoid rate limits
            await asyncio.sleep(0.5)

    return all_results


# --------------------------------------------------------------------------- #
# Report generation
# --------------------------------------------------------------------------- #

def generate_report(results: list) -> str:
    """Generate the Markdown evaluation report."""
    lines = []
    lines.append("# Multi-Pass Workflow Evaluation Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**API endpoint:** `{DATA_ENDPOINT}`")
    lines.append(f"**Overview keys:** {len(OVERVIEW_KEYS)} fields")
    lines.append(f"**Standard keys:** {len(STANDARD_KEYS)} fields")
    lines.append("")

    # ---------------------------------------------------------------------- #
    # Summary table
    # ---------------------------------------------------------------------- #
    lines.append("## Summary")
    lines.append("")
    lines.append("| # | Prompt | Type | Pass 1 Results | Pass 1 Size | Pass 2 OK | Verdict |")
    lines.append("|---|--------|------|----------------|-------------|-----------|---------|")

    exceeded_50 = 0
    under_50 = 0
    overview_sizes = []
    search_results = []

    for r in results:
        pid = r["id"]
        prompt_short = r["prompt"][:55] + ("..." if len(r["prompt"]) > 55 else "")
        qtype = r["type"]

        if qtype == "search":
            p1 = r.get("pass1_overview", {})
            p2 = r.get("pass2_detail")
            total = p1.get("total_results", 0)
            size_kb = p1.get("response_size_kb", 0)
            overview_sizes.append(size_kb)
            search_results.append(total)

            if total > 50:
                exceeded_50 += 1
            else:
                under_50 += 1

            if p2:
                p2_ok = "Yes" if p2.get("all_ids_present") else "FAIL"
            elif total == 0:
                p2_ok = "N/A (0 results)"
            else:
                p2_ok = "Skipped"

            if total == 0:
                verdict = "No results"
            elif p1.get("error"):
                verdict = "API error"
            elif p2 and not p2.get("all_ids_present"):
                verdict = "Pass 2 missing IDs"
            else:
                verdict = "OK"

            lines.append(
                f"| {pid} | {prompt_short} | search | {total} | {size_kb} KB | {p2_ok} | {verdict} |"
            )
        elif qtype == "count":
            cr = r.get("count_result", {})
            groups = len(cr.get("count_data", []))
            total_count = cr.get("total_count", 0)
            verdict = "OK" if cr.get("status") == 200 and not cr.get("error") else "FAIL"
            lines.append(
                f"| {pid} | {prompt_short} | count | {groups} groups | - | - | {verdict} |"
            )
        elif qtype == "count_pair":
            crs = r.get("count_results", [])
            labels = [f"{c.get('label', '?')}: {c.get('total_count', 0)}" for c in crs]
            summary = "; ".join(labels)
            any_error = any(c.get("error") for c in crs)
            verdict = "OK" if not any_error else "FAIL"
            lines.append(
                f"| {pid} | {prompt_short} | count_pair | {summary} | - | - | {verdict} |"
            )

    lines.append("")

    # ---------------------------------------------------------------------- #
    # Per-prompt details
    # ---------------------------------------------------------------------- #
    lines.append("## Per-Prompt Details")
    lines.append("")

    for r in results:
        pid = r["id"]
        lines.append(f"### Prompt {pid}: {r['prompt']}")
        lines.append("")

        if r["type"] == "search":
            p1 = r.get("pass1_overview", {})
            p2 = r.get("pass2_detail")

            lines.append("**Pass 1 -- Overview (auto-detected for broad search)**")
            lines.append(f"- Results: {p1.get('total_results', 0)} interventions")
            lines.append(f"- Response size: {p1.get('response_size_kb', 0)} KB ({p1.get('response_size_bytes', 0):,} bytes)")
            lines.append(f"- Elapsed: {p1.get('elapsed_ms', 0)} ms")
            lines.append(f"- Keys returned: {p1.get('keys_returned', [])}")
            if p1.get("sample_titles"):
                lines.append("- Sample titles:")
                for t in p1["sample_titles"][:5]:
                    lines.append(f"  - {t}")
            if p1.get("error"):
                lines.append(f"- ERROR: {p1['error']}")
            lines.append("")

            if p2:
                lines.append("**Pass 2 -- Standard Detail (auto-detected for specific IDs)**")
                lines.append(f"- IDs requested: {p2.get('ids_requested', [])}")
                lines.append(f"- IDs returned: {p2.get('ids_returned', [])}")
                lines.append(f"- All IDs present: {'Yes' if p2.get('all_ids_present') else 'No'}")
                lines.append(f"- Num returned: {p2.get('num_returned', 0)}")
                lines.append(f"- Response size: {p2.get('response_size_kb', 0)} KB")
                lines.append(f"- Elapsed: {p2.get('elapsed_ms', 0)} ms")
                lines.append(f"- Keys returned: {p2.get('keys_returned', [])}")
                if p2.get("sample_record"):
                    sr = p2["sample_record"]
                    lines.append(f"- Sample record (ID {sr.get('intervention_id', '?')}):")
                    lines.append(f"  - Title: {sr.get('state_act_title', 'N/A')}")
                    lines.append(f"  - Type: {sr.get('intervention_type', 'N/A')}")
                    lines.append(f"  - Evaluation: {sr.get('gta_evaluation', 'N/A')}")
                    lines.append(f"  - Date announced: {sr.get('date_announced', 'N/A')}")
                    lines.append(f"  - In force: {sr.get('is_in_force', 'N/A')}")
                if p2.get("error"):
                    lines.append(f"- ERROR: {p2['error']}")
            elif p1.get("total_results", 0) == 0:
                lines.append("**Pass 2:** Skipped (no results from Pass 1)")
            lines.append("")

            # Multi-pass value
            total = p1.get("total_results", 0)
            if total > 50:
                lines.append(
                    f"**Multi-pass value:** Prompt returned {total} results vs old ceiling of 50. "
                    f"Overview pass reveals {round((total - 50) / 50 * 100)}% more data."
                )
            elif total > 0:
                lines.append(
                    f"**Multi-pass value:** Only {total} results (within old 50-result ceiling). "
                    f"Overview mode still useful for compact triage at {p1.get('response_size_kb', 0)} KB."
                )
            else:
                lines.append("**Multi-pass value:** No results returned -- query may be too narrow.")
            lines.append("")

        elif r["type"] == "count":
            cr = r.get("count_result", {})
            lines.append("**Count query (no multi-pass needed)**")
            lines.append(f"- Status: {cr.get('status', 'N/A')}")
            lines.append(f"- Groups: {len(cr.get('count_data', []))}")
            lines.append(f"- Total count: {cr.get('total_count', 0)}")
            lines.append(f"- Elapsed: {cr.get('elapsed_ms', 0)} ms")
            if cr.get("count_data"):
                lines.append("- Data (first 10 rows):")
                for row in cr["count_data"][:10]:
                    lines.append(f"  - {row}")
            if cr.get("error"):
                lines.append(f"- ERROR: {cr['error']}")
            lines.append("")

        elif r["type"] == "count_pair":
            lines.append("**Count pair (no multi-pass needed)**")
            for cr in r.get("count_results", []):
                label = cr.get("label", "?")
                lines.append(f"- **{label}:**")
                lines.append(f"  - Status: {cr.get('status', 'N/A')}")
                lines.append(f"  - Total count: {cr.get('total_count', 0)}")
                lines.append(f"  - Elapsed: {cr.get('elapsed_ms', 0)} ms")
                if cr.get("count_data"):
                    for row in cr["count_data"][:5]:
                        lines.append(f"    - {row}")
                if cr.get("error"):
                    lines.append(f"  - ERROR: {cr['error']}")
            lines.append("")

        if r.get("error"):
            lines.append(f"**TOP-LEVEL ERROR:** {r['error']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # ---------------------------------------------------------------------- #
    # Key Findings
    # ---------------------------------------------------------------------- #
    lines.append("## Key Findings")
    lines.append("")

    # How many exceeded 50
    lines.append(f"### Result Volume")
    lines.append(f"- **{exceeded_50}** of {exceeded_50 + under_50} search prompts exceeded the old 50-result ceiling")
    lines.append(f"- **{under_50}** search prompts returned 50 or fewer results")
    if search_results:
        lines.append(f"- **Max results:** {max(search_results)} (from a single overview query)")
        lines.append(f"- **Min results (non-zero):** {min(r for r in search_results if r > 0) if any(r > 0 for r in search_results) else 'N/A'}")
        lines.append(f"- **Average results:** {round(sum(search_results) / len(search_results))}")
    lines.append("")

    # Overview response sizes
    lines.append(f"### Response Sizes (Overview Pass)")
    if overview_sizes:
        lines.append(f"- **Average:** {round(sum(overview_sizes) / len(overview_sizes), 1)} KB")
        lines.append(f"- **Max:** {max(overview_sizes)} KB")
        lines.append(f"- **Min:** {min(overview_sizes)} KB")
        fits_context = sum(1 for s in overview_sizes if s < 100)
        lines.append(f"- **Fits in LLM context (<100KB):** {fits_context} of {len(overview_sizes)}")
    lines.append("")

    # Pass 2 success
    pass2_total = 0
    pass2_success = 0
    for r in results:
        if r["type"] == "search" and r.get("pass2_detail"):
            pass2_total += 1
            if r["pass2_detail"].get("all_ids_present"):
                pass2_success += 1

    lines.append(f"### Pass 2 (Detail) Success Rate")
    lines.append(f"- **{pass2_success}** of {pass2_total} detail passes returned all requested IDs")
    if pass2_total > 0 and pass2_success < pass2_total:
        lines.append(f"- **{pass2_total - pass2_success}** detail passes had missing IDs")
    lines.append("")

    # Count queries
    count_prompts = [r for r in results if r["type"] in ("count", "count_pair")]
    lines.append(f"### Count Queries")
    lines.append(f"- **{len(count_prompts)}** count prompts tested")
    for r in count_prompts:
        if r["type"] == "count":
            cr = r.get("count_result", {})
            status_str = "OK" if not cr.get("error") else f"FAIL: {cr['error'][:80]}"
            lines.append(f"  - Prompt {r['id']}: {status_str}")
        elif r["type"] == "count_pair":
            for cr in r.get("count_results", []):
                status_str = "OK" if not cr.get("error") else f"FAIL: {cr['error'][:80]}"
                lines.append(f"  - Prompt {r['id']} ({cr.get('label', '?')}): {status_str}")
    lines.append("")

    # Prompts with no benefit from overview
    lines.append("### Prompts Where Overview Provides Limited Benefit (<= 50 results)")
    for r in results:
        if r["type"] == "search":
            total = r.get("pass1_overview", {}).get("total_results", 0)
            if 0 < total <= 50:
                lines.append(f"- Prompt {r['id']}: {total} results -- {r['prompt'][:60]}")
    no_results = [r for r in results if r["type"] == "search" and r.get("pass1_overview", {}).get("total_results", 0) == 0]
    if no_results:
        lines.append("")
        lines.append("### Prompts With Zero Results")
        for r in no_results:
            lines.append(f"- Prompt {r['id']}: {r['prompt'][:60]}")
    lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #

async def main():
    print("=" * 70)
    print("GTA MCP Multi-Pass Workflow Evaluation")
    print(f"Running {len(PROMPTS)} prompts against live API")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = await run_all()

    # Save raw results
    qa_dir = os.path.dirname(__file__)

    def default_serializer(obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    results_path = os.path.join(qa_dir, "multipass-test-results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=default_serializer)
    print(f"\nRaw results saved to {results_path}")

    # Generate and save report
    report = generate_report(results)
    report_path = os.path.join(qa_dir, "multipass-evaluation-report.md")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report saved to {report_path}")

    # Quick summary
    print("\n" + "=" * 70)
    print("QUICK SUMMARY")
    print("=" * 70)
    for r in results:
        if r["type"] == "search":
            p1 = r.get("pass1_overview", {})
            p2 = r.get("pass2_detail")
            p2_str = (
                f"Pass2={'OK' if p2 and p2.get('all_ids_present') else 'FAIL/Skip'}"
                if p2 else "Pass2=N/A"
            )
            print(f"  [{r['id']:2d}] {p1.get('total_results', 0):4d} results, "
                  f"{p1.get('response_size_kb', 0):6.1f} KB, {p2_str}  "
                  f"| {r['prompt'][:50]}")
        elif r["type"] == "count":
            cr = r.get("count_result", {})
            print(f"  [{r['id']:2d}] COUNT: {cr.get('total_count', 0):6d} total, "
                  f"{len(cr.get('count_data', []))} groups  "
                  f"| {r['prompt'][:50]}")
        elif r["type"] == "count_pair":
            counts = [f"{c.get('label', '?')}={c.get('total_count', 0)}" for c in r.get("count_results", [])]
            print(f"  [{r['id']:2d}] COUNT_PAIR: {', '.join(counts)}  "
                  f"| {r['prompt'][:50]}")


if __name__ == "__main__":
    asyncio.run(main())
