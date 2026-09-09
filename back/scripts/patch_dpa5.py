import re
import os

file_path = r"c:\Users\GARAGAO1\OneDrive - azureford\Desktop\projeto\back\app\services\dpa5_service.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update get_dpa5_data signature
content = content.replace(
    "def get_dpa5_data(gi_code: str, cpsc_filter: str | None = None, pmt_filter: str | None = None) -> dict:",
    "def get_dpa5_data(gi_code: str, cpsc_filter: str | None = None, pmt_filter: str | None = None, snapshot_date: str | None = None) -> dict:"
)

# 2. Update get_dpa5_summary signature
content = content.replace(
    "def get_dpa5_summary(gi_code: str, cpsc_filter: str | None = None, pmt_filter: str | None = None) -> dict:",
    "def get_dpa5_summary(gi_code: str, cpsc_filter: str | None = None, pmt_filter: str | None = None, snapshot_date: str | None = None) -> dict:"
)

# 3. Propagate snapshot_date from summary to data
content = content.replace(
    "full = get_dpa5_data(gi_code=gi_code, cpsc_filter=cpsc_filter, pmt_filter=pmt_filter)",
    "full = get_dpa5_data(gi_code=gi_code, cpsc_filter=cpsc_filter, pmt_filter=pmt_filter, snapshot_date=snapshot_date)"
)

# 4. Inject snapshot logic into get_dpa5_data
old_sql_block = '''        sql = f"""
            WITH unnested_issues AS ('''

snapshot_sql_block = '''
        if snapshot_date:
            if query_params is None:
                query_params = []
            query_params.append(bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date))
            
            sql = f"""
                WITH k_pac_aggregated AS (
                  SELECT
                    cpsc,
                    lead_pmt,
                    program,
                    k_pac_id,
                    SUM(total_issues)                  AS total_issues,
                    MAX(mfg_functional_area)           AS mfg_functional_area,
                    SUM(total_green_compliant)         AS total_green_compliant,
                    SUM(total_red_not_compliant)       AS total_red_not_compliant,
                    SUM(total_blue_cannot_assess)      AS total_blue_cannot_assess,
                    SUM(total_na_not_applicable)       AS total_na_not_applicable,
                    SUM(total_non_scorable)            AS total_non_scorable,
                    SUM(total_not_evaluated)           AS total_not_evaluated
                  FROM `{client.project}.DANDR_DEV.dpa5_weekly_snapshot`
                  WHERE snapshot_date = @snapshot_date
                  GROUP BY cpsc, lead_pmt, program, k_pac_id
                )
                SELECT
                  kp.cpsc,
                  kp.lead_pmt,
                  kp.program,
                  kp.k_pac_id,
                  kp.total_issues,
                  kp.mfg_functional_area,
                  kp.total_green_compliant,
                  kp.total_red_not_compliant,
                  kp.total_blue_cannot_assess,
                  kp.total_na_not_applicable,
                  kp.total_non_scorable,
                  kp.total_not_evaluated,
                  NULL AS glidepath_milestones
                FROM k_pac_aggregated AS kp
                WHERE 1=1 {cpsc_clause.replace("cpsc =", "kp.cpsc =")} {pmt_clause.replace("lead_pmt", "kp.lead_pmt")}
                ORDER BY kp.cpsc, kp.lead_pmt, kp.k_pac_id
            """
        else:
            sql = f"""
                WITH unnested_issues AS (
'''

content = content.replace(old_sql_block, snapshot_sql_block.lstrip('\n'))

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("dpa5_service.py patched successfully.")
