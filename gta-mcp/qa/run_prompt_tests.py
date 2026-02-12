#!/usr/bin/env python3
"""
GTA MCP Server — End-to-End Prompt Evaluation (v2)

Tests all 20 USE_CASES.md prompts plus 3 new-feature prompts (21-23)
against the live GTA API. Records results and generates an evaluation report.

Usage:
    python qa/run_prompt_tests.py
"""

import json
import os
import sys
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("GTA_API_KEY") or os.environ.get("SGEPT_GTA_API_KEY")
if not API_KEY:
    print("ERROR: Set GTA_API_KEY or SGEPT_GTA_API_KEY environment variable")
    sys.exit(1)

BASE_URL = "https://api.globaltradealert.org"
DATA_ENDPOINT = f"{BASE_URL}/api/v2/gta/data/"
COUNT_ENDPOINT = f"{BASE_URL}/api/v1/gta/data-counts/"
HEADERS = {
    "Authorization": f"APIKey {API_KEY}",
    "Content-Type": "application/json",
}

TODAY = date.today().isoformat()

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(OUTPUT_DIR, "prompt-test-results-v2.json")
REPORT_FILE = os.path.join(OUTPUT_DIR, "prompt-evaluation-report-v2.md")

# ---------------------------------------------------------------------------
# Prompt definitions
# ---------------------------------------------------------------------------

