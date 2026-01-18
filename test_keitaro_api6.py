#!/usr/bin/env python3
"""
Test Keitaro API - find the right report type
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

# Try different report types
report_types = ["conversions", "conversion", "leads", "sales", "postbacks", "clicks"]

print("=== Testing different report types ===")
for report_type in report_types:
    print(f"\n--- Report type: {report_type} ---")
    payload = {
        "range": {
            "from": "2026-01-14",
            "to": "2026-01-19",
            "timezone": "Europe/Moscow"
        },
        "type": report_type,
        "columns": [],
        "metrics": ["count"],
        "grouping": ["day"],
        "filters": [
            {
                "name": "campaign_id",
                "operator": "EQUALS",
                "expression": str(campaign_id)
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
            print(f"Total: {total}, Rows: {len(rows)}")
            for row in rows[:10]:
                print(f"  {row}")
        else:
            print(f"Error: {response.text[:200]}")

    except Exception as e:
        print(f"Error: {e}")

# Try postbacks/conversions specific endpoint with raw data
print("\n=== Test: Postbacks/conversions log ===")
payload = {
    "range": {
        "from": "2026-01-14",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "type": "conversions",
    "columns": ["conversion_id", "datetime", "sub_id_2", "revenue", "status"],
    "metrics": [],
    "grouping": [],
    "filters": [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
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
        print(f"Total: {total}, Rows: {len(rows)}")
        for row in rows[:5]:
            print(f"  {row}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

# Check available report types
print("\n=== Test: Available API endpoints ===")
endpoints = [
    "/admin_api/v1/report/types",
    "/admin_api/v1/report/schemas",
    "/admin_api/v1/report/definitions",
]

for endpoint in endpoints:
    try:
        response = requests.get(
            f"{KEITARO_URL}{endpoint}",
            headers=headers,
            timeout=30
        )
        print(f"{endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(f"  {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 50)
