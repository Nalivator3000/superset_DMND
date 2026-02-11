#!/usr/bin/env python3
"""
Test Keitaro API to debug missing dates
"""

import os
import requests
import json
from datetime import datetime, timedelta

# Configuration - you need to set KEITARO_API_KEY environment variable
KEITARO_URL = "https://kt.dmnd.team"
KEITARO_API_KEY = os.environ.get("KEITARO_API_KEY")

if not KEITARO_API_KEY:
    print("ERROR: KEITARO_API_KEY environment variable not set")
    print("Set it with: set KEITARO_API_KEY=your_api_key")
    exit(1)

headers = {
    "Api-Key": KEITARO_API_KEY,
    "Content-Type": "application/json"
}

campaign_id = 12
date_from = "2026-01-01"
date_to = "2026-01-18"

print(f"Testing Keitaro API")
print(f"URL: {KEITARO_URL}")
print(f"Campaign: {campaign_id}")
print(f"Date range: {date_from} to {date_to}")
print("-" * 50)

# Test 1: Aggregated report with grouping by day and sub_id_2
print("\n=== Test 1: Aggregated report (day + sub_id_2) ===")
payload1 = {
    "range": {
        "from": date_from,
        "to": date_to,
        "timezone": "UTC"
    },
    "columns": [],
    "metrics": ["conversions"],
    "grouping": ["day", "sub_id_2"],
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
        json=payload1,
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("rows", [])
    print(f"Total rows: {len(rows)}")

    # Group by date
    by_date = {}
    for row in rows:
        day = row.get("day", "unknown")
        event_type = row.get("sub_id_2", "unknown") or "unknown"
        conversions = int(row.get("conversions", 0))
        if day not in by_date:
            by_date[day] = {}
        by_date[day][event_type] = conversions

    print("\nData by date:")
    for date in sorted(by_date.keys()):
        total = sum(by_date[date].values())
        events = by_date[date]
        print(f"  {date}: {total} events - {events}")

except Exception as e:
    print(f"Error: {e}")

# Test 2: Just group by day
print("\n=== Test 2: Aggregated report (day only) ===")
payload2 = {
    "range": {
        "from": date_from,
        "to": date_to,
        "timezone": "UTC"
    },
    "columns": [],
    "metrics": ["conversions"],
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
        json=payload2,
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("rows", [])
    print(f"Total rows: {len(rows)}")

    print("\nData by date:")
    for row in sorted(rows, key=lambda x: x.get("day", "")):
        print(f"  {row.get('day')}: {row.get('conversions')} conversions")

except Exception as e:
    print(f"Error: {e}")

# Test 3: Try different timezone
print("\n=== Test 3: With Europe/Moscow timezone ===")
payload3 = {
    "range": {
        "from": date_from,
        "to": date_to,
        "timezone": "Europe/Moscow"
    },
    "columns": [],
    "metrics": ["conversions"],
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
        json=payload3,
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("rows", [])
    print(f"Total rows: {len(rows)}")

    print("\nData by date:")
    for row in sorted(rows, key=lambda x: x.get("day", "")):
        print(f"  {row.get('day')}: {row.get('conversions')} conversions")

except Exception as e:
    print(f"Error: {e}")

# Test 4: Get conversions list directly
print("\n=== Test 4: Conversions log endpoint ===")
try:
    response = requests.get(
        f"{KEITARO_URL}/admin_api/v1/conversions",
        headers=headers,
        params={
            "campaign_id": campaign_id,
            "date_from": date_from,
            "date_to": date_to,
            "limit": 100
        },
        timeout=60
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        print(f"Total conversions returned: {len(data)}")
        if data:
            print("Sample conversion:")
            print(json.dumps(data[0], indent=2)[:500])
    else:
        print(f"Response type: {type(data)}")
        print(json.dumps(data, indent=2)[:1000])

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
print("Done testing")
