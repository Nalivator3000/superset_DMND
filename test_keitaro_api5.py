#!/usr/bin/env python3
"""
Test Keitaro API - using correct event columns
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

# Test with event columns
print("=== Test: Events report with correct columns ===")
payload = {
    "range": {
        "from": "2026-01-18",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": ["event_id", "event_type", "datetime", "sub_id"],
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
        print(f"Total: {total}, Rows returned: {len(rows)}")
        if rows:
            print("First 5 rows:")
            for row in rows[:5]:
                print(f"  {row}")
    else:
        error_text = response.text[:1000]
        print(f"Error: {error_text}")

except Exception as e:
    print(f"Error: {e}")

# Test with event_type filter for conversions
print("\n=== Test: Filter by event_type = conversion ===")
payload2 = {
    "range": {
        "from": "2026-01-14",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": ["datetime", "sub_id"],
    "metrics": [],
    "grouping": [],
    "filters": [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
        },
        {
            "name": "event_type",
            "operator": "EQUALS",
            "expression": "conversion"
        }
    ],
    "limit": 100
}

try:
    response = requests.post(
        f"{KEITARO_URL}/admin_api/v1/report/build",
        headers=headers,
        json=payload2,
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
            # Group by day
            by_day = {}
            for row in rows:
                dt = row.get("datetime", "")[:10]
                by_day[dt] = by_day.get(dt, 0) + 1
            print("\nBy day:")
            for day in sorted(by_day.keys()):
                print(f"  {day}: {by_day[day]}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

# Test with different date ranges
print("\n=== Test: Broader date range - last week ===")
payload3 = {
    "range": {
        "from": "2026-01-10",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": ["datetime"],
    "metrics": [],
    "grouping": [],
    "filters": [
        {
            "name": "campaign_id",
            "operator": "EQUALS",
            "expression": str(campaign_id)
        },
        {
            "name": "event_type",
            "operator": "EQUALS",
            "expression": "conversion"
        }
    ],
    "limit": 5000
}

try:
    response = requests.post(
        f"{KEITARO_URL}/admin_api/v1/report/build",
        headers=headers,
        json=payload3,
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        rows = data.get("rows", [])
        total = data.get("total", 0)
        print(f"Total: {total}, Rows returned: {len(rows)}")

        # Group by day
        by_day = {}
        for row in rows:
            dt = row.get("datetime", "")[:10]
            by_day[dt] = by_day.get(dt, 0) + 1
        print("\nBy day:")
        for day in sorted(by_day.keys()):
            print(f"  {day}: {by_day[day]}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

# Try just looking at all events
print("\n=== Test: All events (any type) ===")
payload4 = {
    "range": {
        "from": "2026-01-16",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": ["event_type", "datetime"],
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
        json=payload4,
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        rows = data.get("rows", [])
        total = data.get("total", 0)
        print(f"Total: {total}, Rows returned: {len(rows)}")
        if rows:
            print("First 10 rows:")
            for row in rows[:10]:
                print(f"  {row}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
