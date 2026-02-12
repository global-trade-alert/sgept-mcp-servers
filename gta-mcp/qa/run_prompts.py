"""Run all 20 sample prompts against the live GTA API and save results."""

import asyncio
import json
import os
import sys
import traceback
from datetime import date

# Add parent to path so we can import gta_mcp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gta_mcp.api import build_filters, build_count_filters, GTAAPIClient
import httpx

API_KEY = os.environ['GTA_API_KEY']
HEADERS = {'Authorization': f'APIKey {API_KEY}', 'Content-Type': 'application/json'}
BASE_URL = 'https://api.globaltradealert.org'


async def search(params, limit=50):
    """Execute a search query against the GTA data endpoint."""
    filters, messages = build_filters(params)
    body = {'limit': limit, 'offset': 0, 'request_data': filters}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f'{BASE_URL}/api/v2/gta/data/', json=body, headers=HEADERS)
        if resp.status_code == 200:
            return resp.status_code, resp.json(), messages, filters
        else:
            return resp.status_code, resp.text, messages, filters


async def count(params, count_by, count_variable='intervention_id'):
    """Execute a count query against the GTA data-counts endpoint."""
    filters, messages = build_count_filters(params)
    filters['count_by'] = count_by
    filters['count_variable'] = count_variable
    body = {'request_data': filters}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body, headers=HEADERS)
        if resp.status_code == 200:
            return resp.status_code, resp.json(), messages, filters
        else:
            return resp.status_code, resp.text, messages, filters


def extract_titles(data, max_n=3):
    """Extract first N intervention titles from search results."""
    if not isinstance(data, list):
        return []
    titles = []
    for item in data[:max_n]:
        title = item.get('title', item.get('state_act_title', 'No title'))
        titles.append(title)
    return titles


def extract_count_summary(data, max_n=5):
    """Extract first N count groups from count results."""
    if isinstance(data, dict):
        results = data.get('results', [])
    elif isinstance(data, list):
        results = data
    else:
        return []
    return results[:max_n]


# Define all 20 prompts with their params and query type
PROMPTS = [
    {
        "id": 1,
        "prompt": "What tariffs has the US imposed on China since Jan 2025?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["USA"],
            "affected_jurisdictions": ["CHN"],
            "date_announced_gte": "2025-01-01",
            "intervention_types": ["Import tariff"],
        },
    },
    {
        "id": 2,
        "prompt": "Which countries have retaliated against US tariffs in 2025?",
        "type": "search",
        "params": {
            "affected_jurisdictions": ["USA"],
            "date_announced_gte": "2025-01-01",
            "gta_evaluation": ["Red", "Amber"],
        },
    },
    {
        "id": 3,
        "prompt": "What Section 232 measures has the US implemented since 2025?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["USA"],
            "query": "Section 232",
            "date_announced_gte": "2025-01-01",
        },
    },
    {
        "id": 4,
        "prompt": "What export controls has China imposed on rare earth elements?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["CHN"],
            "mast_chapters": ["P"],
            "query": "rare earth",
        },
    },
    {
        "id": 5,
        "prompt": "What subsidies are governments providing for critical mineral processing?",
        "type": "search",
        "params": {
            "mast_chapters": ["L"],
            "query": "critical mineral",
        },
    },
    {
        "id": 6,
        "prompt": "Has the use of export restrictions increased since 2020?",
        "type": "count",
        "params": {
            "mast_chapters": ["P"],
            "date_announced_gte": "2020-01-01",
            "gta_evaluation": [4],
        },
        "count_by": ["announcement_year"],
        "count_variable": "intervention_id",
    },
    {
        "id": 7,
        "prompt": "What measures currently affect semiconductor manufacturing equipment trade?",
        "type": "search",
        "params": {
            "query": "semiconductor",
            "is_in_force": True,
        },
    },
    {
        "id": 8,
        "prompt": "Which countries subsidise their domestic semiconductor industry?",
        "type": "search",
        "params": {
            "query": "semiconductor",
            "mast_chapters": ["L"],
        },
    },
    {
        "id": 9,
        "prompt": "What harmful measures has the EU imposed on US exports since 2024?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["EU"],
            "affected_jurisdictions": ["USA"],
            "gta_evaluation": ["Red", "Amber"],
            "date_announced_gte": "2024-01-01",
        },
    },
    {
        "id": 10,
        "prompt": "What measures has Brazil implemented affecting US agricultural exports?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["BRA"],
            "affected_jurisdictions": ["USA"],
        },
    },
    {
        "id": 11,
        "prompt": "Compare trade barriers imposed by ASEAN members on EU services",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["IDN", "THA", "VNM", "MYS", "PHL", "SGP", "BRN", "KHM", "LAO", "MMR"],
            "affected_jurisdictions": ["EU"],
            "gta_evaluation": ["Red", "Amber"],
        },
    },
    {
        "id": 12,
        "prompt": "What local content requirements affect automotive production in Southeast Asia?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["IDN", "THA", "VNM", "MYS", "PHL"],
            "intervention_types": ["Local content requirement"],
        },
    },
    {
        "id": 13,
        "prompt": "Find all anti-dumping investigations targeting Chinese steel since 2020",
        "type": "search",
        "params": {
            "affected_jurisdictions": ["CHN"],
            "query": "steel anti-dumping",
            "date_announced_gte": "2020-01-01",
        },
    },
    {
        "id": 14,
        "prompt": "What safeguard measures are currently in force on solar panels?",
        "type": "search",
        "params": {
            "query": "solar panel safeguard",
            "is_in_force": True,
        },
    },
    {
        "id": 15,
        "prompt": "What import licensing requirements affect pharmaceutical products in India?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["IND"],
            "query": "pharmaceutical import licen",
        },
    },
    {
        "id": 16,
        "prompt": "What technical barriers to trade affect medical device imports in the EU?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["EU"],
            "query": "medical device",
        },
    },
    {
        "id": 17,
        "prompt": "Which G20 countries have increased state aid to EV manufacturers since 2022?",
        "type": "search",
        "params": {
            "mast_chapters": ["L"],
            "query": "electric vehicle",
            "date_announced_gte": "2022-01-01",
        },
    },
    {
        "id": 18,
        "prompt": "Which interventions target state-owned enterprises specifically?",
        "type": "search",
        "params": {
            "eligible_firms": ["state-controlled"],
        },
    },
    {
        "id": 19,
        "prompt": "What subnational measures has the US implemented since 2023?",
        "type": "search",
        "params": {
            "implementing_jurisdictions": ["USA"],
            "implementation_levels": ["subnational"],
            "date_announced_gte": "2023-01-01",
        },
    },
    {
        "id": 20,
        "prompt": "How many harmful interventions were implemented globally in 2025 versus 2024?",
        "type": "count",
        "params": {
            "gta_evaluation": [4],
            "date_implemented_gte": "2024-01-01",
        },
        "count_by": ["implementation_year"],
        "count_variable": "intervention_id",
    },
]


