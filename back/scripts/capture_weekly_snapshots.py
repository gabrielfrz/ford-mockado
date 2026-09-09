import os
import sys
from google.cloud import bigquery
from datetime import datetime

# Adjust path to import app services if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.bigquery_client import get_client

def create_tables_if_not_exist(client: bigquery.Client, project: str):
    dpa5_ddl = f"""
        CREATE TABLE IF NOT EXISTS `{project}.DANDR_DEV.dpa5_weekly_snapshot` (
            snapshot_date DATE,
            cpsc STRING,
            lead_pmt STRING,
            program STRING,
            k_pac_id STRING,
            total_issues INT64,
            mfg_functional_area STRING,
            total_green_compliant INT64,
            total_red_not_compliant INT64,
            total_blue_cannot_assess INT64,
            total_na_not_applicable INT64,
            total_non_scorable INT64,
            total_not_evaluated INT64
        )
        PARTITION BY snapshot_date
    """
    
    dvp_ddl = f"""
        CREATE TABLE IF NOT EXISTS `{project}.DANDR_DEV.dvp_weekly_snapshot` (
            snapshot_date DATE,
            gi_code STRING,
            pmt_code STRING,
            model_year STRING,
            milestone_code STRING,
            meet INT64,
            does_not_meet INT64,
            unassessed INT64,
            total INT64
        )
        PARTITION BY snapshot_date
    """
    
    client.query(dpa5_ddl).result()
    client.query(dvp_ddl).result()
    print("Tabelas de snapshot garantidas no BQ.")


def capture_snapshots():
    client = get_client()
    project = client.project
    
    create_tables_if_not_exist(client, project)
    
    today = datetime.utcnow().date().isoformat()
    
    # --- DPA5 Snapshot ---
    dpa5_insert = f"""
        INSERT INTO `{project}.DANDR_DEV.dpa5_weekly_snapshot`
        WITH unnested_issues AS (
            SELECT
            dashboard_id,
            cpsc,
            lead_pmt,
            program,
            mfg_functional_area,
            COALESCE(SAFE_CAST(blue___cannot_assess   AS INT64), 0) AS blue_cannot_assess,
            COALESCE(SAFE_CAST(green___compliant       AS INT64), 0) AS green_compliant,
            COALESCE(SAFE_CAST(na___not_applicable     AS INT64), 0) AS na_not_applicable,
            COALESCE(SAFE_CAST(non_scorable            AS INT64), 0) AS non_scorable,
            COALESCE(SAFE_CAST(not_evaluated           AS INT64), 0) AS not_evaluated,
            COALESCE(SAFE_CAST(red___not_compliant     AS INT64), 0) AS red_not_compliant,
            TRIM(k_pac_single) AS k_pac_id
            FROM `prj-dfad-1242-uapd-p-1242.bq_666_dpa5_lc_vw.dpa5_issue_list_field_raw_vw`,
            UNNEST(SPLIT(REGEXP_REPLACE(k_pac_id, r'[\\r\\n]+', ','), ',')) AS k_pac_single
        ),
        k_pac_aggregated AS (
            SELECT
            cpsc,
            lead_pmt,
            program,
            k_pac_id,
            COUNT(DISTINCT dashboard_id)                  AS total_issues,
            MAX(mfg_functional_area)                      AS mfg_functional_area,
            SUM(green_compliant)                          AS total_green_compliant,
            SUM(red_not_compliant)                        AS total_red_not_compliant,
            SUM(blue_cannot_assess)                       AS total_blue_cannot_assess,
            SUM(na_not_applicable)                        AS total_na_not_applicable,
            SUM(non_scorable)                             AS total_non_scorable,
            SUM(not_evaluated)                            AS total_not_evaluated
            FROM unnested_issues
            WHERE k_pac_id IS NOT NULL AND k_pac_id != ''
            GROUP BY cpsc, lead_pmt, program, k_pac_id
        )
        SELECT 
            DATE('{today}') AS snapshot_date,
            *
        FROM k_pac_aggregated
    """
    
    # --- DVP Snapshot ---
    dvp_insert = f"""
        INSERT INTO `{project}.DANDR_DEV.dvp_weekly_snapshot`
        WITH base_dvp AS (
            SELECT
            gi_code,
            pmt_code,                                             
            REGEXP_EXTRACT(program, r'^(\\d{{4}})') AS model_year,
            TRIM(recommended_milestone) AS milestone_code,
            LOWER(TRIM(conformance_state)) AS conformance_state
            FROM `{project}.DANDR_DEV.dvp_fede`
        ),
        dvp_aggregated AS (
            SELECT
            gi_code,
            pmt_code,                                                
            model_year,
            milestone_code,
            COUNTIF(conformance_state = 'meet') AS meet,
            COUNTIF(conformance_state = 'does not meet') AS does_not_meet,
            COUNTIF(conformance_state = 'unassessed') AS unassessed,
            COUNT(*) AS total
            FROM base_dvp
            GROUP BY gi_code, pmt_code, model_year, milestone_code
        )
        SELECT
            DATE('{today}') AS snapshot_date,
            *
        FROM dvp_aggregated
    """
    
    try:
        print("Iniciando DPA5 Snapshot...")
        client.query(dpa5_insert).result()
        print("DPA5 Snapshot finalizado com sucesso.")
        
        print("Iniciando DVP Snapshot...")
        client.query(dvp_insert).result()
        print("DVP Snapshot finalizado com sucesso.")
        
    except Exception as e:
        print(f"Erro ao capturar snapshot: {e}")

if __name__ == '__main__':
    capture_snapshots()
