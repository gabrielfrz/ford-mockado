"""Build DVP glidepath timelines and available filter values from BigQuery."""

import re

import pandas as pd
from google.cloud import bigquery
from app.services.bigquery_client import get_client
from typing import Optional


def _pmt_predicate(column_expression: str, parameter_name: str = "pmt") -> str:
    """Match canonical PMT codes and source-specific numeric prefixes."""
    extracted_value = (
        f"SAFE_CAST(REGEXP_EXTRACT(CAST({column_expression} AS STRING), r'\\d+') AS INT64)"
    )
    extracted_parameter = (
        f"SAFE_CAST(REGEXP_EXTRACT(@{parameter_name}, r'\\d+') AS INT64)"
    )
    return (
        f"{extracted_value} IN "
        f"({extracted_parameter}, DIV({extracted_parameter}, 100))"
    )


def _canonical_pmt_code(value: object) -> str | None:
    """Normalize a source PMT value to its canonical three-digit code."""
    match = re.search(r"\d+", str(value))
    if not match:
        return None
    numeric_value = int(match.group())
    if 1 <= numeric_value <= 6:
        numeric_value *= 100
    return str(numeric_value)


def get_dvp_glidepath_data(
    gi_code: str,
    pmt: Optional[str] = None,
    milestone: Optional[str] = None,
    snapshot_date: Optional[str] = None
) -> dict:
    """Return DVP glidepath data for a GI code and optional filters."""
    try:
        client = get_client()

        where_conditions = ["gi_code = @gi_code"]
        query_params = [
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]

        if pmt:
            where_conditions.append(_pmt_predicate("pmt_code"))
            query_params.append(
                bigquery.ScalarQueryParameter("pmt", "STRING", pmt)
            )

        if milestone:
            where_conditions.append("SAFE_CAST(milestone_date AS DATE) = @milestone")
            query_params.append(
                bigquery.ScalarQueryParameter("milestone", "DATE", milestone)
            )
        
        if snapshot_date:
            where_conditions.append("snapshot_date = @snapshot_date")
            query_params.append(
                bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date)
            )
            table_name = f"`{client.project}.DANDR_DEV.dvp_weekly_snapshot`"
        else:
            table_name = f"`{client.project}.DANDR_DEV.dvp_fede`"
        
        where_clause = " AND ".join(where_conditions)
        
        sql = f'''
            WITH base_dvp AS (
              SELECT
                gi_code,
                pmt_code,                                             
                REGEXP_EXTRACT(program, r'^(\\d{{4}})') AS model_year,
                TRIM(recommended_milestone) AS milestone_code,
                SAFE_CAST(milestone_date AS DATE) AS milestone,
                SAFE_CAST(milestone_fede AS DATE) AS milestone_fede,
                SAFE_CAST(glidepath_start_date AS DATE) AS glidepath_start,
                SAFE_CAST(glideapth_end_date AS DATE) AS glidepath_end,
                SAFE_CAST(sched_finish AS DATE) AS scheduled_finished,
                SAFE_CAST(actual_end_date AS DATE) AS actual_finished,
                LOWER(TRIM(conformance_state)) AS conformance_state
              FROM {table_name}
              WHERE {where_clause}
            )
            SELECT
              gi_code,
              pmt_code,
              model_year,
              milestone_code,
              milestone,
              milestone_fede,
              glidepath_start,
              glidepath_end,
              scheduled_finished,
              actual_finished,
              conformance_state
            FROM base_dvp
            ORDER BY
              pmt_code,
              scheduled_finished;
        '''
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        if df.empty:
            return {
                "gi_code": gi_code,
                "pmt": pmt,
                "milestone": milestone,
                "data": [],
                "total_records": 0
            }

        records = []
        for _, row in df.iterrows():
            c_state = str(row.get("conformance_state", ""))
            records.append({
                "gi_code": str(row["gi_code"]) if pd.notna(row["gi_code"]) else None,
                "pmt_code": str(row["pmt_code"]) if pd.notna(row["pmt_code"]) else None,
                "model_year": str(row["model_year"]) if pd.notna(row["model_year"]) else None,
                "milestone_code": str(row["milestone_code"]) if pd.notna(row["milestone_code"]) else None,
                "milestone": str(row["milestone"]) if pd.notna(row["milestone"]) else None,
                "milestone_fede": str(row["milestone_fede"]) if pd.notna(row["milestone_fede"]) else None,
                "glidepath_start": str(row["glidepath_start"]) if pd.notna(row["glidepath_start"]) else None,
                "glidepath_end": str(row["glidepath_end"]) if pd.notna(row["glidepath_end"]) else None,
                "scheduled_finished": str(row["scheduled_finished"]) if pd.notna(row["scheduled_finished"]) else None,
                "actual_finished": str(row["actual_finished"]) if pd.notna(row["actual_finished"]) else None,
                "metrics": {
                    "meet": 1 if c_state == 'meet' else 0,
                    "does_not_meet": 1 if c_state == 'does not meet' else 0,
                    "unassessed": 1 if c_state == 'unassessed' else 0,
                    "total": 1
                }
            })
        
        return {
            "gi_code": gi_code,
            "pmt": pmt,
            "milestone": milestone,
            "data": records,
            "total_records": len(records)
        }
        
    except Exception as e:
        print(f"Erro ao buscar dados de DVP Glidepath: {str(e)}")
        raise Exception(f"Erro ao buscar dados de DVP Glidepath: {str(e)}")


