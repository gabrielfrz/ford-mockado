"""
Script to refresh the vehicle_line table in BigQuery.
Merges vpp001_glb_integrator_prj_vw and vpp005_prj_timing_pivot_vw
into ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.vehicle_line.

Also detects schema changes (added, removed or renamed columns) comparing
the schema before and after the refresh, logging a clear diff report.

Usage:
    python scripts/refresh_vehicle_line.py
"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.bigquery_client import get_client
from datetime import datetime

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

QUERY = """
CREATE OR REPLACE TABLE `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.vehicle_line` AS

SELECT
    -- Columns merged from both source views
  COALESCE(b1.vpp001_gi_prj_id,          b2.vpp001_gi_prj_id)          AS vpp001_gi_prj_id,
  COALESCE(b1.vpp001_gi_prj_ds,          b2.vpp001_gi_prj_ds)          AS vpp001_gi_prj_ds,
  COALESCE(b1.vpp001_engnrng_ptvl_ds,    b2.vpp001_engnrng_ptvl_ds)    AS vpp001_engnrng_ptvl_ds,
  COALESCE(b1.vpp001_engnrng_ptvl_cd,    b2.vpp001_engnrng_ptvl_cd)    AS vpp001_engnrng_ptvl_cd,
  COALESCE(b1.vpp001_gi_prod_pgm_nm,     b2.vpp001_gi_prod_pgm_nm)     AS vpp001_gi_prod_pgm_nm,
  COALESCE(b1.vpp001_veh_mdl_yr,         b2.vpp001_veh_mdl_yr)         AS vpp001_veh_mdl_yr,
  COALESCE(b1.vpp001_prj_eff_in_pnt_cd,  b2.vpp001_prj_eff_in_pnt_cd)  AS vpp001_prj_eff_in_pnt_cd,
  COALESCE(b1.vpp001_veh_nm_plte_nm,     b2.vpp001_veh_nm_plte_nm)     AS vpp001_veh_nm_plte_nm,

    -- Column available only in the 001 source
  b1.vpp001_cyc_pln_job_1_dt AS vpp001_cyc_pln_job_1_dt,

    -- Plant metadata resolved through effectiveIn
  b12.plantCode       AS plant_code,
  b12.plantName       AS plant_name,
  b21.vpp021_wers_plant AS wers_plant,

    -- Remaining non-duplicate columns from the 005 source
  b2.* EXCEPT (
    vpp001_gi_prj_id,
    vpp001_gi_prj_ds,
    vpp001_engnrng_ptvl_ds,
    vpp001_engnrng_ptvl_cd,
    vpp001_gi_prod_pgm_nm,
    vpp001_veh_mdl_yr,
    vpp001_prj_eff_in_pnt_cd,
    vpp001_veh_nm_plte_nm,
    vpp001_cyc_pln_job_1_dt
  )

FROM `prj-dfad-1242-uapd-p-1242.bq_vpp_secret_fdp_dwc_vw.vpp001_glb_integrator_prj_vw` b1
FULL OUTER JOIN `prj-dfad-1242-uapd-p-1242.bq_vpp_secret_fdp_dwc_vw.vpp005_prj_timing_pivot_vw` b2
  ON b1.vpp001_gi_prj_id = b2.vpp001_gi_prj_id

-- Plant code via effectiveIn → vpp012
LEFT JOIN (
  SELECT DISTINCT effectiveIn, plantCode, plantName
  FROM `prj-dfad-1242-uapd-p-1242.bq_vpp_secret_fdp_dwc_vw.vpp012_fedebom_decoder_vw`
) b12
  ON COALESCE(b1.vpp001_prj_eff_in_pnt_cd, b2.vpp001_prj_eff_in_pnt_cd) = b12.effectiveIn

-- WERS plant via effectiveIn → vpp021
LEFT JOIN (
  SELECT DISTINCT vpp021_eff_in, vpp021_wers_plant
  FROM `prj-dfad-1242-uapd-p-1242.bq_vpp_secret_fdp_dwc_vw.vpp021_wers_vpid_decoder_vw`
) b21
  ON COALESCE(b1.vpp001_prj_eff_in_pnt_cd, b2.vpp001_prj_eff_in_pnt_cd) = b21.vpp021_eff_in
"""

TABLE_REF = "ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.vehicle_line"


def get_schema(client) -> dict[str, str]:
    """Return the vehicle-line schema, or an empty mapping if absent."""
    try:
        table = client.get_table(TABLE_REF)
        return {field.name: field.field_type for field in table.schema}
    except Exception:
        return {}


def log_schema_diff(before: dict[str, str], after: dict[str, str]) -> bool:
    """Log schema differences and report whether any change occurred."""
    added   = {k: v for k, v in after.items()  if k not in before}
    removed = {k: v for k, v in before.items() if k not in after}
    changed = {
        k: {"before": before[k], "after": after[k]}
        for k in after
        if k in before and before[k] != after[k]
    }

    if not added and not removed and not changed:
        logger.info("  Schema: no changes detected ✅")
        return False

    logger.warning("  ⚠️  SCHEMA CHANGES DETECTED:")

    if added:
        logger.warning(f"  ➕ ADDED columns ({len(added)}):")
        for col, dtype in sorted(added.items()):
            logger.warning(f"       + {col}  [{dtype}]")

    if removed:
        logger.warning(f"  ➖ REMOVED columns ({len(removed)}):")
        for col, dtype in sorted(removed.items()):
            logger.warning(f"       - {col}  [{dtype}]")

    if changed:
        logger.warning(f"  🔄 TYPE CHANGED columns ({len(changed)}):")
        for col, diff in sorted(changed.items()):
            logger.warning(f"       ~ {col}:  {diff['before']} → {diff['after']}")

    return True


def refresh_table():
    """Refresh the vehicle-line table and report schema changes."""
    logger.info(f"Starting refresh of vehicle_line table...")

    client = get_client()

    # Capture the schema before refreshing.
    schema_before = get_schema(client)
    if schema_before:
        logger.info(f"  Schema before: {len(schema_before)} columns")
    else:
        logger.info("  Table does not exist yet — will be created from scratch.")

    # Replace the destination table.
    job = client.query(QUERY)
    logger.info(f"  Job ID: {job.job_id}")
    logger.info("  Waiting for completion...")
    job.result()

    # Capture the schema after refreshing.
    schema_after = get_schema(client)
    logger.info(f"  Schema after:  {len(schema_after)} columns")

    # ── Diff ─────────────────────────────────────────────────────────────────
    log_schema_diff(schema_before, schema_after)

    logger.info(f"vehicle_line table refreshed successfully!")
    logger.info(f"  Destination: {TABLE_REF}")


if __name__ == "__main__":
    refresh_table()
