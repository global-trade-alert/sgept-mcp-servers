#!/usr/bin/env python3
"""Test GTA and DPA APIs with corrected format based on documentation."""

import asyncio
import httpx
import json

async def test_gta_corrected():
    """Test GTA API with corrected format."""

    api_key = "96b947f0c8c4d7a84fcdb7238b4c3107f7b3f774"

    # According to documentation:
    # - URL: https://api.globaltradealert.org/api/v2/gta/data/
    # - Header: APIKey (name) with value "APIKey [YOUR_API_KEY]"
    # - OR: Authorization: APIKey [YOUR_API_KEY]
    # - sorting is an ARRAY, not a string!

    # Try both header formats
    headers_variations = [
        {
            "APIKey": f"APIKey {api_key}",
            "Content-Type": "application/json"
        },
        {
            "Authorization": f"APIKey {api_key}",
            "Content-Type": "application/json"
        }
    ]

    # Corrected body with sorting as ARRAY
    body = {
        "limit": 25,
        "offset": 0,
        "sorting": ["-date_announced"],  # ARRAY, not string!
        "request_data": {
            "announcement_period": ["2025-10-16", "2025-10-23"]
        }
    }

    print("=" * 80)
    print("TESTING GTA API WITH CORRECTED FORMAT")
    print("=" * 80)
    print()
    print(f"URL: https://api.globaltradealert.org/api/v2/gta/data/")
    print(f"Body: {json.dumps(body, indent=2)}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, headers in enumerate(headers_variations, 1):
            print(f"--- Attempt {i}: {list(headers.keys())[0]} header ---")
            try:
                response = await client.post(
                    "https://api.globaltradealert.org/api/v2/gta/data/",
                    json=body,
                    headers=headers
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS!")
                    print(f"Count: {data.get('count', 'N/A')}")
                    results = data.get('results', [])
                    print(f"Results returned: {len(results)}")
                    print()

                    # Print first few
                    for j, intervention in enumerate(results[:5], 1):
                        int_id = intervention.get('intervention_id', 'N/A')
                        title = intervention.get('state_act_title', 'N/A')
                        date = intervention.get('date_announced', 'N/A')
                        print(f"{j}. [{date}] {title}")
                        print(f"   ID: {int_id}")
                        print(f"   URL: https://globaltradealert.org/intervention/{int_id}")
                        print()

                    return True
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    print()

            except Exception as e:
                print(f"❌ Exception: {e}")
                print()

    return False


async def test_dpa_corrected():
    """Test DPA API with corrected endpoint."""

    api_key = "7df2e67c7a4ec6473652a3e0f9127a820a9b87cf"

    # According to documentation:
    # - URL: https://api.globaltradealert.org/api/v1/dpa/events/ (not v2!)

    headers_variations = [
        {
            "APIKey": f"APIKey {api_key}",
            "Content-Type": "application/json"
        },
        {
            "Authorization": f"APIKey {api_key}",
            "Content-Type": "application/json"
        }
    ]

    body = {
        "limit": 10,
        "offset": 0,
        "sorting": ["-id"],  # ARRAY format
        "request_data": {
            "event_period": ["2025-10-01", "2025-10-31"]
        }
    }

    print("=" * 80)
    print("TESTING DPA API WITH CORRECTED FORMAT")
    print("=" * 80)
    print()
    print(f"URL: https://api.globaltradealert.org/api/v1/dpa/events/")
    print(f"Body: {json.dumps(body, indent=2)}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, headers in enumerate(headers_variations, 1):
            print(f"--- Attempt {i}: {list(headers.keys())[0]} header ---")
            try:
                response = await client.post(
                    "https://api.globaltradealert.org/api/v1/dpa/events/",
                    json=body,
                    headers=headers
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ DPA API SUCCESS!")
                    print(f"Count: {data.get('count', 'N/A')}")
                    results = data.get('results', [])
                    print(f"Results returned: {len(results)}")
                    print()

                    # Print first few
                    for j, event in enumerate(results[:5], 1):
                        event_id = event.get('id', 'N/A')
                        title = event.get('title', 'N/A')
                        date = event.get('date', 'N/A')
                        print(f"{j}. [{date}] {title}")
                        print(f"   ID: {event_id}")
                        print()

                    return True
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    print()

            except Exception as e:
                print(f"❌ Exception: {e}")
                print()

    return False


async def main():
    """Run all tests."""

    print("\n" + "=" * 80)
    print("SGEPT API TESTS - CORRECTED FORMAT")
    print("=" * 80)
    print()

    gta_success = await test_gta_corrected()
    print()
    dpa_success = await test_dpa_corrected()

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"GTA API: {'✅ WORKING' if gta_success else '❌ FAILED'}")
    print(f"DPA API: {'✅ WORKING' if dpa_success else '❌ FAILED'}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
