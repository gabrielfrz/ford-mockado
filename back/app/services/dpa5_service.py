"""Query and aggregate DPA5 K-PAC status and glidepath data."""

import pandas as pd
from collections import defaultdict
from datetime import datetime
from google.cloud import bigquery
from app.services.bigquery_client import get_client


# Source tables (external project — read-only)
_DPA5_ISSUE_TABLE     = "prj-dfad-1242-uapd-p-1242.bq_666_dpa5_lc_vw.dpa5_issue_list_field_raw_vw"
_DPA5_GLIDEPATH_TABLE = "prj-dfad-1242-uapd-p-1242.bq_666_dpa5_lc_vw.dpa5_glidepath_date_raw_vw"
_DPA5_GI_MAP_TABLE    = "prj-dfad-1242-uapd-p-1242.bq_666_dpa5_lc_vw.dpa5_dashboard_id_gp_id_raw_vw"


def _safe_int(val) -> int:
    try:
        return int(val) if pd.notna(val) else 0
    except Exception:
        return 0

_MILESTONE_ORDER = ["mr","ps","psc","fpd","fc1","fc2","fc3","fc4","fc5","k3","k5",
    "upv0","upv1","upv2","pa","fdj","dcv","pec","fec","lr","ls","j1","oktb","fsr",
    "faa","ept","ept_ipd","tt_ipd","tt","pp","mp1","mp2","_pcf1","_tcb1","_tcb2",
    "tmr","tps","tsc","tdc","ttc","tdj","tpv","unv0","unv1","unv2","xm","aa1","vp","_dtm"]
_MILESTONE_RANK = {m: i for i, m in enumerate(_MILESTONE_ORDER)}


def _safe_str(val):
    return str(val) if pd.notna(val) else None


def get_dpa5_snapshots(gi_code: str):
    try:
        # Mocking for UI testing
        return ["2024-01-01", "2024-01-08"]
    except Exception as e:
        print(f"Erro ao buscar snapshots: {str(e)}")
        return []


def _get_cpscs_for_gi_code(client, gi_code: str) -> list[str]:
    """Returns distinct CPSC codes from dvp_fede for the given gi_code."""
    sql = """
        SELECT DISTINCT CAST(cpsc AS STRING) AS cpsc
        FROM `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.dvp_fede`
        WHERE gi_code = @gi_code
          AND cpsc IS NOT NULL
          AND TRIM(CAST(cpsc AS STRING)) != ''
        ORDER BY cpsc ASC
    """
    df = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
        )
    ).to_dataframe()
    return df["cpsc"].dropna().astype(str).tolist()

import re

def _get_base_programs_for_gi_code(client, gi_code: str) -> list[str]:
    """Extracts base program codes (e.g. U725, P800) from dvp_fede program strings."""
    sql = """
        SELECT DISTINCT program
        FROM `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.dvp_fede`
        WHERE gi_code = @gi_code
          AND program IS NOT NULL
    """
    df = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
        )
    ).to_dataframe()
    
    base_codes = set()
    for prog in df["program"].dropna().astype(str):
        parts = re.split(r'[^a-zA-Z0-9]', prog)
        for p in parts:
            if re.match(r'^[a-zA-Z][a-zA-Z0-9]+', p) and len(p) >= 3:
                base_codes.add(p.upper())
                break
                
    return list(base_codes)


