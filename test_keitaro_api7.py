#!/usr/bin/env python3
"""
Test Keitaro API - try conversion log export approach
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

# The CSV shows conversion logs - let's try the conversions report with columns
# Based on error messages, these columns should exist:
# conversion_id, datetime, sub_id_2, revenue, status

print("=== Test: Conversions report without type parameter ===")

# Try with only basic grouping and conversion metrics
payload = {
    "range": {
        "from": "2026-01-14",
        "to": "2026-01-19",
        "timezone": "Europe/Moscow"
    },
    "columns": [],
    "metrics": ["conversions", "revenue"],
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
        json=payload,
        timeout=60
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        rows = data.get("rows", [])
        total = data.get("total", 0)
        print(f"Total: {total}, Rows: {len(rows)}")

        # Sort by date
        rows_sorted = sorted(rows, key=lambda x: x.get("day", ""))
        for row in rows_sorted:
            print(f"  {row}")
    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

# Try with different granularity - include conversion_datetime if possible
print("\n=== Test: Check available metrics ===")
metrics_to_try = ["conversions", "leads", "sales", "revenue", "cost", "profit", "clicks", "unique_clicks"]

for metric in metrics_to_try:
    payload = {
        "range": {
            "from": "2026-01-14",
            "to": "2026-01-19",
            "timezone": "Europe/Moscow"
        },
        "columns": [],
        "metrics": [metric],
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
        if response.status_code == 200:
            data = response.json()
            rows = data.get("rows", [])
            print(f"Metric '{metric}': {len(rows)} rows")
            for row in rows:
                value = row.get(metric, "N/A")
                print(f"  {row.get('day')}: {value}")
        else:
            print(f"Metric '{metric}': Error")

    except Exception as e:
        print(f"Metric '{metric}': Exception")

# Check if there's pagination or data storage limit
print("\n=== Test: Check data retention - older dates ===")

date_ranges = [
    ("2026-01-01", "2026-01-05"),
    ("2026-01-05", "2026-01-10"),
    ("2026-01-10", "2026-01-15"),
    ("2026-01-15", "2026-01-20"),
]

for date_from, date_to in date_ranges:
    payload = {
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
        "limit": 100
    }

    try:
        response = requests.post(
            f"{KEITARO_URL}/admin_api/v1/report/build",
            headers=headers,
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            rows = data.get("rows", [])
            total_conv = sum(row.get("conversions", 0) for row in rows)
            print(f"Range {date_from} to {date_to}: {total_conv} conversions in {len(rows)} days")
        else:
            print(f"Range {date_from} to {date_to}: Error")

    except Exception as e:
        print(f"Range {date_from} to {date_to}: Exception")

print("\n" + "=" * 50)
