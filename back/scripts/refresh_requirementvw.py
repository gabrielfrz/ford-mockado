"""Refresh the local FEDE requirement table from its source BigQuery view."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.bigquery_client import get_client
from datetime import datetime

QUERY = """
CREATE OR REPLACE TABLE `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.fede_daily_requirementvw` AS
SELECT * FROM `prj-dfad-1242-uapd-p-1242.bq_707_fedve_daily_lc_vw.requirement_vw`
"""

def refresh_table():
    """Replace the destination FEDE requirement table."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting refresh of fede_daily_requirementvw...")
    client = get_client()
    job = client.query(QUERY)
    job.result()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Table fede_daily_requirementvw refreshed successfully!")

if __name__ == "__main__":
    refresh_table()