def get_dpa5_cpsc_list(gi_code: str, pmt_filter: str | None = None) -> list[str]:
    """
    Returns distinct CPSC codes present in DPA5 data for the given gi_code,
    optionally filtered by PMT code (sidebar value like '200').
    """
    try:
        client = get_client()

        pmt_prefix: str | None = None
        if pmt_filter:
            try:
                pmt_prefix = str(int(pmt_filter) // 100)
            except (ValueError, TypeError):
                pmt_prefix = pmt_filter.split()[0]
        pmt_clause = "AND lead_pmt LIKE @pmt_prefix_like" if pmt_prefix else ""

        # Check gi_map strategy
        gi_count = client.query(
            f"SELECT COUNT(*) AS cnt FROM `{_DPA5_GI_MAP_TABLE}` WHERE gi LIKE CONCAT('%', @gi_code, '%')",
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
            )
        ).to_dataframe().iloc[0]["cnt"]

        if gi_count > 0:
            issue_filter = f"""
                dashboard_id IN (
                  SELECT dashboard_id FROM `{_DPA5_GI_MAP_TABLE}` WHERE gi LIKE CONCAT('%', @gi_code, '%')
                )
                {pmt_clause}
            """
            query_params = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
        else:
            all_cpscs = _get_cpscs_for_gi_code(client, gi_code)
            if not all_cpscs:
                return []
            cpsc_in = ", ".join(f"'{c}'" for c in all_cpscs)
            
            base_programs = _get_base_programs_for_gi_code(client, gi_code)
            if not base_programs:
                program_filter = "AND 1=0"
            else:
                like_conditions = " OR ".join([f"LOWER(program) LIKE '%{b.lower()}%'" for b in base_programs])
                program_filter = f"AND ({like_conditions})"
                
            issue_filter = f"""
                cpsc IN ({cpsc_in}) 
                {program_filter}

                {pmt_clause}
            """
            query_params = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]

        if pmt_prefix:
            query_params.append(bigquery.ScalarQueryParameter("pmt_prefix_like", "STRING", f"{pmt_prefix} -%"))

        sql = f"""
            SELECT DISTINCT cpsc
            FROM `{_DPA5_ISSUE_TABLE}`
            WHERE {issue_filter}
              AND cpsc IS NOT NULL
              AND TRIM(cpsc) != ''
            ORDER BY cpsc
        """
        job_config = bigquery.QueryJobConfig(query_parameters=query_params) if query_params else None
        df = client.query(sql, job_config=job_config).to_dataframe() if job_config else client.query(sql).to_dataframe()
        return df["cpsc"].dropna().astype(str).tolist()

    except Exception as e:
        print(f"Error in get_dpa5_cpsc_list: {e}")
        return []


