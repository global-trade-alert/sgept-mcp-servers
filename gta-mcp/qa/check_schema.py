"""Check the actual schema of v2 data endpoint responses."""
import asyncio, os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import httpx

API_KEY = os.environ['GTA_API_KEY']
HEADERS = {'Authorization': f'APIKey {API_KEY}', 'Content-Type': 'application/json'}
BASE_URL = 'https://api.globaltradealert.org'

async def main():
    # Get one search result and dump keys
    body = {'limit': 2, 'offset': 0, 'request_data': {
        'implementer': [840],
        'announcement_period': ['2025-01-01', '2099-12-31'],
        'intervention_types': [47],
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v2/gta/data/', json=body, headers=HEADERS)
        data = r.json()

    print("=== v2 data response structure ===")
    if isinstance(data, list) and len(data) > 0:
        print(f"Type: list of {len(data)} items")
        item = data[0]
        print(f"First item keys: {list(item.keys())}")
        # Print first item (truncated)
        print(json.dumps(item, indent=2, default=str)[:2000])
    else:
        print(f"Type: {type(data)}")
        print(json.dumps(data, indent=2, default=str)[:2000])

    # Try count endpoint with different count_by format
    print("\n=== Count with count_by=['year_announced'] ===")
    body2 = {'request_data': {
        'mast_chapters': [14],
        'gta_evaluation': [4],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'count_by': ['year_announced'],
        'count_variable': 'intervention_id',
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body2, headers=HEADERS)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2)[:1000])

    print("\n=== Count with count_by=['year'] ===")
    body3 = {'request_data': {
        'mast_chapters': [14],
        'gta_evaluation': [4],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'count_by': ['year'],
        'count_variable': 'intervention_id',
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body3, headers=HEADERS)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2)[:1000])

    print("\n=== Count with count_by=['date_announced'] ===")
    body4 = {'request_data': {
        'mast_chapters': [14],
        'gta_evaluation': [4],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'count_by': ['date_announced'],
        'count_variable': 'intervention_id',
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body4, headers=HEADERS)
        print(f"Status: {r.status_code}")
        d = r.json()
        print(json.dumps(d, indent=2)[:1500])

    print("\n=== Count with count_by=['implementer'] ===")
    body5 = {'request_data': {
        'mast_chapters': [14],
        'gta_evaluation': [4],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'count_by': ['implementer'],
        'count_variable': 'intervention_id',
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body5, headers=HEADERS)
        print(f"Status: {r.status_code}")
        d = r.json()
        print(f"Count: {d.get('count', 'N/A')}")
        results = d.get('results', [])
        print(f"Results items: {len(results)}")
        print(json.dumps(results[:5], indent=2))

asyncio.run(main())
