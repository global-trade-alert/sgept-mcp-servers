"""Investigate edge cases: count endpoint grouping, and 0-result queries."""
import asyncio, os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import httpx

API_KEY = os.environ['GTA_API_KEY']
HEADERS = {'Authorization': f'APIKey {API_KEY}', 'Content-Type': 'application/json'}
BASE_URL = 'https://api.globaltradealert.org'

async def raw_count(body_rd):
    """Send raw request_data to counts endpoint."""
    body = {'request_data': body_rd}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body, headers=HEADERS)
        return r.status_code, r.json() if r.status_code == 200 else r.text

async def raw_search(body_rd, limit=10):
    body = {'limit': limit, 'offset': 0, 'request_data': body_rd}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v2/gta/data/', json=body, headers=HEADERS)
        return r.status_code, r.json() if r.status_code == 200 else r.text

async def main():
    print("=== 1. Count endpoint: export restrictions by year ===")
    status, data = await raw_count({
        'mast_chapters': [14],
        'gta_evaluation': [4],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'count_by': ['announcement_year'],
        'count_variable': 'intervention_id',
    })
    print(f"Status: {status}")
    print(json.dumps(data, indent=2)[:1000])

    print("\n=== 2. Count endpoint: harmful by implementation year ===")
    status, data = await raw_count({
        'gta_evaluation': [4],
        'implementation_period': ['2024-01-01', '2099-12-31'],
        'count_by': ['implementation_year'],
        'count_variable': 'intervention_id',
    })
    print(f"Status: {status}")
    print(json.dumps(data, indent=2)[:1000])

    print("\n=== 3. Prompt 13 fix: split 'steel' and 'anti-dumping' ===")
    # Try text search for just "steel" with intervention type filter
    status, data = await raw_search({
        'affected': [156],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'query': 'steel',
        'intervention_types': [51],  # Anti-dumping
    })
    n = len(data) if isinstance(data, list) else 0
    print(f"Status: {status}, Results: {n}")
    if n > 0:
        for d in data[:3]:
            print(f"  - {d.get('title', 'N/A')}")

    print("\n=== 3b. Prompt 13 alt: anti-dumping affecting CHN with steel sectors ===")
    status, data = await raw_search({
        'affected': [156],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'intervention_types': [51],  # Anti-dumping
        'affected_sectors': [411, 412],  # Basic iron and steel + Products of iron or steel
    })
    n = len(data) if isinstance(data, list) else 0
    print(f"Status: {status}, Results: {n}")
    if n > 0:
        for d in data[:3]:
            print(f"  - {d.get('title', 'N/A')}")

    print("\n=== 4. Prompt 14 fix: try 'solar' query with safeguard type ===")
    status, data = await raw_search({
        'query': 'solar',
        'intervention_types': [52],  # Safeguard
        'in_force_on_date': '2026-02-12',
        'keep_in_force_on_date': True,
        'announcement_period': ['1900-01-01', '2099-12-31'],
    })
    n = len(data) if isinstance(data, list) else 0
    print(f"Status: {status}, Results: {n}")
    if n > 0:
        for d in data[:3]:
            print(f"  - {d.get('title', 'N/A')}")

    print("\n=== 4b. Prompt 14 alt: 'solar' + safeguard, no in_force filter ===")
    status, data = await raw_search({
        'query': 'solar',
        'intervention_types': [52],  # Safeguard
        'announcement_period': ['1900-01-01', '2099-12-31'],
    })
    n = len(data) if isinstance(data, list) else 0
    print(f"Status: {status}, Results: {n}")
    if n > 0:
        for d in data[:3]:
            print(f"  - {d.get('title', 'N/A')}")

    print("\n=== 5. Prompt 15 fix: India (699) + 'pharmaceutical' only ===")
    status, data = await raw_search({
        'implementer': [699],
        'query': 'pharmaceutical',
        'announcement_period': ['1900-01-01', '2099-12-31'],
    })
    n = len(data) if isinstance(data, list) else 0
    print(f"Status: {status}, Results: {n}")
    if n > 0:
        for d in data[:3]:
            print(f"  - {d.get('title', 'N/A')}")

    print("\n=== 5b. Prompt 15 alt: India + import licensing type ===")
    status, data = await raw_search({
        'implementer': [699],
        'intervention_types': [36],  # Import licensing requirement
        'announcement_period': ['1900-01-01', '2099-12-31'],
    })
    n = len(data) if isinstance(data, list) else 0
    print(f"Status: {status}, Results: {n}")
    if n > 0:
        for d in data[:3]:
            print(f"  - {d.get('title', 'N/A')}")

    print("\n=== 5c. Prompt 15 alt: India + pharma sector (352) ===")
    status, data = await raw_search({
        'implementer': [699],
        'intervention_types': [36],  # Import licensing requirement
        'affected_sectors': [352],  # Pharmaceutical products
        'announcement_period': ['1900-01-01', '2099-12-31'],
    })
    n = len(data) if isinstance(data, list) else 0
    print(f"Status: {status}, Results: {n}")
    if n > 0:
        for d in data[:3]:
            print(f"  - {d.get('title', 'N/A')}")

asyncio.run(main())
