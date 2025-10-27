#!/usr/bin/env python3
"""Test script to verify GTA MCP server returns expected data."""

import asyncio
import sys
import os

# Add the gta_mcp module to the path
sys.path.insert(0, '/home/user/sgept-mcp-servers/gta-mcp/src')

from gta_mcp.api import GTAAPIClient, build_filters

async def test_recent_interventions():
    """Test fetching recent interventions from GTA."""

    # Set API key
    api_key = "96b947f0c8c4d7a84fcdb7238b4c3107f7b3f774"

    # Create client
    client = GTAAPIClient(api_key)

    print("=" * 80)
    print("TESTING GTA MCP SERVER - Recent Interventions (Oct 16-23, 2025)")
    print("=" * 80)
    print()

    try:
        # Search for interventions announced in the specified period
        # Note: The date in the example is Oct 16-23, 2025, but today is Oct 27, 2025
        params = {
            "date_announced_gte": "2025-10-16",
            "date_announced_lte": "2025-10-23",
        }

        print(f"📡 Querying GTA API with parameters:")
        print(f"   Date range: {params['date_announced_gte']} to {params['date_announced_lte']}")
        print()

        # Build filters using the API module
        filters = build_filters(params)

        print(f"🔧 API filters: {filters}")
        print()

        # Call the API
        response = await client.search_interventions(
            filters=filters,
            limit=50,
            offset=0,
            sorting="-date_announced"
        )

        print("=" * 80)
        print("RESULTS:")
        print("=" * 80)
        print()

        # Print basic info
        if isinstance(response, dict):
            print(f"Total interventions found: {response.get('count', 'N/A')}")
            results = response.get('results', []) if 'results' in response else response if isinstance(response, list) else []
        else:
            results = response if isinstance(response, list) else []

        print(f"Results returned: {len(results)}")
        print()

        # Print first few interventions
        for i, intervention in enumerate(results[:10], 1):
            int_id = intervention.get('intervention_id', 'N/A')
            title = intervention.get('title', 'N/A')
            date = intervention.get('date_announced', 'N/A')
            implementers = intervention.get('implementing_jurisdictions', [])

            print(f"\n{i}. {title}")
            print(f"   ID: {int_id}")
            print(f"   Date: {date}")
            print(f"   Implementers: {implementers[:3] if isinstance(implementers, list) else implementers}")
            print(f"   URL: https://globaltradealert.org/intervention/{int_id}")

        print()
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recent_interventions())
