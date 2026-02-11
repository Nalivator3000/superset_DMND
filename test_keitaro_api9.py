#!/usr/bin/env python3
"""
Test Keitaro API - conversions/log with pagination
"""

import os
import requests
import json
from collections import defaultdict

KEITARO_URL = "https://kt.dmnd.team"
KEITARO_API_KEY = os.environ.get("KEITARO_API_KEY")

headers = {
    "Api-Key": KEITARO_API_KEY,
    "Content-Type": "application/json"
}

campaign_id = 12

print("=== Fetching all conversions with pagination ===")

all_rows = []
offset = 0
limit = 500
total = None

while True:
    payload = {
        "range": {
            "from": "2026-01-01",
            "to": "2026-01-20",
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
        "limit": limit,
        "offset": offset
    }

    try:
        response = requests.post(
            f"{KEITARO_URL}/admin_api/v1/conversions/log",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            print(f"Error at offset {offset}: {response.status_code}")
            break

        data = response.json()
        rows = data.get("rows", [])

        if total is None:
            total = data.get("total", 0)
            print(f"Total records: {total}")

        if not rows:
            break

        all_rows.extend(rows)
        print(f"Fetched {len(all_rows)} / {total}")

        offset += limit

        if offset >= total:
            break

    except Exception as e:
        print(f"Error: {e}")
        break

print(f"\nTotal fetched: {len(all_rows)}")

# Analyze by day and event type
by_day_type = defaultdict(lambda: defaultdict(int))
by_day_total = defaultdict(int)

for row in all_rows:
    dt = row.get("datetime", "")[:10]
    event_type = row.get("sub_id_2", "unknown") or "unknown"
    by_day_type[dt][event_type] += 1
    by_day_total[dt] += 1

print("\n=== Data by day and event type ===")
for day in sorted(by_day_type.keys()):
    print(f"\n{day}: {by_day_total[day]} total")
    for event_type, count in sorted(by_day_type[day].items()):
        print(f"  {event_type}: {count}")

# Summary
print("\n=== Summary by event type ===")
event_totals = defaultdict(int)
for day_data in by_day_type.values():
    for event_type, count in day_data.items():
        event_totals[event_type] += count

for event_type, count in sorted(event_totals.items(), key=lambda x: -x[1]):
    print(f"  {event_type}: {count}")

print("\n" + "=" * 50)
