"""Aggregate milestone readiness across DVP, CAE, and Design Rules."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import pandas as pd
from google.cloud import bigquery
from app.services.bigquery_client import get_client

# Valid milestone column names from the vehicle_line table
VALID_MILESTONES = [
    "mr", "ps", "psc", "fpd", "fc1", "fc2", "fc3", "fc4", "fc5",
    "k3", "k5", "upv0", "upv1", "upv2", "pa", "fdj", "dcv", "pec", "fec",
    "lr", "ls", "j1", "oktb", "fsr", "faa", "ept", "ept_ipd", "tt_ipd", "tt",
    "pp", "mp1", "mp2", "_pcf1", "_tcb1", "_tcb2", "tmr", "tps", "tsc", "tdc",
    "ttc", "tdj", "tpv", "unv0", "unv1", "unv2", "xm", "aa1", "vp", "_dtm",
]

# Completion statuses for DVP / CAE assessments
_COMPLETED_STATES = ("pass", "meet", "approved deviation")


def _pmt_predicate(column_expression: str) -> str:
    """Match canonical PMT codes and source-specific numeric prefixes."""
    extracted_value = (
        f"SAFE_CAST(REGEXP_EXTRACT(CAST({column_expression} AS STRING), r'\\d+') AS INT64)"
    )
    extracted_parameter = "SAFE_CAST(REGEXP_EXTRACT(@pmt_code, r'\\d+') AS INT64)"
    return (
        f"{extracted_value} IN "
        f"({extracted_parameter}, DIV({extracted_parameter}, 100))"
    )


def _row_pmt_expression(row_alias: str) -> str:
    """Resolve PMT values from source views with different field names."""
    return f"""COALESCE(
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.pmt_code'),
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.pmt'),
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.lead_pmt'),
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.pmt_id')
    )"""


def _compute_status(percentage: float) -> str:
    """Map a readiness percentage to its dashboard traffic-light status."""
    if percentage >= 100.0:
        return "Green"
    elif percentage >= 80.0:
        return "Yellow"
    return "Red"


def _build_metric(source: str, target: int, actual: int) -> dict:
    """Build a normalized readiness metric for one deliverable source."""
    percentage = round((actual / target * 100), 2) if target > 0 else 0.0
    return {
        "source": source,
        "target": target,
        "actual": actual,
        "percentage": percentage,
        "status": _compute_status(percentage),
    }


# ---------------------------------------------------------------------------
# Step 1 – Fetch program name + milestone date from vehicle_line
# ---------------------------------------------------------------------------

def _get_milestone_info(gi_code: str, milestone: str) -> Optional[dict]:
    """
    Queries vehicle_line to retrieve the program name and the date stored in
    the milestone column (e.g. 'mr', 'ps') for the given gi_code.

    The milestone column name is validated against VALID_MILESTONES before
    being interpolated into SQL, preventing any injection risk.
    """
    client = get_client()
    sql = f"""
        SELECT
            vpp001_gi_prod_pgm_ds AS program_name,
            SAFE_CAST({milestone} AS DATE) AS milestone_date
        FROM `{client.project}.DANDR_DEV.vehicle_line`
        WHERE vpp001_gi_prj_id = @gi_code
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code),
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    if df.empty:
        return None
    row = df.iloc[0]
    return {
        "program": str(row["program_name"]) if pd.notna(row["program_name"]) else None,
        "milestone_date": str(row["milestone_date"]) if pd.notna(row["milestone_date"]) else None,
    }


# ---------------------------------------------------------------------------
# Step 2 – Individual readiness queries (run in parallel)
# ---------------------------------------------------------------------------

def _get_dvp_readiness(
    gi_code: str,
    milestone_date: str,
    pmt_code: str | None = None,
) -> dict:
    """
    DVP readiness: non-CAE records in dvp_fede whose milestone_date falls on
    or before the selected milestone date.

    Target  = total items due by this milestone.
    Actual  = items with a completion status (pass / meet / approved deviation).
    """
    client = get_client()
    pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
    sql = f"""
        SELECT
            COUNT(*) AS target,
            COUNTIF(
                LOWER(TRIM(conformance_state)) IN ({", ".join(f"'{s}'" for s in _COMPLETED_STATES)})
            ) AS actual
        FROM `{client.project}.DANDR_DEV.dvp_fede`
        WHERE
            gi_code = @gi_code
            {pmt_filter}
            AND NOT REGEXP_CONTAINS(UPPER(COALESCE(CAST(prototype_type AS STRING), '')), r'CAE')
            AND conformance_state IS NOT NULL
            AND TRIM(CAST(conformance_state AS STRING)) != ''
            AND SAFE_CAST(milestone_date AS DATE) <= @milestone_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code),
            bigquery.ScalarQueryParameter("milestone_date", "DATE", milestone_date),
            *(
                [bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code)]
                if pmt_code
                else []
            ),
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    target = int(df.iloc[0]["target"]) if not df.empty else 0
    actual = int(df.iloc[0]["actual"]) if not df.empty else 0
    return _build_metric("DVP", target, actual)


def _get_cae_readiness(
    gi_code: str,
    milestone_date: str,
    pmt_code: str | None = None,
) -> dict:
    """
    CAE readiness: records where prototype_type contains 'CAE' in dvp_fede,
    filtered by milestone_date <= selected milestone date.

    Target  = total CAE items due by this milestone.
    Actual  = items with a completion status (pass / meet / approved deviation).
    """
    client = get_client()
    pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
    sql = f"""
        SELECT
            COUNT(*) AS target,
            COUNTIF(
                LOWER(TRIM(conformance_state)) IN ({", ".join(f"'{s}'" for s in _COMPLETED_STATES)})
            ) AS actual
        FROM `{client.project}.DANDR_DEV.dvp_fede`
        WHERE
            gi_code = @gi_code
            {pmt_filter}
            AND REGEXP_CONTAINS(UPPER(COALESCE(CAST(prototype_type AS STRING), '')), r'CAE')
            AND conformance_state IS NOT NULL
            AND TRIM(CAST(conformance_state AS STRING)) != ''
            AND SAFE_CAST(milestone_date AS DATE) <= @milestone_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code),
            bigquery.ScalarQueryParameter("milestone_date", "DATE", milestone_date),
            *(
                [bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code)]
                if pmt_code
                else []
            ),
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    target = int(df.iloc[0]["target"]) if not df.empty else 0
    actual = int(df.iloc[0]["actual"]) if not df.empty else 0
    return _build_metric("CAE", target, actual)


