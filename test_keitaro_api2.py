#!/usr/bin/env python3
"""
Test Keitaro API - extended tests
"""

import os
import requests
import json
from datetime import datetime, timedelta

KEITARO_URL = "https://kt.dmnd.team"
KEITARO_API_KEY = os.environ.get("KEITARO_API_KEY")

headers = {
    "Api-Key": KEITARO_API_KEY,
    "Content-Type": "application/json"
}

campaign_id = 12

# Test with today as end date
today = datetime.now().strftime("%Y-%m-%d")
date_from = "2026-01-14"
date_to = "2026-01-19"  # Tomorrow to be safe

print(f"Testing with date range: {date_from} to {date_to}")
print(f"Today is: {today}")
print("-" * 50)

# Test: Try conversions endpoint differently
print("\n=== Test: Report with different parameters ===")

# Try without any grouping - just total
payload = {
    "range": {
        "from": date_from,
        "to": date_to,
        "timezone": "UTC"
    },
    "columns": [],
    "metrics": ["conversions"],
    "grouping": ["datetime"],  # Try grouping by datetime
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

    if rows:
        # Show first and last few
        print("\nFirst 5 rows:")
        for row in rows[:5]:
            print(f"  {row}")
        print("\nLast 5 rows:")
        for row in rows[-5:]:
            print(f"  {row}")

except Exception as e:
    print(f"Error: {e}")

# Try hour grouping
print("\n=== Test: Report grouped by hour ===")
payload2 = {
    "range": {
        "from": date_from,
        "to": date_to,
        "timezone": "UTC"
    },
    "columns": [],
    "metrics": ["conversions"],
    "grouping": ["hour"],
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

    # Group by day from hour data
    by_day = {}
    for row in rows:
        hour = row.get("hour", "")
        if hour:
            day = hour.split(" ")[0] if " " in hour else hour[:10]
            conversions = int(row.get("conversions", 0))
            by_day[day] = by_day.get(day, 0) + conversions

    print("\nData by day (from hour grouping):")
    for day in sorted(by_day.keys()):
        print(f"  {day}: {by_day[day]} conversions")

except Exception as e:
    print(f"Error: {e}")

# Try sub_id grouping for recent dates
print("\n=== Test: Only last 3 days ===")
payload3 = {
    "range": {
        "from": "2026-01-16",
        "to": "2026-01-18",
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
        json=payload3,
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    rows = data.get("rows", [])
    print(f"Total rows: {len(rows)}")
    print(f"Rows: {rows}")

except Exception as e:
    print(f"Error: {e}")

# Check if the campaign has data at all
print("\n=== Test: Campaign info ===")
try:
    response = requests.get(
        f"{KEITARO_URL}/admin_api/v1/campaigns/{campaign_id}",
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    campaign = response.json()
    print(f"Campaign name: {campaign.get('name')}")
    print(f"Campaign state: {campaign.get('state')}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
