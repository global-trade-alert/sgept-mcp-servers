#!/usr/bin/env python3
"""Test DPA API authentication."""

import asyncio
import httpx
import json

async def test_dpa_api():
    """Test DPA API with provided key."""

    api_key = "7df2e67c7a4ec6473652a3e0f9127a820a9b87cf"
    base_url = "https://api.digitalpolicyalert.org"  # Using DPA URL

    headers = {
        "Authorization": f"APIKey {api_key}",
        "Content-Type": "application/json"
    }

    body = {
        "limit": 5,
        "offset": 0,
        "sorting": "-id",
        "request_data": {
            "event_period": ["2025-10-01", "2025-10-31"]
        }
    }

    print("=" * 80)
    print("TESTING DPA API")
    print("=" * 80)
    print()
    print(f"URL: {base_url}/api/v2/dpa/data/")
    print(f"API Key: {api_key[:20]}...")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/api/v2/dpa/data/",
                json=body,
                headers=headers
            )

            print(f"Status Code: {response.status_code}")
            print()

            if response.status_code == 200:
                data = response.json()
                print(f"✅ DPA API WORKS! Got response")
                print(f"Results: {len(data) if isinstance(data, list) else 'N/A'}")
                if isinstance(data, list) and len(data) > 0:
                    print()
                    print("First event:")
                    print(json.dumps(data[0], indent=2)[:1000])
                return True
            else:
                print(f"❌ DPA API Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    asyncio.run(test_dpa_api())
