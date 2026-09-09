import re
import os

file_path = r"c:\Users\GARAGAO1\OneDrive - azureford\Desktop\projeto\back\app\services\dvp_glidepath_service.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update get_dvp_glidepath_data signature
content = content.replace(
    "def get_dvp_glidepath_data(\n    gi_code: str,\n    pmt: Optional[str] = None,\n    milestone: Optional[str] = None\n) -> dict:",
    "def get_dvp_glidepath_data(\n    gi_code: str,\n    pmt: Optional[str] = None,\n    milestone: Optional[str] = None,\n    snapshot_date: Optional[str] = None\n) -> dict:"
)

# 2. Update get_dvp_glidepath_aggregated_data signature
content = content.replace(
    "def get_dvp_glidepath_aggregated_data(\n    gi_code: str,\n    pmt: Optional[str] = None,\n    milestone: Optional[str] = None\n) -> dict:",
    "def get_dvp_glidepath_aggregated_data(\n    gi_code: str,\n    pmt: Optional[str] = None,\n    milestone: Optional[str] = None,\n    snapshot_date: Optional[str] = None\n) -> dict:"
)

# 3. Inject snapshot logic into get_dvp_glidepath_data
old_sql_block1 = '''        sql = f"""
            WITH base_dvp AS ('''

snapshot_sql_block1 = '''
        if snapshot_date:
            if not pmt:
                pmt_clause = ""
            else:
                pmt_clause = "AND pmt_code = @pmt"
                
            sql = f"""
                WITH base_dvp AS (
                  SELECT
                    gi_code,
                    pmt_code,
                    model_year,
                    milestone_code,
                    NULL AS milestone,
                    NULL AS milestone_fede,
                    NULL AS glidepath_start,
                    NULL AS glidepath_end,
                    NULL AS scheduled_finished,
                    NULL AS actual_finished,
                    CASE 
                      WHEN meet > 0 THEN 'meet'
                      WHEN does_not_meet > 0 THEN 'does not meet'
                      WHEN unassessed > 0 THEN 'unassessed'
                      ELSE ''
                    END AS conformance_state
                  FROM `{client.project}.DANDR_DEV.dvp_weekly_snapshot`
                  WHERE snapshot_date = SAFE_CAST('{snapshot_date}' AS DATE)
                    AND gi_code = @gi_code
                    {pmt_clause}
                )
            """
        else:
            sql = f"""
                WITH base_dvp AS ('''

content = content.replace(old_sql_block1, snapshot_sql_block1.lstrip('\n'), 1)

# 4. Inject snapshot logic into get_dvp_glidepath_aggregated_data
old_sql_block2 = '''        sql = f"""
            WITH base_dvp AS ('''

snapshot_sql_block2 = '''
        if snapshot_date:
            if not pmt:
                pmt_clause = ""
            else:
                pmt_clause = "AND pmt_code = @pmt"
                
            sql = f"""
                SELECT
                  gi_code,
                  pmt_code,
                  model_year,
                  milestone_code,
                  NULL AS milestone,
                  NULL AS milestone_fede,
                  NULL AS glidepath_start,
                  NULL AS glidepath_end,
                  NULL AS scheduled_finished_min,
                  NULL AS scheduled_finished_max,
                  NULL AS actual_finished_min,
                  NULL AS actual_finished_max,
                  SUM(meet) AS meet,
                  SUM(does_not_meet) AS does_not_meet,
                  SUM(unassessed) AS unassessed,
                  SUM(total) AS total
                FROM `{client.project}.DANDR_DEV.dvp_weekly_snapshot`
                WHERE snapshot_date = SAFE_CAST('{snapshot_date}' AS DATE)
                  AND gi_code = @gi_code
                  {pmt_clause}
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
            """
        else:
            sql = f"""
                WITH base_dvp AS (
                  SELECT
                    gi_code,
                    pmt_code,                                             
                    REGEXP_EXTRACT(program, r'^(\\\\d{{4}})') AS model_year,
                    TRIM(recommended_milestone) AS milestone_code,
                    SAFE_CAST(milestone_date AS DATE) AS milestone,
                    SAFE_CAST(milestone_fede AS DATE) AS milestone_fede,
                    SAFE_CAST(glidepath_start_date AS DATE) AS glidepath_start,
                    SAFE_CAST(glideapth_end_date AS DATE) AS glidepath_end,
                    SAFE_CAST(sched_finish AS DATE) AS scheduled_finished,
                    SAFE_CAST(actual_end_date AS DATE) AS actual_finished,
                    LOWER(TRIM(conformance_state)) AS conformance_state
                  FROM `{client.project}.DANDR_DEV.dvp_fede`
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
            """
'''

# To avoid messing up the second sql block replacement, we will use regex to find the second occurrence
parts = content.split('        sql = f"""\n            WITH base_dvp AS (')
if len(parts) == 3:
    content = parts[0] + snapshot_sql_block1.lstrip('\n') + parts[1] + snapshot_sql_block2.lstrip('\n') + parts[2].split('        job_config = bigquery.QueryJobConfig(query_parameters=query_params)')[1]
    # Wait, splitting and rejoining like this drops the rest of the second query
    pass

# We will just write a simpler patch for DVP using regex or just write the whole functions out if needed.
