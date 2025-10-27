#!/usr/bin/env python3
"""Direct API test to diagnose 403 error."""

import asyncio
import httpx
import json

async def test_gta_api_direct():
    """Test GTA API directly with detailed debugging."""

    api_key = "96b947f0c8c4d7a84fcdb7238b4c3107f7b3f774"
    base_url = "https://api.globaltradealert.org"

    headers = {
        "Authorization": f"APIKey {api_key}",
        "Content-Type": "application/json"
    }

    # Simple query for recent data
    body = {
        "limit": 10,
        "offset": 0,
        "sorting": "-date_announced",
        "request_data": {
            "announcement_period": ["2025-10-16", "2025-10-23"]
        }
    }

    print("=" * 80)
    print("DIRECT GTA API TEST")
    print("=" * 80)
    print()
    print(f"URL: {base_url}/api/v2/gta/data/")
    print(f"Headers: {headers}")
    print(f"Body: {json.dumps(body, indent=2)}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/api/v2/gta/data/",
                json=body,
                headers=headers
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print()

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Got {len(data) if isinstance(data, list) else 'unknown'} results")
                print()
                print(json.dumps(data, indent=2)[:2000])
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:1000]}")

        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gta_api_direct())