def get_dvp_glidepath_aggregated_data(
    gi_code: str,
    pmt: Optional[str] = None,
    milestone: Optional[str] = None,
    snapshot_date: Optional[str] = None
) -> dict:
    """
    Retorna os dados AGREGADOS de DVP Glidepath para exportação em Excel.
    Agrupa por pmt, model_year e milestone_code e consolida as datas com MIN/MAX e status com COUNT.
    """
    try:
        client = get_client()

        where_conditions = ["gi_code = @gi_code"]
        query_params = [
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]

        if pmt:
            where_conditions.append("pmt_code = @pmt")
            query_params.append(
                bigquery.ScalarQueryParameter("pmt", "STRING", pmt)
            )

        if milestone:
            where_conditions.append("SAFE_CAST(milestone_date AS DATE) = @milestone")
            query_params.append(
                bigquery.ScalarQueryParameter("milestone", "DATE", milestone)
            )
        
        if snapshot_date:
            where_conditions.append("snapshot_date = @snapshot_date")
            query_params.append(
                bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date)
            )
            table_name = f"`{client.project}.DANDR_DEV.dvp_weekly_snapshot`"
        else:
            table_name = f"`{client.project}.DANDR_DEV.dvp_fede`"
            
        where_clause = " AND ".join(where_conditions)
        
        sql = f'''
            WITH base_dvp AS (
              SELECT
                gi_code,
                pmt_code,                                             
                REGEXP_EXTRACT(program, r'^(\\d{{4}})') AS model_year,
                TRIM(recommended_milestone) AS milestone_code,
                SAFE_CAST(milestone_date AS DATE) AS milestone,
                SAFE_CAST(milestone_fede AS DATE) AS milestone_fede,
                SAFE_CAST(glidepath_start_date AS DATE) AS glidepath_start,
                SAFE_CAST(glideapth_end_date AS DATE) AS glidepath_end,
                SAFE_CAST(sched_finish AS DATE) AS scheduled_finished,
                SAFE_CAST(actual_end_date AS DATE) AS actual_finished,
                LOWER(TRIM(conformance_state)) AS conformance_state
              FROM {table_name}
              WHERE {where_clause}
            )
            SELECT
              gi_code,
              pmt_code,                                                
              model_year,
              milestone_code,
              MIN(milestone)       AS milestone,
              MIN(milestone_fede)  AS milestone_fede,
              MIN(glidepath_start) AS glidepath_start,
              MIN(glidepath_end)   AS glidepath_end,
              MIN(scheduled_finished) AS scheduled_finished_min,
              MAX(scheduled_finished) AS scheduled_finished_max,
              MIN(actual_finished)    AS actual_finished_min,
              MAX(actual_finished)    AS actual_finished_max,
              COUNTIF(conformance_state = 'meet') AS meet,
              COUNTIF(conformance_state = 'does not meet') AS does_not_meet,
              COUNTIF(conformance_state = 'unassessed') AS unassessed,
              COUNT(*) AS total
            FROM base_dvp
            GROUP BY
              gi_code,
              pmt_code,
              model_year,
              milestone_code
            ORDER BY
              pmt_code,
              gi_code,
              model_year,
              milestone_code;
        '''
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        if df.empty:
            return {
                "gi_code": gi_code,
                "pmt": pmt,
                "milestone": milestone,
                "data": [],
                "total_records": 0
            }

        records = []
        for _, row in df.iterrows():
            records.append({
                "gi_code": str(row["gi_code"]) if pd.notna(row["gi_code"]) else None,
                "pmt_code": str(row["pmt_code"]) if pd.notna(row["pmt_code"]) else None,
                "model_year": str(row["model_year"]) if pd.notna(row["model_year"]) else None,
                "milestone_code": str(row["milestone_code"]) if pd.notna(row["milestone_code"]) else None,
                "milestone": str(row["milestone"]) if pd.notna(row["milestone"]) else None,
                "milestone_fede": str(row["milestone_fede"]) if pd.notna(row["milestone_fede"]) else None,
                "glidepath_start": str(row["glidepath_start"]) if pd.notna(row["glidepath_start"]) else None,
                "glidepath_end": str(row["glidepath_end"]) if pd.notna(row["glidepath_end"]) else None,
                "scheduled_finished": str(row["scheduled_finished_max"]) if pd.notna(row["scheduled_finished_max"]) else None,
                "actual_finished": str(row["actual_finished_max"]) if pd.notna(row["actual_finished_max"]) else None,
                "metrics": {
                    "meet": int(row["meet"]) if pd.notna(row["meet"]) else 0,
                    "does_not_meet": int(row["does_not_meet"]) if pd.notna(row["does_not_meet"]) else 0,
                    "unassessed": int(row["unassessed"]) if pd.notna(row["unassessed"]) else 0,
                    "total": int(row["total"]) if pd.notna(row["total"]) else 0
                }
            })
        
        return {
            "gi_code": gi_code,
            "pmt": pmt,
            "milestone": milestone,
            "data": records,
            "total_records": len(records)
        }
        
    except Exception as e:
        print(f"Erro ao buscar dados agregados de DVP Glidepath: {str(e)}")
        raise Exception(f"Erro ao buscar dados agregados de DVP Glidepath: {str(e)}")


