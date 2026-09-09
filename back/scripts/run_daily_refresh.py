"""Run all BigQuery refresh jobs sequentially.

In cloud environments this module runs as a Cloud Run Job triggered by Cloud
Scheduler. For local execution, use:

    python scripts/run_daily_refresh.py

Log output:
    logs/daily_refresh_YYYY-MM-DD.log
"""

import sys
import os
import logging
from datetime import datetime

# Make project modules importable when the script is run directly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Logging configuration
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_filename = os.path.join(LOG_DIR, f"daily_refresh_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Refresh job imports
from scripts.refresh_fede_daily_status import refresh_table as refresh_fede
from scripts.refresh_vehicle_line import refresh_table as refresh_vehicle_line
from scripts.refresh_assessment import refresh_table as refresh_assessment
from scripts.refresh_dr_design_rule import refresh_table as refresh_dr_design_rule
from scripts.refresh_dr_mapping import refresh_table as refresh_dr_mapping
from scripts.refresh_dr_pk import refresh_table as refresh_dr_pk
from scripts.refresh_drassesmentvw import refresh_table as refresh_drassesmentvw
from scripts.refresh_requirementvw import refresh_table as refresh_requirementvw
from scripts.verify_data_readiness import validate_data_readiness

# Ordered refresh jobs
JOBS = [
    ("vehicle_line",          refresh_vehicle_line),
    ("fede_daily_fedestatus", refresh_fede),
    ("assessment",            refresh_assessment),
    ("dr_design_rule",        refresh_dr_design_rule),
    ("dr_mapping",            refresh_dr_mapping),
    ("dr_pk",                 refresh_dr_pk),
    ("drassesmentvw",         refresh_drassesmentvw),
    ("requirementvw",         refresh_requirementvw),
]

def main():
    """Run refresh jobs, validate data readiness, and set the exit status."""
    logger.info("=" * 60)
    logger.info("DANDR Daily Refresh — START")
    logger.info("=" * 60)

    results = {}

    for name, fn in JOBS:
        logger.info(f"▶ Running: {name}")
        try:
            fn()
            results[name] = "SUCCESS"
            logger.info(f"{name} — completed successfully")
        except Exception as e:
            results[name] = f"FAILED: {e}"
            logger.error(f"{name} — FAILED: {e}", exc_info=True)

    logger.info("=" * 60)
    logger.info("SUMMARY:")
    for name, status in results.items():
        logger.info(f"  {name}: {status}")
    logger.info("=" * 60)
    logger.info("DANDR Daily Refresh — END")

    refresh_failed = any("FAILED" in status for status in results.values())
    readiness_errors = []
    if not refresh_failed:
        logger.info("Validating post-refresh data readiness...")
        readiness_errors = validate_data_readiness(max_age_hours=24)
        if readiness_errors:
            for error in readiness_errors:
                logger.error("Data readiness — %s", error)
        else:
            logger.info("Data readiness — PASSED")

    # Exit with failure when a refresh or post-refresh validation fails.
    if refresh_failed or readiness_errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
