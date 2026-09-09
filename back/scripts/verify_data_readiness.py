"""Validate that all BigQuery tables required by a deployment are populated and fresh.

Usage:
    python scripts/verify_data_readiness.py
    python scripts/verify_data_readiness.py --max-age-hours 24
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

# Make project modules importable when the script is run directly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.bigquery_client import PROJECT_ID, get_client

DATASET_ID = "DANDR_DEV"
DESTINATION_TABLES = (
    "vehicle_line",
    "fede_daily_fedestatus",
    "fede_daily_assessmentvw",
    "dr_design_rule",
    "dr_mapping",
    "fede_daily_pkvw",
    "drassesmentvw",
    "fede_daily_requirementvw",
)

logger = logging.getLogger(__name__)


def validate_data_readiness(max_age_hours: float = 24.0) -> list[str]:
    """Return validation errors for missing, empty, or stale destination tables."""
    if max_age_hours <= 0:
        raise ValueError("max_age_hours must be greater than zero")

    client = get_client()
    now = datetime.now(timezone.utc)
    errors: list[str] = []

    for table_name in DESTINATION_TABLES:
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        try:
            table = client.get_table(table_id)
        except Exception as exc:
            message = f"{table_name}: could not read metadata: {exc}"
            logger.error(message)
            errors.append(message)
            continue

        modified = table.modified
        age_hours = (now - modified).total_seconds() / 3600 if modified else float("inf")
        logger.info(
            "%s: rows=%s, modified=%s, age_hours=%.2f",
            table_name,
            table.num_rows,
            modified.isoformat() if modified else "unknown",
            age_hours,
        )

        if table.num_rows <= 0:
            errors.append(f"{table_name}: table is empty")
        if age_hours > max_age_hours:
            errors.append(
                f"{table_name}: stale ({age_hours:.2f}h old; maximum is {max_age_hours:.2f}h)"
            )

    return errors


def main() -> int:
    """Validate destination tables and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=24.0,
        help="Maximum accepted table age in hours (default: 24)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    errors = validate_data_readiness(args.max_age_hours)
    if errors:
        logger.error("DATA READINESS: FAILED (%d issue(s))", len(errors))
        for error in errors:
            logger.error("  - %s", error)
        return 1

    logger.info("DATA READINESS: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
