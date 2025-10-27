#!/usr/bin/env python3
"""Test different authentication formats."""

import asyncio
import httpx
import json

async def test_auth_variations():
    """Try different authentication header formats."""

    api_key = "96b947f0c8c4d7a84fcdb7238b4c3107f7b3f774"
    base_url = "https://api.globaltradealert.org"

    auth_variations = [
        ("APIKey format", {"Authorization": f"APIKey {api_key}"}),
        ("Token format", {"Authorization": f"Token {api_key}"}),
        ("Bearer format", {"Authorization": f"Bearer {api_key}"}),
        ("X-API-Key header", {"X-API-Key": api_key}),
        ("Direct key", {"Authorization": api_key}),
    ]

    body = {
        "limit": 1,
        "offset": 0,
        "request_data": {
            "announcement_period": ["2025-10-01", "2025-10-31"]
        }
    }

    print("=" * 80)
    print("TESTING DIFFERENT AUTH FORMATS")
    print("=" * 80)
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for name, headers in auth_variations:
            headers["Content-Type"] = "application/json"

            try:
                response = await client.post(
                    f"{base_url}/api/v2/gta/data/",
                    json=body,
                    headers=headers
                )

                status = "✅ SUCCESS" if response.status_code == 200 else f"❌ {response.status_code}"
                print(f"{name:20s} -> {status}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"   Got {len(data) if isinstance(data, list) else 'N/A'} results")
                    print(f"   Working headers: {headers}")
                    return True

            except Exception as e:
                print(f"{name:20s} -> ❌ Exception: {e}")

    print()
    print("=" * 80)
    print("❌ None of the authentication formats worked.")
    print("This suggests the API key may be invalid or not have proper permissions.")
    print("=" * 80)
    return False

if __name__ == "__main__":
    asyncio.run(test_auth_variations())
