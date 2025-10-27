#!/usr/bin/env python3
"""Test if brackets should be literal in the Authorization header."""

import asyncio
import httpx
import json

async def test_all_variations():
    """Try all possible header variations."""

    api_key = "96b947f0c8c4d7a84fcdb7238b4c3107f7b3f774"

    # Test different header formats
    variations = [
        ("Without brackets", f"APIKey {api_key}"),
        ("With brackets", f"APIKey [{api_key}]"),
        ("Just the key", api_key),
    ]

    body = {
        "limit": 5,
        "offset": 0,
        "sorting": ["-date_announced"],
        "request_data": {
            "announcement_period": ["2025-10-16", "2025-10-23"]
        }
    }

    print("=" * 80)
    print("TESTING ALL AUTHORIZATION HEADER VARIATIONS")
    print("=" * 80)
    print()
    print(f"Request Body: {json.dumps(body, indent=2)}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for name, auth_value in variations:
            headers = {
                "Authorization": auth_value,
                "Content-Type": "application/json"
            }

            print(f"--- Testing: {name} ---")
            print(f"Authorization header: '{auth_value}'")

            try:
                response = await client.post(
                    "https://api.globaltradealert.org/api/v2/gta/data/",
                    json=body,
                    headers=headers
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS WITH: {name}")
                    print(f"Count: {data.get('count', 'N/A')}")
                    print(f"Results: {len(data.get('results', []))}")
                    print()

                    # Show first result
                    results = data.get('results', [])
                    if results:
                        first = results[0]
                        print(f"First intervention:")
                        print(f"  ID: {first.get('intervention_id')}")
                        print(f"  Title: {first.get('state_act_title', 'N/A')[:100]}")
                        print(f"  Date: {first.get('date_announced')}")

                    return True
                elif response.status_code == 403:
                    print(f"❌ 403 Forbidden - Access denied")
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"Response: {response.text[:200]}")

            except Exception as e:
                print(f"❌ Exception: {e}")

            print()

    print("=" * 80)
    print("❌ None of the variations worked")
    print("=" * 80)
    print()
    print("This confirms the API key doesn't have permissions.")
    print("Please verify with Liubomyr that:")
    print("1. The key is active")
    print("2. The key has permissions for /api/v2/gta/data/")
    print("3. There are no IP restrictions blocking this request")

    return False

if __name__ == "__main__":
    asyncio.run(test_all_variations())