PROMPTS: List[Dict[str, Any]] = [
    # --- 1-14: Search prompts ---
    {
        "id": 1,
        "prompt": "What tariffs has the US imposed on China since Jan 2025?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [840],
                "affected": [156],
                "intervention_types": [47],
                "announcement_period": ["2025-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 2,
        "prompt": "Which countries have imposed tariffs affecting US exports in 2025?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "affected": [840],
                "intervention_types": [47],
                "announcement_period": ["2025-01-01", "2025-12-31"],
            },
        },
    },
    {
        "id": 3,
        "prompt": "What export controls has China imposed on rare earth elements?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [156],
                "mast_chapters": [14],
                "query": "rare earth",
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 4,
        "prompt": "Which countries have restricted exports of lithium or cobalt since 2022?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "mast_chapters": [14],
                "query": "lithium | cobalt",
                "announcement_period": ["2022-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 5,
        "prompt": "What measures currently affect semiconductor manufacturing equipment trade?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "query": "semiconductor",
                "in_force_on_date": TODAY,
                "keep_in_force_on_date": True,
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 6,
        "prompt": "What subsidies are governments providing for critical mineral processing?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "mast_chapters": [10],
                "query": "critical mineral",
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 7,
        "prompt": "Which countries subsidise their domestic semiconductor industry?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "query": "semiconductor",
                "in_force_on_date": TODAY,
                "keep_in_force_on_date": True,
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 8,
        "prompt": "Which G20 countries have increased state aid to EV manufacturers since 2022?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "mast_chapters": [10],
                "query": "electric vehicle",
                "announcement_period": ["2022-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 9,
        "prompt": "What harmful measures has the EU imposed on US exports since 2024?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [1049],
                "affected": [840],
                "gta_evaluation": [1, 2],
                "announcement_period": ["2024-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 10,
        "prompt": "What measures has Brazil implemented affecting US agricultural exports?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [76],
                "affected": [840],
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 11,
        "prompt": "Find all anti-dumping investigations targeting Chinese steel since 2020",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "affected": [156],
                "intervention_types": [51],
                "query": "steel",
                "announcement_period": ["2020-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 12,
        "prompt": "What safeguard measures are currently in force on solar panels?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "intervention_types": [52],
                "query": "solar",
                "in_force_on_date": TODAY,
                "keep_in_force_on_date": True,
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 13,
        "prompt": "What local content requirements affect automotive production in Southeast Asia?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [360, 764, 704, 458, 608],
                "intervention_types": [28],
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 14,
        "prompt": "What import licensing requirements affect pharmaceutical products in India?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [699],
                "intervention_types": [36],
                "query": "pharmaceutical",
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    # --- 15-16: Count prompts ---
    {
        "id": 15,
        "prompt": "Has the use of export restrictions increased since 2020?",
        "endpoint": "counts",
        "body": {
            "request_data": {
                "mast_chapters": [14],
                "count_by": ["date_announced_year"],
                "count_variable": "intervention_id",
            },
        },
    },
    {
        "id": "16a",
        "prompt": "How many harmful interventions were implemented globally in 2025?",
        "endpoint": "counts",
        "body": {
            "request_data": {
                "gta_evaluation": [1, 2],
                "implementation_period": ["2025-01-01", "2025-12-31"],
                "count_by": ["date_implemented_year"],
                "count_variable": "intervention_id",
            },
        },
    },
    {
        "id": "16b",
        "prompt": "How many harmful interventions were implemented globally in 2024?",
        "endpoint": "counts",
        "body": {
            "request_data": {
                "gta_evaluation": [1, 2],
                "implementation_period": ["2024-01-01", "2024-12-31"],
                "count_by": ["date_implemented_year"],
                "count_variable": "intervention_id",
            },
        },
    },
    # --- 17-20: Advanced search prompts ---
    {
        "id": 17,
        "prompt": "Which interventions target state-owned enterprises specifically?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "eligible_firms": [4],
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 18,
        "prompt": "What subnational measures has the US implemented since 2023?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [840],
                "implementation_level": [3],
                "announcement_period": ["2023-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 19,
        "prompt": "What FDI screening measures target Chinese investments in European technology sectors?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "affected": [156],
                "intervention_types": [25],
                "query": "technology",
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    {
        "id": 20,
        "prompt": "What measures have G7 countries coordinated against Russia since February 2022?",
        "endpoint": "data",
        "body": {
            "limit": 50,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "implementer": [840, 826, 251, 276, 381, 392, 124],
                "affected": [643],
                "announcement_period": ["2022-02-01", "2099-12-31"],
            },
        },
    },
    # --- 21-23: New feature tests ---
    {
        "id": 21,
        "prompt": "Overview mode -- semiconductor measures (test detail_level=overview via show_keys)",
        "endpoint": "data",
        "body": {
            "limit": 500,
            "offset": 0,
            "sorting": "-date_announced",
            "request_data": {
                "query": "semiconductor",
                "in_force_on_date": TODAY,
                "keep_in_force_on_date": True,
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
            "show_keys": [
                "intervention_id",
                "state_act_title",
                "intervention_type",
                "gta_evaluation",
                "date_announced",
                "is_in_force",
                "implementing_jurisdictions",
                "intervention_url",
            ],
        },
    },
    {
        "id": 22,
        "prompt": "Recently modified interventions (test -last_updated sorting and update_period)",
        "endpoint": "data",
        "body": {
            "limit": 20,
            "offset": 0,
            "sorting": "-last_updated",
            "request_data": {
                "update_period": ["2026-02-01", None],
                "announcement_period": ["1900-01-01", "2099-12-31"],
            },
        },
    },
    # Prompt 23 is dynamic -- built after prompt 21 returns IDs
]

# Prompt 23 template (filled after prompt 21 runs)
PROMPT_23_TEMPLATE = {
    "id": 23,
    "prompt": "Standard detail for specific IDs (test show_keys with intervention_id filter)",
    "endpoint": "data",
    "show_keys_standard": [
        "intervention_id",
        "state_act_id",
        "state_act_title",
        "intervention_type",
        "mast_chapter",
        "gta_evaluation",
        "implementation_level",
        "eligible_firm",
        "date_announced",
        "date_implemented",
        "date_removed",
        "is_in_force",
        "implementing_jurisdictions",
        "affected_jurisdictions",
        "affected_sectors",
        "intervention_url",
        "state_act_url",
        "is_official_source",
    ],
}


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def call_api(endpoint: str, body: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
    """Make a POST request to the GTA API and return structured result."""
    url = DATA_ENDPOINT if endpoint == "data" else COUNT_ENDPOINT
    t0 = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=body, headers=HEADERS)
            elapsed = round(time.time() - t0, 2)
            status = resp.status_code
            try:
                data = resp.json()
            except Exception:
                data = resp.text
            return {
                "status": status,
                "elapsed_s": elapsed,
                "data": data,
                "error": None if status == 200 else f"HTTP {status}",
            }
    except Exception as exc:
        elapsed = round(time.time() - t0, 2)
        return {
            "status": 0,
            "elapsed_s": elapsed,
            "data": None,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def count_results(data: Any, endpoint: str) -> int:
    """Extract result count from API response."""
    if endpoint == "data":
        if isinstance(data, list):
            return len(data)
        return 0
    elif endpoint == "counts":
        # counts returns {"count": N, "results": [...]} or just a list
        if isinstance(data, dict):
            results = data.get("results", [])
            return len(results) if isinstance(results, list) else 0
        if isinstance(data, list):
            return len(data)
        return 0
    return 0


def sample_results(data: Any, endpoint: str, n: int = 3) -> List[Dict[str, Any]]:
    """Extract a sample of results for reporting."""
    items = []
    if endpoint == "data" and isinstance(data, list):
        items = data[:n]
    elif endpoint == "counts":
        if isinstance(data, dict):
            items = (data.get("results") or [])[:n]
        elif isinstance(data, list):
            items = data[:n]
    # Trim large nested structures for readability
    trimmed = []
    for item in items:
        if isinstance(item, dict):
            trimmed_item = {}
            for k, v in item.items():
                if isinstance(v, list) and len(v) > 5:
                    trimmed_item[k] = v[:5]  # first 5 elements
                    trimmed_item[f"_{k}_total"] = len(v)
                elif isinstance(v, str) and len(v) > 300:
                    trimmed_item[k] = v[:300] + "..."
                else:
                    trimmed_item[k] = v
            trimmed.append(trimmed_item)
        else:
            trimmed.append(item)
    return trimmed


def get_response_keys(data: Any) -> Optional[List[str]]:
    """Get the keys of the first result item (for show_keys verification)."""
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        return sorted(data[0].keys())
    return None


def evaluate_prompt(prompt_def: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single prompt result."""
    evaluation = {
        "prompt_id": prompt_def["id"],
        "prompt": prompt_def["prompt"],
        "endpoint": prompt_def["endpoint"],
        "body_sent": prompt_def["body"],
        "http_status": result["status"],
        "elapsed_s": result["elapsed_s"],
        "error": result["error"],
        "result_count": count_results(result["data"], prompt_def["endpoint"]),
        "sample_results": sample_results(result["data"], prompt_def["endpoint"]),
        "response_keys": get_response_keys(result["data"]),
        "verdict": "UNKNOWN",
        "notes": [],
    }

    # Determine verdict
    if result["error"]:
        evaluation["verdict"] = "FAIL"
        evaluation["notes"].append(f"Error: {result['error']}")
    elif result["status"] != 200:
        evaluation["verdict"] = "FAIL"
        evaluation["notes"].append(f"Non-200 status: {result['status']}")
    elif evaluation["result_count"] == 0:
        evaluation["verdict"] = "WARN"
        evaluation["notes"].append("No results returned — may be legitimate or filter too narrow")
    else:
        evaluation["verdict"] = "PASS"
        evaluation["notes"].append(f"Returned {evaluation['result_count']} result(s)")

    return evaluation


# ---------------------------------------------------------------------------
# New-feature specific checks
# ---------------------------------------------------------------------------

def check_prompt_21(evaluation: Dict[str, Any], data: Any) -> None:
    """Verify overview mode: show_keys restricts response fields, limit=500 returns more."""
    expected_keys = sorted([
        "intervention_id", "state_act_title", "intervention_type",
        "gta_evaluation", "date_announced", "is_in_force",
        "implementing_jurisdictions", "intervention_url",
    ])
    actual_keys = evaluation.get("response_keys")

    if actual_keys:
        extra_keys = set(actual_keys) - set(expected_keys)
        missing_keys = set(expected_keys) - set(actual_keys)
        if extra_keys:
            evaluation["notes"].append(f"SHOW_KEYS: Extra fields returned: {sorted(extra_keys)}")
            evaluation["verdict"] = "WARN"
        if missing_keys:
            evaluation["notes"].append(f"SHOW_KEYS: Missing expected fields: {sorted(missing_keys)}")
            evaluation["verdict"] = "WARN"
        if not extra_keys and not missing_keys:
            evaluation["notes"].append("SHOW_KEYS: Response contains exactly the requested fields")

    if evaluation["result_count"] > 50:
        evaluation["notes"].append(f"LIMIT=500: Returned {evaluation['result_count']} results (more than default 50)")
    else:
        evaluation["notes"].append(f"LIMIT=500: Only {evaluation['result_count']} results returned (expected >50)")


def check_prompt_22(evaluation: Dict[str, Any], data: Any) -> None:
    """Verify -last_updated sorting and update_period filter."""
    if not isinstance(data, list) or len(data) == 0:
        evaluation["notes"].append("UPDATE_PERIOD: No results to verify")
        return

    # Check sorting: last_updated should be in descending order
    last_updated_values = []
    for item in data:
        lu = item.get("last_updated")
        if lu:
            last_updated_values.append(lu)

    if last_updated_values:
        is_sorted_desc = all(
            last_updated_values[i] >= last_updated_values[i + 1]
            for i in range(len(last_updated_values) - 1)
        )
        if is_sorted_desc:
            evaluation["notes"].append("SORTING: Results are correctly sorted by -last_updated (descending)")
        else:
            evaluation["notes"].append("SORTING: Results are NOT correctly sorted by -last_updated")
            evaluation["verdict"] = "WARN"

        # Check that all dates are from Feb 2026 or later
        all_recent = all(lu >= "2026-02-01" for lu in last_updated_values)
        if all_recent:
            evaluation["notes"].append("UPDATE_PERIOD: All results have last_updated >= 2026-02-01")
        else:
            old_dates = [lu for lu in last_updated_values if lu < "2026-02-01"]
            evaluation["notes"].append(
                f"UPDATE_PERIOD: {len(old_dates)} result(s) have last_updated before 2026-02-01"
            )
            evaluation["verdict"] = "WARN"
    else:
        evaluation["notes"].append("UPDATE_PERIOD: last_updated field not present in response (may need show_keys)")


def check_prompt_23(evaluation: Dict[str, Any], data: Any, requested_ids: List[int]) -> None:
    """Verify standard detail: correct show_keys and all requested IDs present."""
    expected_keys = sorted(PROMPT_23_TEMPLATE["show_keys_standard"])
    actual_keys = evaluation.get("response_keys")

    if actual_keys:
        extra_keys = set(actual_keys) - set(expected_keys)
        missing_keys = set(expected_keys) - set(actual_keys)
        if extra_keys:
            evaluation["notes"].append(f"SHOW_KEYS: Extra fields returned: {sorted(extra_keys)}")
            evaluation["verdict"] = "WARN"
        if missing_keys:
            evaluation["notes"].append(f"SHOW_KEYS: Missing expected fields: {sorted(missing_keys)}")
            evaluation["verdict"] = "WARN"
        if not extra_keys and not missing_keys:
            evaluation["notes"].append("SHOW_KEYS: Response contains exactly the requested standard fields")

    if isinstance(data, list):
        returned_ids = {item.get("intervention_id") for item in data if isinstance(item, dict)}
        missing_ids = set(requested_ids) - returned_ids
        if missing_ids:
            evaluation["notes"].append(f"IDs: Missing {len(missing_ids)} of {len(requested_ids)} requested IDs: {sorted(missing_ids)}")
            evaluation["verdict"] = "WARN"
        else:
            evaluation["notes"].append(f"IDs: All {len(requested_ids)} requested intervention IDs are present")


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def run_all_tests() -> List[Dict[str, Any]]:
    """Run all prompt tests and return evaluation results."""
    results = []
    prompt_21_data = None

    print(f"Running {len(PROMPTS)} prompts against live GTA API...\n")

    for i, prompt_def in enumerate(PROMPTS):
        pid = prompt_def["id"]
        print(f"  [{i+1}/{len(PROMPTS)+1}] Prompt {pid}: {prompt_def['prompt'][:70]}...")

        api_result = call_api(prompt_def["endpoint"], prompt_def["body"])
        evaluation = evaluate_prompt(prompt_def, api_result)

        # New-feature checks
        if pid == 21:
            check_prompt_21(evaluation, api_result["data"])
            prompt_21_data = api_result["data"]
        elif pid == 22:
            check_prompt_22(evaluation, api_result["data"])

        results.append(evaluation)

        # Rate-limit courtesy
        time.sleep(0.5)

    # --- Prompt 23: dynamic based on prompt 21 results ---
    print(f"  [{len(PROMPTS)+1}/{len(PROMPTS)+1}] Prompt 23: Standard detail for specific IDs...")

    prompt_23_ids = []
    if isinstance(prompt_21_data, list) and len(prompt_21_data) > 0:
        for item in prompt_21_data[:5]:
            if isinstance(item, dict) and "intervention_id" in item:
                prompt_23_ids.append(item["intervention_id"])

    if not prompt_23_ids:
        # Fallback: use some known IDs
        prompt_23_ids = [138295, 138296, 138297, 138298, 138299]
        print(f"    (Using fallback IDs: {prompt_23_ids})")

    prompt_23_body = {
        "limit": 5,
        "offset": 0,
        "request_data": {
            "intervention_id": prompt_23_ids,
            "announcement_period": ["1900-01-01", "2099-12-31"],
        },
        "show_keys": PROMPT_23_TEMPLATE["show_keys_standard"],
    }

    prompt_23_def = {
        "id": 23,
        "prompt": f"Standard detail for specific IDs: {prompt_23_ids}",
        "endpoint": "data",
        "body": prompt_23_body,
    }

    api_result = call_api("data", prompt_23_body)
    evaluation = evaluate_prompt(prompt_23_def, api_result)
    check_prompt_23(evaluation, api_result["data"], prompt_23_ids)
    results.append(evaluation)

    return results


def generate_report(results: List[Dict[str, Any]]) -> str:
    """Generate a markdown evaluation report from results."""
    lines = []
    lines.append("# GTA MCP Server -- Prompt Evaluation Report (v2)")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**API Base:** `{BASE_URL}`")
    lines.append(f"**Total Prompts Tested:** {len(results)}")
    lines.append("")

    # Summary counts
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    warn_count = sum(1 for r in results if r["verdict"] == "WARN")
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Verdict | Count |")
    lines.append(f"|---------|-------|")
    lines.append(f"| PASS | {pass_count} |")
    lines.append(f"| WARN | {warn_count} |")
    lines.append(f"| FAIL | {fail_count} |")
    lines.append("")

    # Summary table
    lines.append("## Results Overview")
    lines.append("")
    lines.append("| # | Prompt | Status | Results | Time (s) | Verdict |")
    lines.append("|---|--------|--------|---------|----------|---------|")
    for r in results:
        prompt_short = r["prompt"][:55] + ("..." if len(r["prompt"]) > 55 else "")
        lines.append(
            f"| {r['prompt_id']} | {prompt_short} | {r['http_status']} | {r['result_count']} | {r['elapsed_s']} | **{r['verdict']}** |"
        )
    lines.append("")

    # Per-prompt details
    lines.append("---")
    lines.append("")
    lines.append("## Per-Prompt Details")
    lines.append("")

    for r in results:
        lines.append(f"### Prompt {r['prompt_id']}: {r['prompt']}")
        lines.append("")
        lines.append(f"- **Endpoint:** `{r['endpoint']}`")
        lines.append(f"- **HTTP Status:** {r['http_status']}")
        lines.append(f"- **Result Count:** {r['result_count']}")
        lines.append(f"- **Response Time:** {r['elapsed_s']}s")
        lines.append(f"- **Verdict:** **{r['verdict']}**")
        lines.append("")

        if r["notes"]:
            lines.append("**Notes:**")
            for note in r["notes"]:
                lines.append(f"- {note}")
            lines.append("")

        if r.get("response_keys"):
            lines.append(f"**Response Keys:** `{', '.join(r['response_keys'])}`")
            lines.append("")

        if r["sample_results"]:
            lines.append("**Sample Results:**")
            lines.append("```json")
            lines.append(json.dumps(r["sample_results"], indent=2, default=str)[:3000])
            lines.append("```")
            lines.append("")

        # Show request body
        lines.append("<details>")
        lines.append("<summary>Request Body</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(r["body_sent"], indent=2, default=str))
        lines.append("```")
        lines.append("</details>")
        lines.append("")

    # New feature section
    lines.append("---")
    lines.append("")
    lines.append("## New Feature Verification (Prompts 21-23)")
    lines.append("")

    for r in results:
        if r["prompt_id"] in (21, 22, 23):
            lines.append(f"### Prompt {r['prompt_id']}: {r['prompt'][:80]}")
            lines.append("")
            lines.append(f"- **Verdict:** **{r['verdict']}**")
            for note in r["notes"]:
                lines.append(f"- {note}")
            lines.append("")

    # Overall assessment
    lines.append("---")
    lines.append("")
    lines.append("## Overall Assessment")
    lines.append("")

    if fail_count == 0 and warn_count == 0:
        lines.append("All prompts passed successfully. The GTA MCP server's API integration is working correctly for all 23 test cases.")
    elif fail_count == 0:
        lines.append(
            f"No failures detected. {warn_count} prompt(s) returned warnings (typically zero results or minor "
            f"discrepancies). The core API integration is functioning correctly."
        )
    else:
        lines.append(
            f"{fail_count} prompt(s) failed. These require investigation. "
            f"{warn_count} prompt(s) returned warnings. {pass_count} prompt(s) passed."
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = run_all_tests()

    # Save raw results
    print(f"\nSaving results to {RESULTS_FILE}")
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate and save report
    report = generate_report(results)
    print(f"Saving report to {REPORT_FILE}")
    with open(REPORT_FILE, "w") as f:
        f.write(report)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        icon = {"PASS": "[OK]", "WARN": "[!!]", "FAIL": "[XX]"}.get(r["verdict"], "[??]")
        print(f"  {icon} Prompt {str(r['prompt_id']):>3s}: {r['result_count']:>4d} results | {r['elapsed_s']:>5.1f}s | {r['prompt'][:60]}")
    print("=" * 60)

    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    warn_count = sum(1 for r in results if r["verdict"] == "WARN")
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    print(f"  PASS: {pass_count}  |  WARN: {warn_count}  |  FAIL: {fail_count}")
    print(f"\nDone.")