def get_dpa5_data(gi_code: str, cpsc_filter: str | None = None, pmt_filter: str | None = None, snapshot_date: str | None = None) -> dict:
    """
    Returns DPA5 K-PAC aggregated data with glidepath milestones.

    First tries to resolve dashboard_ids via dpa5_dashboard_id_gp_id_raw_vw (gi = gi_code).
    Falls back to CPSC-based filtering via dvp_fede when the gi_map has no entries.
    """
    try:
        client = get_client()

        cpsc_clause = "AND cpsc = @cpsc" if cpsc_filter else ""

        # Convert sidebar PMT code (e.g. "200") to lead_pmt numeric prefix (e.g. "2").
        # DPA5 lead_pmt format is "<n> - <Description>" (e.g. "2 - Body Interior").
        # Sidebar codes are multiples of 100, so we extract the leading integer.
        pmt_prefix: str | None = None
        if pmt_filter:
            try:
                pmt_prefix = str(int(pmt_filter) // 100)
            except (ValueError, TypeError):
                pmt_prefix = pmt_filter.split()[0]  # fallback: first token
        pmt_clause = "AND lead_pmt LIKE @pmt_prefix_like" if pmt_prefix else ""

        # Extract base program (e.g. U725) to do a fuzzy match against dpa5.program
        base_programs = _get_base_programs_for_gi_code(client, gi_code)
        if not base_programs:
            program_filter = "AND 1=0"
        else:
            like_conditions = " OR ".join([f"LOWER(program) LIKE '%{b.lower()}%'" for b in base_programs])
            program_filter = f"AND ({like_conditions})"

        # --- Strategy 1: filter via gi_map dashboard_ids ---
        gi_map_sql = f"""
            SELECT COUNT(*) AS cnt
            FROM `{_DPA5_GI_MAP_TABLE}`
            WHERE gi LIKE CONCAT('%', @gi_code, '%')
        """
        gi_count = client.query(
            gi_map_sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
            )
        ).to_dataframe().iloc[0]["cnt"]

        if gi_count > 0:
            print(f"DPA5: using gi_map strategy ({gi_count} dashboard_ids for {gi_code})")
            issue_filter = f"""
                dashboard_id IN (
                  SELECT dashboard_id FROM `{_DPA5_GI_MAP_TABLE}` WHERE gi LIKE CONCAT('%', @gi_code, '%')
                )
                {cpsc_clause}
                {pmt_clause}
                {program_filter}
            """
            query_params = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
            if cpsc_filter:
                query_params.append(bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc_filter))
            # pmt_clause uses LIKE with a query param
            if pmt_prefix:
                query_params.append(bigquery.ScalarQueryParameter("pmt_prefix_like", "STRING", f"{pmt_prefix} -%"))
        else:
            # --- Strategy 2: filter via CPSC codes from dvp_fede ---
            if cpsc_filter:
                print(f"DPA5: using direct CPSC filter ({cpsc_filter}) for {gi_code}")
                issue_filter = f"cpsc = @cpsc {program_filter} {pmt_clause}"
                query_params = [
                    bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc_filter),
                    bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
                ]
                if pmt_prefix:
                    query_params.append(bigquery.ScalarQueryParameter("pmt_prefix_like", "STRING", f"{pmt_prefix} -%"))
            else:
                all_cpscs = _get_cpscs_for_gi_code(client, gi_code)
                if not all_cpscs:
                    return {"gi_code": gi_code, "cpsc_filter": cpsc_filter, "pmt_filter": pmt_filter, "data": [], "total_records": 0}

                cpsc_in = ", ".join(f"'{c}'" for c in all_cpscs)
                print(f"DPA5: using CPSC strategy ({len(all_cpscs)} CPSCs for {gi_code})")
                issue_filter = f"cpsc IN ({cpsc_in}) {program_filter} {pmt_clause}"
                query_params = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
                if pmt_prefix:
                    query_params.append(bigquery.ScalarQueryParameter("pmt_prefix_like", "STRING", f"{pmt_prefix} -%"))

        is_mock_date = False
        mock_modifier = 0
        if snapshot_date and snapshot_date.startswith("2026"):
            is_mock_date = True
            mock_modifier = int(snapshot_date.split("-")[2]) # 1, 8, 15
            snapshot_date = None

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
                WHERE 1=1 {cpsc_clause.replace("cpsc =", "kp.cpsc =")} {pmt_clause.replace("lead_pmt", "kp.lead_pmt")} {program_filter.replace("program", "kp.program")}
                ORDER BY kp.cpsc, kp.lead_pmt, kp.k_pac_id
            """
        else:
            sql = f"""
                WITH unnested_issues AS (

              SELECT
                dashboard_id,
                cpsc,
                lead_pmt,
                program,
                date_opened,
                date_closed,
                mfg_functional_area,
                COALESCE(SAFE_CAST(blue___cannot_assess   AS INT64), 0) AS blue_cannot_assess,
                COALESCE(SAFE_CAST(green___compliant       AS INT64), 0) AS green_compliant,
                COALESCE(SAFE_CAST(na___not_applicable     AS INT64), 0) AS na_not_applicable,
                COALESCE(SAFE_CAST(non_scorable            AS INT64), 0) AS non_scorable,
                COALESCE(SAFE_CAST(not_evaluated           AS INT64), 0) AS not_evaluated,
                COALESCE(SAFE_CAST(red___not_compliant     AS INT64), 0) AS red_not_compliant,
                TRIM(k_pac_single) AS k_pac_id
              FROM `{_DPA5_ISSUE_TABLE}`,
              UNNEST(SPLIT(REGEXP_REPLACE(k_pac_id, r'[\\r\\n]+', ','), ',')) AS k_pac_single
              WHERE {issue_filter}
            ),

            k_pac_aggregated AS (
              SELECT
                cpsc,
                lead_pmt,
                program,
                k_pac_id,
                ARRAY_AGG(DISTINCT dashboard_id IGNORE NULLS) AS issue_dashboard_ids,
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
            ),

            glidepath_date AS (
              SELECT
                dashboard_id AS t2_dashboard_id,
                CAST(glidepath_date AS STRING) AS glidepath_date,
                milestone,
                SAFE_CAST(assessment_goal_curve  AS FLOAT64) AS assessment_goal_curve,
                SAFE_CAST(compliance_goal_curve  AS FLOAT64) AS compliance_goal_curve
              FROM `{_DPA5_GLIDEPATH_TABLE}`
            ),

            kpac_dashboard_expanded AS (
              SELECT kp.cpsc, kp.lead_pmt, kp.program, kp.k_pac_id, dash_id AS dashboard_id
              FROM k_pac_aggregated AS kp,
              UNNEST(kp.issue_dashboard_ids) AS dash_id
            ),

            kpac_glidepath_raw AS (
              SELECT
                kde.cpsc, kde.lead_pmt, kde.program, kde.k_pac_id,
                gd.glidepath_date,
                gd.milestone,
                gd.assessment_goal_curve,
                gd.compliance_goal_curve
              FROM kpac_dashboard_expanded AS kde
              LEFT JOIN glidepath_date AS gd ON gd.t2_dashboard_id = kde.dashboard_id
            ),

            kpac_glidepath_consolidated AS (
              SELECT
                cpsc, lead_pmt, program, k_pac_id, glidepath_date, milestone,
                AVG(assessment_goal_curve) AS avg_assessment_goal_curve,
                AVG(compliance_goal_curve) AS avg_compliance_goal_curve
              FROM kpac_glidepath_raw
              WHERE milestone IS NOT NULL
              GROUP BY cpsc, lead_pmt, program, k_pac_id, glidepath_date, milestone
            ),

            kpac_glidepath_array AS (
              SELECT
                cpsc, lead_pmt, program, k_pac_id,
                ARRAY_AGG(
                  STRUCT(glidepath_date, milestone, avg_assessment_goal_curve, avg_compliance_goal_curve)
                  ORDER BY glidepath_date ASC
                ) AS glidepath_milestones
              FROM kpac_glidepath_consolidated
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
              gpa.glidepath_milestones
            FROM k_pac_aggregated AS kp
            LEFT JOIN kpac_glidepath_array AS gpa
              ON  kp.k_pac_id  = gpa.k_pac_id
              AND kp.program   = gpa.program
              AND kp.lead_pmt  = gpa.lead_pmt
              AND kp.cpsc      = gpa.cpsc
            ORDER BY kp.cpsc, kp.lead_pmt, kp.k_pac_id
        """

        print(f"\n=== DEBUG DPA5 QUERY ===")
        print(f"gi_code: {gi_code} | cpsc_filter: {cpsc_filter} | pmt_filter: {pmt_filter} -> lead_pmt prefix: {pmt_prefix}")
        print(f"========================\n")

        job_config = bigquery.QueryJobConfig(query_parameters=query_params) if query_params else None
        df = client.query(sql, job_config=job_config).to_dataframe() if job_config else client.query(sql).to_dataframe()
        print(f"Rows returned: {len(df)}")

        if is_mock_date and not df.empty:
            if 'total_issues' in df.columns:
                df['total_issues'] = df['total_issues'] + mock_modifier
            if 'total_green_compliant' in df.columns:
                df['total_green_compliant'] = df['total_green_compliant'] + (mock_modifier * 2)
            if 'total_red_not_compliant' in df.columns:
                df['total_red_not_compliant'] = df['total_red_not_compliant'].apply(lambda x: max(0, x - mock_modifier))

        if df.empty:
            return {
                "gi_code": gi_code,
                "cpsc_filter": cpsc_filter,
                "pmt_filter": pmt_filter,
                "data": [],
                "total_records": 0,
            }

        records = []
        for _, row in df.iterrows():
            milestones = []
            raw = row["glidepath_milestones"]
            if raw is not None and not (isinstance(raw, float) and pd.isna(raw)):
                for m in raw:
                    try:
                        gdate = m.get("glidepath_date")
                        ms  = m["milestone"]
                        agc = m["avg_assessment_goal_curve"]
                        cgc = m["avg_compliance_goal_curve"]
                        milestones.append({
                            "glidepath_date":        str(gdate) if gdate else None,
                            "milestone":             str(ms)    if ms  is not None else None,
                            "assessment_goal_curve": float(agc) if agc is not None else None,
                            "compliance_goal_curve": float(cgc) if cgc is not None else None,
                        })
                    except Exception:
                        pass

            records.append({
                "cpsc":                     _safe_str(row["cpsc"]),
                "lead_pmt":                 _safe_str(row["lead_pmt"]),
                "program":                  _safe_str(row["program"]),
                "k_pac_id":                 _safe_str(row["k_pac_id"]),
                "total_issues":             _safe_int(row["total_issues"]),
                "mfg_functional_area":      _safe_str(row["mfg_functional_area"]),
                "total_green_compliant":    _safe_int(row["total_green_compliant"]),
                "total_red_not_compliant":  _safe_int(row["total_red_not_compliant"]),
                "total_blue_cannot_assess": _safe_int(row["total_blue_cannot_assess"]),
                "total_na_not_applicable":  _safe_int(row["total_na_not_applicable"]),
                "total_non_scorable":       _safe_int(row["total_non_scorable"]),
                "total_not_evaluated":      _safe_int(row["total_not_evaluated"]),
                "glidepath_milestones":     milestones,
            })

        return {
            "gi_code": gi_code,
            "cpsc_filter": cpsc_filter,
            "pmt_filter": pmt_filter,
            "data": records,
            "total_records": len(records),
        }

    except Exception as e:
        print(f"Error fetching DPA5 data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "gi_code": gi_code,
            "cpsc_filter": cpsc_filter,
            "pmt_filter": pmt_filter,
            "data": [],
            "total_records": 0,
            "error": str(e),
        }


def _get_glidepath_via_cpscs(client, gi_code: str) -> list[dict]:
    """
    Fallback glidepath query when the embedded K-PAC approach returns no data.

    Schema:
      glidepath: dashboard_id, glidepath_date, milestone, assessment_goal_curve, compliance_goal_curve
      gi_map:    dashboard_id, gi, ...
      issue:     dashboard_id, cpsc, ...

    Strategies (in order):
    1. gi_map exact match: glidepath.dashboard_id = gi_map.dashboard_id WHERE gi = gi_code
    2. gi_map LIKE match: for compound gi values ("GI-10032,GI-3067")
    3. CPSC bridge: get CPSCs from dvp_fede → get dashboard_ids from issue table → join to glidepath

    X-axis  = glidepath_date (actual date)
    Tooltip = milestone name (UPV1, FDJ, SOP ...)
    """
    gi_param = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]

    base_select = f"""
        SELECT
            CAST(gp.glidepath_date AS STRING)                   AS glidepath_date,
            gp.milestone,
            AVG(SAFE_CAST(gp.assessment_goal_curve AS FLOAT64)) AS avg_agc,
            AVG(SAFE_CAST(gp.compliance_goal_curve AS FLOAT64)) AS avg_cgc
        FROM `{_DPA5_GLIDEPATH_TABLE}` AS gp
    """

    strategies = [
        (1, base_select + f"""
            INNER JOIN `{_DPA5_GI_MAP_TABLE}` AS gm
                   ON  gm.gi = @gi_code AND gp.dashboard_id = gm.dashboard_id
            WHERE gp.glidepath_date IS NOT NULL
            GROUP BY gp.glidepath_date, gp.milestone ORDER BY SAFE.PARSE_DATE('%d-%b-%Y', gp.glidepath_date)
        """, gi_param),
        (2, base_select + f"""
            INNER JOIN `{_DPA5_GI_MAP_TABLE}` AS gm
                   ON  gm.gi LIKE CONCAT('%', @gi_code, '%') AND gp.dashboard_id = gm.dashboard_id
            WHERE gp.glidepath_date IS NOT NULL
            GROUP BY gp.glidepath_date, gp.milestone ORDER BY gp.glidepath_date ASC
        """, gi_param),
    ]

    df = pd.DataFrame()
    for strat_id, sql, params in strategies:
        try:
            df = client.query(
                sql,
                job_config=bigquery.QueryJobConfig(query_parameters=params)
            ).to_dataframe()
            print(f"DPA5 glidepath strategy {strat_id} (gi_map): {len(df)} rows for {gi_code}")
            if not df.empty:
                break
        except Exception as e:
            print(f"DPA5 glidepath strategy {strat_id} failed: {e}")
            df = pd.DataFrame()

    # Strategy 3: CPSC bridge
    if df.empty:
        try:
            cpscs = _get_cpscs_for_gi_code(client, gi_code)
            
            base_programs = _get_base_programs_for_gi_code(client, gi_code)
            if not base_programs:
                program_filter = "AND 1=0"
            else:
                like_conditions = " OR ".join([f"LOWER(program) LIKE '%{b.lower()}%'" for b in base_programs])
                program_filter = f"AND ({like_conditions})"
                
            if cpscs:
                cpsc_in = ", ".join(f"'{c}'" for c in cpscs)
                sql_cpsc = base_select + f"""
                    WHERE gp.glidepath_date IS NOT NULL
                      AND gp.dashboard_id IN (
                          SELECT DISTINCT dashboard_id
                          FROM `{_DPA5_ISSUE_TABLE}`
                          WHERE cpsc IN ({cpsc_in})
                            {program_filter}
                            AND dashboard_id IS NOT NULL
                      )
                    GROUP BY gp.glidepath_date, gp.milestone ORDER BY gp.glidepath_date ASC
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
                )
                df = client.query(sql_cpsc, job_config=job_config).to_dataframe()
                print(f"DPA5 glidepath strategy 3 (CPSC bridge): {len(df)} rows for {gi_code}")
        except Exception as e:
            print(f"DPA5 glidepath strategy 3 failed: {e}")
            df = pd.DataFrame()

    result = []
    for _, row in df.iterrows():
        date   = _safe_str(row["glidepath_date"])
        mstone = _safe_str(row["milestone"]) if "milestone" in row.index else None
        if not date:
            continue
        agc = float(row["avg_agc"]) if pd.notna(row["avg_agc"]) else None
        cgc = float(row["avg_cgc"]) if pd.notna(row["avg_cgc"]) else None
        if agc is not None and agc <= 1.0:
            agc = round(agc * 100, 2)
        if cgc is not None and cgc <= 1.0:
            cgc = round(cgc * 100, 2)
        result.append({"glidepath_date": date, "milestone_name": mstone, "avg_agc": agc, "avg_cgc": cgc})
    return result


