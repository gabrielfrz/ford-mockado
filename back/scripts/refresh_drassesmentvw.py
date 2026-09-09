"""Refresh the local Design Rule assessment table from BigQuery."""

import sys
import os

# Make project modules importable when the script is run directly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.bigquery_client import get_client
from datetime import datetime

# Source: dr_assessment_vw; destination: drassesmentvw.
QUERY = """
CREATE OR REPLACE TABLE `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.drassesmentvw` AS
SELECT * FROM `prj-dfad-1242-uapd-p-1242.bq_707_fedve_daily_lc_vw.dr_assessment_vw`
"""

def refresh_table():
    """Replace the destination Design Rule assessment table."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting refresh of drassesmentvw table...")
    
    client = get_client()
    
    job = client.query(QUERY)
    print(f"  Job ID: {job.job_id}")
    print("  Waiting for completion...")
    
    job.result()  # Block until the BigQuery job finishes.
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Table refreshed successfully!")
    print(f"  Destination: ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.drassesmentvw")

if __name__ == "__main__":
    refresh_table()