async def run_all():
    results = []

    for p in PROMPTS:
        prompt_id = p["id"]
        prompt_text = p["prompt"]
        query_type = p["type"]
        params = p["params"]

        print(f"Running prompt {prompt_id}: {prompt_text[:60]}...")

        try:
            if query_type == "search":
                status, data, messages, filters_used = await search(params)
                num_results = len(data) if isinstance(data, list) else 0
                first_titles = extract_titles(data)
                result = {
                    "id": prompt_id,
                    "prompt": prompt_text,
                    "type": query_type,
                    "params_sent": params,
                    "filters_used": filters_used,
                    "http_status": status,
                    "num_results": num_results,
                    "first_titles": first_titles,
                    "messages": messages,
                    "error": None if status == 200 else str(data),
                }
            else:
                count_by = p.get("count_by", ["announcement_year"])
                count_variable = p.get("count_variable", "intervention_id")
                status, data, messages, filters_used = await count(params, count_by, count_variable)
                count_groups = extract_count_summary(data)
                result = {
                    "id": prompt_id,
                    "prompt": prompt_text,
                    "type": query_type,
                    "params_sent": params,
                    "filters_used": filters_used,
                    "http_status": status,
                    "count_groups": count_groups,
                    "messages": messages,
                    "error": None if status == 200 else str(data),
                }

            print(f"  -> Status {status}, ", end="")
            if query_type == "search":
                print(f"{result['num_results']} results")
            else:
                print(f"{len(count_groups)} count groups")

        except Exception as e:
            traceback.print_exc()
            result = {
                "id": prompt_id,
                "prompt": prompt_text,
                "type": query_type,
                "params_sent": params,
                "filters_used": {},
                "http_status": -1,
                "error": str(e),
                "messages": [],
            }
            print(f"  -> ERROR: {e}")

        results.append(result)
        # Small delay to be polite to the API
        await asyncio.sleep(0.5)

    return results


async def main():
    results = await run_all()

    # Custom serializer for non-JSON types
    def default_serializer(obj):
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    output_path = os.path.join(os.path.dirname(__file__), 'prompt-test-results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=default_serializer)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