def get_dpa5_summary(gi_code: str, cpsc_filter: str | None = None, pmt_filter: str | None = None, snapshot_date: str | None = None) -> dict:
    """
    Returns DPA5 summary (totals for donut chart) and glidepath goal curves
    per milestone date (for the glidepath chart).

    The glidepath array contains one entry per milestone date with:
    - current status counts (compliant / not_compliant / not_assessable) — same values at all dates
    - goal curves (assessment_goal_curve, compliance_goal_curve) from the glidepath table
    """
    try:
        full = get_dpa5_data(gi_code=gi_code, cpsc_filter=cpsc_filter, pmt_filter=pmt_filter, snapshot_date=snapshot_date)
        records = full.get("data", [])

        # Aggregate totals for donut
        total_compliant = sum(r["total_green_compliant"] for r in records)
        total_not_compliant = sum(r["total_red_not_compliant"] for r in records)
        total_not_assessable = sum(
            r["total_blue_cannot_assess"] + r["total_na_not_applicable"] +
            r["total_non_scorable"] + r["total_not_evaluated"]
            for r in records
        )
        total = total_compliant + total_not_compliant + total_not_assessable

        # Collect glidepath milestone dates from the embedded K-PAC JOIN result
        # (milestone = name like UPV1; the embedded approach works when issue.dashboard_id
        #  matches glidepath.dashboard_id — reliable for some PMTs, not all)
        milestone_map: dict[str, dict] = {}
        for r in records:
            for m in r.get("glidepath_milestones", []):
                label = m.get("milestone")
                gdate = m.get("glidepath_date")
                if not label or not gdate:
                    continue
                
                if gdate not in milestone_map:
                    milestone_map[gdate] = {"milestone_name": label, "agc_vals": [], "cgc_vals": []}
                
                if m.get("assessment_goal_curve") is not None:
                    milestone_map[gdate]["agc_vals"].append(m["assessment_goal_curve"])
                if m.get("compliance_goal_curve") is not None:
                    milestone_map[gdate]["cgc_vals"].append(m["compliance_goal_curve"])

        # Build glidepath from embedded data
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        glidepath_embedded = []
        for gdate in sorted(milestone_map.keys()):
            d = milestone_map[gdate]
            label = d["milestone_name"]
            agc_vals = d["agc_vals"]
            cgc_vals = d["cgc_vals"]
            
            agc = round(sum(agc_vals) / len(agc_vals), 2) if agc_vals else None
            cgc = round(sum(cgc_vals) / len(cgc_vals), 2) if cgc_vals else None
            
            # Normalise fractions (0-1) → percent
            if agc is not None and agc <= 1.0:
                agc = round(agc * 100, 2)
            if cgc is not None and cgc <= 1.0:
                cgc = round(cgc * 100, 2)
                
            is_future = gdate > now_str
            
            glidepath_embedded.append({
                "milestone_date": gdate,       # The actual timestamp for chronological sorting
                "milestone_name": label,       # e.g. "FDJ 14-Aug-2026"
                "compliant": 0 if is_future else total_compliant,
                "not_compliant": 0 if is_future else total_not_compliant,
                "not_assessable": 0 if is_future else total_not_assessable,
                "assessment_goal_curve": agc,
                "compliance_goal_curve": cgc,
                "compliance_prediction": None,
            })

        # Fallback: if embedded approach returned nothing, query glidepath table directly
        # The direct approach uses glidepath_date (actual date) as X-axis and milestone name for annotations
        glidepath = glidepath_embedded
        if not glidepath_embedded:
            client = get_client()
            gp_rows = _get_glidepath_via_cpscs(client, gi_code)
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            glidepath = []
            for row in gp_rows:
                gdate = row["glidepath_date"]
                is_future = gdate > now_str
                glidepath.append({
                    "milestone_date": gdate,
                    "milestone_name": row["milestone_name"],
                    "compliant": 0 if is_future else total_compliant,
                    "not_compliant": 0 if is_future else total_not_compliant,
                    "not_assessable": 0 if is_future else total_not_assessable,
                    "assessment_goal_curve": row["avg_agc"],
                    "compliance_goal_curve": row["avg_cgc"],
                    "compliance_prediction": None,
                })

        return {
            "gi_code": gi_code,
            "cpsc_filter": cpsc_filter,
            "pmt_filter": pmt_filter,
            "summary": {
                "compliant": total_compliant,
                "not_compliant": total_not_compliant,
                "not_assessable": total_not_assessable,
                "total": total,
            },
            "glidepath": glidepath,
        }

    except Exception as e:
        print(f"Error in get_dpa5_summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "gi_code": gi_code,
            "cpsc_filter": cpsc_filter,
            "pmt_filter": pmt_filter,
            "summary": {"compliant": 0, "not_compliant": 0, "not_assessable": 0, "total": 0},
            "glidepath": [],
            "error": str(e),
        }

def get_dpa5_snapshots(gi_code: str) -> list[str]:
    try:
        client = get_client()
        sql = f"""
            SELECT DISTINCT CAST(snapshot_date AS STRING) as snapshot_date 
            FROM `{client.project}.DANDR_DEV.dpa5_weekly_snapshot` 
            ORDER BY snapshot_date DESC
        """
        df = client.query(sql).to_dataframe()
        return df['snapshot_date'].dropna().tolist()
    except Exception as e:
        print(f'Error getting dpa5 snapshots: {e}')
        return []

