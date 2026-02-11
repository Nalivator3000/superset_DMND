#!/usr/bin/env python3
"""
Test Keitaro API - timezone and status investigation
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

# Test different status values
print("=== Test: Different conversion statuses ===")

for status in ["lead", "sale", "rejected", None]:
    filters = [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
        }
    ]

    if status:
        filters.append({
            "name": "status",
            "operator": "EQUALS",
            "expression": status
        })

    payload = {
        "range": {
            "from": "2026-01-14",
            "to": "2026-01-19",
            "timezone": "Europe/Moscow"
        },
        "columns": [],
        "metrics": ["conversions"],
        "grouping": ["day"],
        "filters": filters,
        "limit": 10000
    }

    try:
        response = requests.post(
            f"{KEITARO_URL}/admin_api/v1/report/build",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        rows = data.get("rows", [])
        status_name = status or "all"
        print(f"\nStatus '{status_name}': {len(rows)} rows")
        for row in rows:
            print(f"  {row.get('day')}: {row.get('conversions')}")

    except Exception as e:
        print(f"Error for status {status}: {e}")

# Test with conversion_type instead of status
print("\n=== Test: Different conversion types (lead vs sale) ===")

for conv_type in ["lead", "sale"]:
    payload = {
        "range": {
            "from": "2026-01-14",
            "to": "2026-01-19",
            "timezone": "Europe/Moscow"
        },
        "columns": [],
        "metrics": [conv_type + "s"],  # leads or sales
        "grouping": ["day"],
        "filters": [
            {
                "name": "campaign_id",
                "operator": "EQUALS",
                "expression": str(campaign_id)
            }
        ],
        "limit": 10000
    }

    try:
        response = requests.post(
            f"{KEITARO_URL}/admin_api/v1/report/build",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        rows = data.get("rows", [])
        print(f"\nMetric '{conv_type}s': {len(rows)} rows")
        for row in rows:
            print(f"  {row.get('day')}: {row.get(conv_type + 's')}")

    except Exception as e:
        print(f"Error for {conv_type}: {e}")

# Check system settings
print("\n=== Test: Keitaro system info ===")
try:
    response = requests.get(
        f"{KEITARO_URL}/admin_api/v1/settings",
        headers=headers,
        timeout=30
    )
    if response.status_code == 200:
        settings = response.json()
        print(f"Settings: {json.dumps(settings, indent=2)[:500]}")
    else:
        print(f"Settings endpoint returned: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

# Check clicks data as comparison
print("\n=== Test: Clicks data (not conversions) ===")
payload = {
    "range": {
        "from": "2026-01-14",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": [],
    "metrics": ["clicks", "conversions", "leads", "sales"],
    "grouping": ["day"],
    "filters": [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
        }
    ],
    "limit": 10000
}

try:
    response = requests.post(
        f"{KEITARO_URL}/admin_api/v1/report/build",
        headers=headers,
        json=payload,
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("rows", [])
    print(f"Total rows: {len(rows)}")
    for row in rows:
        print(f"  {row}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