def get_available_pmts(gi_code: str) -> list[str]:
    """Return canonical PMT codes available for a GI code."""
    try:
        client = get_client()
        
        sql = f'''
            SELECT DISTINCT pmt_code
            FROM `{client.project}.DANDR_DEV.dvp_fede`
            WHERE gi_code = @gi_code
              AND pmt_code IS NOT NULL
            ORDER BY pmt_code ASC
        '''
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
            ]
        )
        
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        if df.empty:
            return []
        
        canonical_pmts = {
            canonical
            for value in df["pmt_code"].dropna().tolist()
            if (canonical := _canonical_pmt_code(value)) is not None
        }
        return sorted(canonical_pmts, key=int)
        
    except Exception as e:
        print(f"Failed to retrieve available PMTs: {str(e)}")
        return []


def get_available_milestones(gi_code: str, pmt: Optional[str] = None) -> list[str]:
    """Return milestone dates available for a GI code and optional PMT."""
    try:
        client = get_client()
        
        where_conditions = ["gi_code = @gi_code", "milestone_date IS NOT NULL"]
        query_params = [
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]
        
        if pmt:
            where_conditions.append(_pmt_predicate("pmt_code"))
            query_params.append(
                bigquery.ScalarQueryParameter("pmt", "STRING", pmt)
            )
        
        where_clause = " AND ".join(where_conditions)
        
        sql = f'''
            SELECT DISTINCT SAFE_CAST(milestone_date AS DATE) AS milestone
            FROM `{client.project}.DANDR_DEV.dvp_fede`
            WHERE {where_clause}
            ORDER BY milestone ASC
        '''
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        if df.empty:
            return []
        
        return df["milestone"].dropna().astype(str).tolist()
        
        return df["milestone"].dropna().astype(str).tolist()
        
    except Exception as e:
        print(f"Failed to retrieve available milestones: {str(e)}")
        return []

def get_dvp_snapshots(gi_code: str) -> list[str]:
    try:
        client = get_client()
        sql = f"""
            SELECT DISTINCT CAST(snapshot_date AS STRING) as snapshot_date 
            FROM `{client.project}.DANDR_DEV.dvp_weekly_snapshot` 
            ORDER BY snapshot_date DESC
        """
        df = client.query(sql).to_dataframe()
        return df['snapshot_date'].dropna().tolist()
    except Exception as e:
        print(f'Error getting dvp snapshots: {e}')
        return []
