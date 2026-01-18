#!/usr/bin/env python3
"""
Keitaro to PostgreSQL Sync Service
Fetches conversion logs from Keitaro API and stores in PostgreSQL
"""

import os
import time
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KEITARO_URL = os.environ.get("KEITARO_URL", "https://kt.dmnd.team")
KEITARO_API_KEY = os.environ.get("KEITARO_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
SYNC_INTERVAL = int(os.environ.get("SYNC_INTERVAL", 300))  # 5 minutes
CAMPAIGN_IDS = os.environ.get("CAMPAIGN_IDS", "12").split(",")  # Topacio campaign


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL)


def init_database():
    """Create tables if not exist"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS keitaro_conversions (
            id SERIAL PRIMARY KEY,
            campaign_id INTEGER,
            campaign_name VARCHAR(255),
            datetime TIMESTAMP,
            clicks INTEGER,
            conversions INTEGER,
            revenue DECIMAL(18,2),
            cost DECIMAL(18,2),
            sub_id VARCHAR(255),
            country VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(campaign_id, datetime)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_keitaro_campaign_id
        ON keitaro_conversions(campaign_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_keitaro_datetime
        ON keitaro_conversions(datetime)
    """)

    conn.commit()
    cur.close()
    conn.close()
    logger.info("Database initialized")


def fetch_keitaro_data(campaign_id, date_from, date_to):
    """Fetch conversion data from Keitaro API"""
    headers = {
        "Api-Key": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "range": {
            "from": date_from,
            "to": date_to,
            "timezone": "UTC"
        },
        "columns": [
            "datetime",
            "campaign_id",
            "clicks",
            "conversions",
            "revenue",
            "cost",
            "sub_id_1",
            "country"
        ],
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
        return data.get("rows", [])
    except Exception as e:
        logger.error(f"Error fetching Keitaro data: {e}")
        return []


def get_campaign_name(campaign_id):
    """Get campaign name from Keitaro"""
    headers = {"Api-Key": KEITARO_API_KEY}
    try:
        response = requests.get(
            f"{KEITARO_URL}/admin_api/v1/campaigns/{campaign_id}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("name", f"Campaign {campaign_id}")
    except:
        return f"Campaign {campaign_id}"


def sync_campaign(campaign_id):
    """Sync data for a specific campaign"""
    logger.info(f"Syncing campaign {campaign_id}")

    # Get last 7 days of data
    date_to = datetime.utcnow().strftime("%Y-%m-%d")
    date_from = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    rows = fetch_keitaro_data(campaign_id, date_from, date_to)
    if not rows:
        logger.info(f"No data for campaign {campaign_id}")
        return 0

    campaign_name = get_campaign_name(campaign_id)

    conn = get_db_connection()
    cur = conn.cursor()

    # Prepare data for insert
    values = []
    for row in rows:
        values.append((
            campaign_id,
            campaign_name,
            row.get("datetime"),
            row.get("clicks", 0),
            row.get("conversions", 0),
            row.get("revenue", 0),
            row.get("cost", 0),
            row.get("sub_id_1", ""),
            row.get("country", "")
        ))

    # Upsert data
    execute_values(
        cur,
        """
        INSERT INTO keitaro_conversions
        (campaign_id, campaign_name, datetime, clicks, conversions, revenue, cost, sub_id, country)
        VALUES %s
        ON CONFLICT (campaign_id, datetime)
        DO UPDATE SET
            clicks = EXCLUDED.clicks,
            conversions = EXCLUDED.conversions,
            revenue = EXCLUDED.revenue,
            cost = EXCLUDED.cost,
            sub_id = EXCLUDED.sub_id,
            country = EXCLUDED.country
        """,
        values
    )

    conn.commit()
    cur.close()
    conn.close()

    logger.info(f"Synced {len(values)} records for campaign {campaign_id}")
    return len(values)


def run_sync():
    """Run sync for all campaigns"""
    total = 0
    for campaign_id in CAMPAIGN_IDS:
        campaign_id = campaign_id.strip()
        if campaign_id:
            total += sync_campaign(int(campaign_id))
    return total


def main():
    """Main entry point"""
    logger.info("Starting Keitaro sync service")
    logger.info(f"Keitaro URL: {KEITARO_URL}")
    logger.info(f"Campaigns: {CAMPAIGN_IDS}")
    logger.info(f"Sync interval: {SYNC_INTERVAL}s")

    if not KEITARO_API_KEY:
        logger.error("KEITARO_API_KEY not set!")
        return

    if not DATABASE_URL:
        logger.error("DATABASE_URL not set!")
        return

    # Initialize database
    init_database()

    # Run sync loop
    while True:
        try:
            records = run_sync()
            logger.info(f"Sync complete. Total records: {records}")
        except Exception as e:
            logger.error(f"Sync error: {e}")

        logger.info(f"Sleeping for {SYNC_INTERVAL} seconds...")
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    main()
