#!/usr/bin/env python3
"""Debug test to show exactly what's being sent."""

import asyncio
import httpx

async def debug_keys():
    """Show exact keys being used."""

    gta_key = "96b947f0c8c4d7a84fcdb7238b4c3107f7b3f774"
    dpa_key = "7df2e67c7a4ec6473652a3e0f9127a820a9b87cf"

    print("=" * 80)
    print("DEBUG: API KEYS")
    print("=" * 80)
    print()
    print(f"GTA Key:")
    print(f"  Length: {len(gta_key)}")
    print(f"  Value: '{gta_key}'")
    print(f"  Has spaces: {' ' in gta_key}")
    has_newlines_gta = '\n' in gta_key or '\r' in gta_key
    print(f"  Has newlines: {has_newlines_gta}")
    print()
    print(f"DPA Key:")
    print(f"  Length: {len(dpa_key)}")
    print(f"  Value: '{dpa_key}'")
    print(f"  Has spaces: {' ' in dpa_key}")
    has_newlines_dpa = '\n' in dpa_key or '\r' in dpa_key
    print(f"  Has newlines: {has_newlines_dpa}")
    print()
    print("=" * 80)
    print("TESTING WITH SIMPLE REQUEST")
    print("=" * 80)
    print()

    # Ultra simple request
    simple_body = {
        "limit": 1,
        "request_data": {
            "announcement_period": ["2025-01-01", "2025-12-31"]
        }
    }

    headers = {
        "Authorization": f"APIKey {gta_key}",
        "Content-Type": "application/json"
    }

    print(f"Headers being sent:")
    for k, v in headers.items():
        if k == "Authorization":
            # Show header value clearly
            print(f"  {k}: '{v}'")
            print(f"    Length: {len(v)}")
        else:
            print(f"  {k}: {v}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("Sending request to GTA API...")
            response = await client.post(
                "https://api.globaltradealert.org/api/v2/gta/data/",
                json=simple_body,
                headers=headers
            )

            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text[:500]}")

        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_keys())