def _get_design_rules_readiness(
    gi_code: str,
    milestone_date: str,
    pmt_code: str | None = None,
) -> dict:
    """
    Design Rules readiness: from dr_design_rule table.

    The table has no date column, so the milestone_date argument is not used
    for filtering – the metric reflects the overall classification status.

    Target  = rules classified as 'Applicable' (must be validated).
    Actual  = rules classified as 'Carryover' or 'Previously Validated'
              (already confirmed / carried over from prior program).
    """
    client = get_client()

    # Look up model_year and program_name from vehicle_line — dr_design_rule has no gi_code column
    vl_df = client.query(
        f"""
        SELECT
            CAST(vpp001_veh_mdl_yr AS STRING) AS model_year,
            vpp001_gi_prod_pgm_ds AS program_name
        FROM `{client.project}.DANDR_DEV.vehicle_line`
        WHERE vpp001_gi_prj_id = @gi_code
        LIMIT 1
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
        ),
    ).to_dataframe()

    if vl_df.empty:
        return _build_metric("Design Rules", 0, 0)

    model_year = str(vl_df.iloc[0]["model_year"]).strip().split(".")[0]
    program_name = str(vl_df.iloc[0]["program_name"]).strip()
    # Normalize: spaces → underscores to handle vehicle_line vs dr_pk2 format differences
    program_name_normalized = program_name.replace(" ", "_")
    dr_pk2_prefix = f"{model_year}_{program_name_normalized}"
    pmt_filter = (
        f"AND {_pmt_predicate(_row_pmt_expression('design_rule'))}"
        if pmt_code
        else ""
    )

    sql = f"""
        SELECT
            COUNTIF(classified IN ('Applicable', 'Carryover', 'Previously Validated')) AS target,
            COUNTIF(classified IN ('Carryover', 'Previously Validated')) AS actual
                FROM `{client.project}.DANDR_DEV.dr_design_rule` AS design_rule
        WHERE STARTS_WITH(LOWER(REPLACE(dr_pk2, ' ', '_')), LOWER(@dr_pk2_prefix))
                    {pmt_filter}
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("dr_pk2_prefix", "STRING", dr_pk2_prefix),
            *(
                [bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code)]
                if pmt_code
                else []
            ),
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    target = int(df.iloc[0]["target"]) if not df.empty else 0
    actual = int(df.iloc[0]["actual"]) if not df.empty else 0
    return _build_metric("Design Rules", target, actual)


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

_SOURCE_FUNCS = {
    "DVP": _get_dvp_readiness,
    "CAE": _get_cae_readiness,
    "Design Rules": _get_design_rules_readiness,
}


def get_milestone_readiness(
    gi_code: str,
    milestone: str,
    pmt_code: str | None = None,
) -> dict:
    """
    Calculates the Milestone Readiness for a given gi_code and milestone.

    Steps:
    1. Validates the milestone name against the whitelist.
    2. Fetches program name and milestone_date from vehicle_line.
    3. Fires parallel BigQuery queries for DVP, CAE, and Design Rules.
    4. Returns aggregated JSON with per-source target/actual/percentage/status.
    """
    if milestone not in VALID_MILESTONES:
        raise ValueError(
            f"Milestone '{milestone}' is invalid. "
            f"Accepted values: {', '.join(VALID_MILESTONES)}"
        )

    info = _get_milestone_info(gi_code, milestone)
    if info is None:
        raise ValueError(
            f"GI code '{gi_code}' was not found in the vehicle_line table."
        )
    if not info.get("milestone_date"):
        raise ValueError(
            f"Milestone '{milestone}' has no date defined "
            f"for GI code '{gi_code}'."
        )

    milestone_date: str = info["milestone_date"]
    program: Optional[str] = info["program"]

    # Parallel execution of the three source queries
    metrics: dict[str, dict] = {}
    errors: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fn, gi_code, milestone_date, pmt_code): source
            for source, fn in _SOURCE_FUNCS.items()
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                metrics[source] = future.result()
            except Exception as exc:
                errors[source] = str(exc)
                metrics[source] = _build_metric(source, 0, 0)
                metrics[source]["error"] = str(exc)

    ordered_metrics = [
        metrics.get("DVP", _build_metric("DVP", 0, 0)),
        metrics.get("CAE", _build_metric("CAE", 0, 0)),
        metrics.get("Design Rules", _build_metric("Design Rules", 0, 0)),
    ]

    response = {
        "gi_code": gi_code,
        "program": program,
        "milestone": milestone,
        "milestone_date": milestone_date,
        "pmt_code": pmt_code,
        "metrics": ordered_metrics,
    }
    if errors:
        response["errors"] = errors

    return response
