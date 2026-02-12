"""Re-run count queries with correct count_by dimension names."""
import asyncio, os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import httpx

API_KEY = os.environ['GTA_API_KEY']
HEADERS = {'Authorization': f'APIKey {API_KEY}', 'Content-Type': 'application/json'}
BASE_URL = 'https://api.globaltradealert.org'

async def main():
    # Prompt 6: Export restrictions by announced year
    print("=== Prompt 6: Export restrictions by date_announced_year ===")
    body = {'request_data': {
        'mast_chapters': [14],
        'gta_evaluation': [4],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'count_by': ['date_announced_year'],
        'count_variable': 'intervention_id',
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body, headers=HEADERS)
        print(f"Status: {r.status_code}")
        d = r.json()
        print(f"Count: {d.get('count', 'N/A')}")
        results = d.get('results', [])
        print(f"Results: {len(results)} groups")
        for item in results[:10]:
            print(f"  {json.dumps(item)}")

    # Prompt 20: Harmful by implementation year
    print("\n=== Prompt 20: Harmful by date_implemented_year ===")
    body2 = {'request_data': {
        'gta_evaluation': [4],
        'implementation_period': ['2024-01-01', '2099-12-31'],
        'count_by': ['date_implemented_year'],
        'count_variable': 'intervention_id',
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v1/gta/data-counts/', json=body2, headers=HEADERS)
        print(f"Status: {r.status_code}")
        d = r.json()
        print(f"Count: {d.get('count', 'N/A')}")
        results = d.get('results', [])
        print(f"Results: {len(results)} groups")
        for item in results[:10]:
            print(f"  {json.dumps(item)}")

    # Also test: prompt 13 with separated query terms
    print("\n=== Prompt 13: steel + anti-dumping (separated) ===")
    body3 = {'limit': 5, 'offset': 0, 'request_data': {
        'affected': [156],
        'announcement_period': ['2020-01-01', '2099-12-31'],
        'query': 'steel',
        'intervention_types': [51],
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v2/gta/data/', json=body3, headers=HEADERS)
        data = r.json()
        n = len(data) if isinstance(data, list) else 0
        print(f"Status: {r.status_code}, Results: {n}")
        if n > 0:
            for d in data[:3]:
                print(f"  - {d.get('state_act_title', 'N/A')}")

    # Prompt 14: solar panel safeguard - try splitting
    print("\n=== Prompt 14: 'solar' + safeguard type ===")
    body4 = {'limit': 10, 'offset': 0, 'request_data': {
        'query': 'solar',
        'intervention_types': [52],
        'in_force_on_date': '2026-02-12',
        'keep_in_force_on_date': True,
        'announcement_period': ['1900-01-01', '2099-12-31'],
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v2/gta/data/', json=body4, headers=HEADERS)
        data = r.json()
        n = len(data) if isinstance(data, list) else 0
        print(f"Status: {r.status_code}, Results: {n}")
        if n > 0:
            for d in data[:5]:
                print(f"  - {d.get('state_act_title', 'N/A')}")

    # Prompt 15: India pharma - try broader search
    print("\n=== Prompt 15: India + pharmaceutical (broader) ===")
    body5 = {'limit': 10, 'offset': 0, 'request_data': {
        'implementer': [699],
        'query': 'pharmaceutical',
        'announcement_period': ['1900-01-01', '2099-12-31'],
    }}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f'{BASE_URL}/api/v2/gta/data/', json=body5, headers=HEADERS)
        data = r.json()
        n = len(data) if isinstance(data, list) else 0
        print(f"Status: {r.status_code}, Results: {n}")
        if n > 0:
            for d in data[:5]:
                print(f"  - {d.get('state_act_title', 'N/A')}")

asyncio.run(main())
