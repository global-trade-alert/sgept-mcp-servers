#!/bin/bash
# Quick test script for GTA and DPA APIs
# Usage: ./QUICK_TEST.sh

echo "================================"
echo "QUICK API TEST"
echo "================================"
echo ""

# Replace these with your actual API keys
GTA_KEY="96b947f0c8c4d7a84fcdb7238b4c3107f7b3f774"
DPA_KEY="7df2e67c7a4ec6473652a3e0f9127a820a9b87cf"

echo "Testing GTA API..."
echo "---"
curl -X POST "https://api.globaltradealert.org/api/v2/gta/data/" \
  -H "Content-Type: application/json" \
  -H "Authorization: APIKey $GTA_KEY" \
  -d '{
    "limit": 2,
    "offset": 0,
    "sorting": ["-date_announced"],
    "request_data": {
      "announcement_period": ["2025-10-16", "2025-10-23"]
    }
  }' 2>&1 | head -50

echo ""
echo ""
echo "================================"
echo ""
echo "Testing DPA API..."
echo "---"
curl -X POST "https://api.globaltradealert.org/api/v1/dpa/events/" \
  -H "Content-Type: application/json" \
  -H "Authorization: APIKey $DPA_KEY" \
  -d '{
    "limit": 2,
    "offset": 0,
    "sorting": ["-id"],
    "request_data": {
      "event_period": ["2025-10-01", "2025-10-31"]
    }
  }' 2>&1 | head -50

echo ""
echo "================================"
echo "If you see JSON data above, the APIs are working!"
echo "If you see 'Access denied', the API keys need activation."
echo "================================"
