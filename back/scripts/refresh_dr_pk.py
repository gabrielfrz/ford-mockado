"""Refresh the local FEDE primary-key table from its source BigQuery view."""

import sys
import os

# Make project modules importable when the script is run directly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.bigquery_client import get_client
from datetime import datetime

# Source: pk_vw; destination: fede_daily_pkvw.
QUERY = """
CREATE OR REPLACE TABLE `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.fede_daily_pkvw` AS
SELECT * FROM `prj-dfad-1242-uapd-p-1242.bq_707_fedve_daily_lc_vw.pk_vw`
"""

def refresh_table():
    """Replace the destination FEDE primary-key table."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting refresh of fede_daily_pkvw table...")
    
    client = get_client()
    
    job = client.query(QUERY)
    print(f"  Job ID: {job.job_id}")
    print("  Waiting for completion...")
    
    job.result()  
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Table refreshed successfully!")
    print(f"  Destination: ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.fede_daily_pkvw")

if __name__ == "__main__":
    refresh_table()
