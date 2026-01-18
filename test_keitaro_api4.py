#!/usr/bin/env python3
"""
Test Keitaro API - find conversion logs endpoint
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

# Try different endpoints for conversion logs
endpoints_to_try = [
    "/admin_api/v1/conversions",
    "/admin_api/v1/conversion/log",
    "/admin_api/v1/logs/conversions",
    "/admin_api/v1/report/conversions",
    "/admin_api/v1/campaigns/12/conversions",
    "/admin_api/v1/campaigns/12/logs",
    "/admin_api/v1/logs",
]

print("=== Testing different endpoints ===")
for endpoint in endpoints_to_try:
    print(f"\nTrying: {endpoint}")
    try:
        # Try GET
        response = requests.get(
            f"{KEITARO_URL}{endpoint}",
            headers=headers,
            params={"campaign_id": campaign_id, "limit": 10},
            timeout=30
        )
        print(f"  GET: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response type: {type(data)}")
            if isinstance(data, list) and data:
                print(f"  First item keys: {data[0].keys() if isinstance(data[0], dict) else 'not a dict'}")
            elif isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
    except Exception as e:
        print(f"  GET Error: {e}")

    try:
        # Try POST
        response = requests.post(
            f"{KEITARO_URL}{endpoint}",
            headers=headers,
            json={"campaign_id": campaign_id, "limit": 10},
            timeout=30
        )
        print(f"  POST: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response type: {type(data)}")
    except Exception as e:
        print(f"  POST Error: {e}")

# Try the raw columns approach with conversion_id
print("\n=== Test: Report with conversion details ===")
payload = {
    "range": {
        "from": "2026-01-18",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": ["conversion_id", "datetime", "sub_id_2", "status"],
    "metrics": [],
    "grouping": [],
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
        f"{KEITARO_URL}/admin_api/v1/report/build",
        headers=headers,
        json=payload,
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        rows = data.get("rows", [])
        total = data.get("total", 0)
        print(f"Total: {total}, Rows returned: {len(rows)}")
        if rows:
            print("First 5 rows:")
            for row in rows[:5]:
                print(f"  {row}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

# Try fetching conversions through clicks endpoint
print("\n=== Test: Clicks with conversion info ===")
payload = {
    "range": {
        "from": "2026-01-18",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": ["click_id", "datetime", "sub_id_2", "conversion_status", "conversion_datetime"],
    "metrics": [],
    "grouping": [],
    "filters": [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
        },
        {
            "name": "is_converted",
            "operator": "EQUALS",
            "expression": "1"
        }
    ],
    "limit": 100
}

try:
    response = requests.post(
        f"{KEITARO_URL}/admin_api/v1/report/build",
        headers=headers,
        json=payload,
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        rows = data.get("rows", [])
        total = data.get("total", 0)
        print(f"Total: {total}, Rows returned: {len(rows)}")
        if rows:
            print("First 5 rows:")
            for row in rows[:5]:
                print(f"  {row}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
