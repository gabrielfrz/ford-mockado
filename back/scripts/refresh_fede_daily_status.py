"""
Temporary script to refresh the fede_daily_fedestatus table in BigQuery.
Executes a CREATE OR REPLACE TABLE from the source view.

Usage:
    python scripts/refresh_fede_daily_status.py
"""

import sys
import os

# Make project modules importable when the script is run directly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.bigquery_client import get_client
from datetime import datetime

QUERY = """
CREATE OR REPLACE TABLE `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.fede_daily_fedestatus` AS
SELECT * FROM `prj-dfad-1242-uapd-p-1242.bq_707_fedve_daily_lc_vw.fede_dv_status_vw`
"""

def refresh_table():
    """Replace the destination FEDE status table."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting refresh of fede_daily_fedestatus table...")
    
    client = get_client()
    
    job = client.query(QUERY)
    print(f"  Job ID: {job.job_id}")
    print("  Waiting for completion...")
    
    job.result()  # Block until the BigQuery job finishes.
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Table refreshed successfully!")
    print(f"  Destination: ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.fede_daily_fedestatus")

if __name__ == "__main__":
    refresh_table()
