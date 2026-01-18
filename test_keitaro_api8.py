#!/usr/bin/env python3
"""
Test Keitaro API - conversions/log endpoint
"""

import os
import requests
import json

KEITARO_URL = "https://kt.dmnd.team"
KEITARO_API_KEY = os.environ.get("KEITARO_API_KEY")

headers = {
    "Api-Key": KEITARO_API_KEY,
    "Content-Type": "application/json"
}

campaign_id = 12

print("=== Test: /conversions/log endpoint ===")

# Try the conversions/log endpoint
payload = {
    "range": {
        "from": "2026-01-14",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": ["datetime", "sub_id_2", "revenue", "status"],
    "filters": [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
        }
    ],
    "limit": 100,
    "offset": 0
}

try:
    response = requests.post(
        f"{KEITARO_URL}/admin_api/v1/conversions/log",
        headers=headers,
        json=payload,
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict):
            rows = data.get("rows", data.get("conversions", []))
            total = data.get("total", len(rows))
            print(f"Total: {total}, Rows returned: {len(rows)}")
            print("\nFirst 10 rows:")
            for row in rows[:10]:
                print(f"  {row}")

            # Group by day
            by_day = {}
            for row in rows:
                dt = row.get("datetime", "")[:10]
                by_day[dt] = by_day.get(dt, 0) + 1
            print("\nBy day:")
            for day in sorted(by_day.keys()):
                print(f"  {day}: {by_day[day]}")
        elif isinstance(data, list):
            print(f"Rows returned: {len(data)}")
            for row in data[:10]:
                print(f"  {row}")
    else:
        print(f"Response: {response.text[:1000]}")

except Exception as e:
    print(f"Error: {e}")

# Try without columns parameter
print("\n=== Test: /conversions/log without specific columns ===")
payload2 = {
    "range": {
        "from": "2026-01-14",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "filters": [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
        }
    ],
    "limit": 10
}

try:
    response = requests.post(
        f"{KEITARO_URL}/admin_api/v1/conversions/log",
        headers=headers,
        json=payload2,
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            rows = data.get("rows", data.get("conversions", []))
            print(f"Rows: {len(rows)}")
            if rows:
                print(f"First row keys: {rows[0].keys() if isinstance(rows[0], dict) else 'not dict'}")
                print(f"First row: {rows[0]}")
        elif isinstance(data, list) and data:
            print(f"First item keys: {data[0].keys() if isinstance(data[0], dict) else 'not dict'}")
            print(f"First item: {data[0]}")
    else:
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

# Try GET request
print("\n=== Test: GET /conversions/log ===")
try:
    response = requests.get(
        f"{KEITARO_URL}/admin_api/v1/conversions/log",
        headers=headers,
        params={
            "campaign_id": campaign_id,
            "date_from": "2026-01-14",
            "date_to": "2026-01-19",
            "limit": 10
        },
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:1000]}")
    else:
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
