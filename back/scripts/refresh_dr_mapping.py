"""Refresh the local Design Rule mapping table from BigQuery."""

import sys
import os

# Make project modules importable when the script is run directly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.bigquery_client import get_client
from datetime import datetime

QUERY = """
CREATE OR REPLACE TABLE `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.dr_mapping` AS
SELECT * FROM `prj-dfad-1242-uapd-p-1242.bq_707_fedve_daily_lc_vw.dr_mapping_vw`
"""

def refresh_table():
    """Replace the destination Design Rule mapping table."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting refresh of dr_mapping table...")
    
    client = get_client()
    
    job = client.query(QUERY)
    print(f"  Job ID: {job.job_id}")
    print("  Waiting for completion...")
    
    job.result() 
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Table refreshed successfully!")
    print(f"  Destination: ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.dr_mapping")

if __name__ == "__main__":
    refresh_table()
