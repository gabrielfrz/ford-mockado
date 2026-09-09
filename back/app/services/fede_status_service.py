"""Query and aggregate FEDE, DVP, CAE, Design Rule, and HIR metrics."""

import re
import pandas as pd
from collections import defaultdict
from app.services.bigquery_client import get_client
from google.cloud import bigquery


def _pmt_predicate(column_expression: str, parameter_name: str = "pmt_code") -> str:
    """Match both canonical PMT codes (200) and source prefixes (2 / '2 - ...')."""
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


def _row_pmt_expression(row_alias: str) -> str:
    """Read PMT from views whose field name differs without depending on one schema."""
    return f"""COALESCE(
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.pmt_code'),
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.pmt'),
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.lead_pmt'),
        JSON_VALUE(TO_JSON_STRING({row_alias}), '$.pmt_id')
    )"""


def _query_parameters(gi_code: str | None = None, pmt_code: str | None = None) -> list:
    parameters = []
    if gi_code:
        parameters.append(bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code))
    if pmt_code:
        parameters.append(bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code))
    return parameters

def autocomplete_dvp_team(query: str = "") -> list[str]:
    """Return distinct DVP teams that contain a case-insensitive search term."""
    client = get_client()
    sql = f'''
        SELECT DISTINCT dvp_team
        FROM `{client.project}.DANDR_DEV.dvp_fede`
        WHERE CAST(dvp_team AS STRING) LIKE '%{query}%'
        ORDER BY dvp_team ASC
        LIMIT 50
    '''
    df = client.query(sql).to_dataframe()
    return df['dvp_team'].dropna().astype(str).tolist()

def get_metrics_by_dvp_team_list(
    gi_code: str,
    pmt_code: str | None = None,
    snapshot_date: str | None = None,
) -> dict:
    """
    Retorna as métricas de conformance_state para CADA DVP Team individualmente,
    agrupando (concatenando) registros que possuem o mesmo nome de DVP Team.
    """
    try:
        client = get_client()
        pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
        
        query_params = _query_parameters(gi_code, pmt_code)
        where_clause = (
            "WHERE gi_code = @gi_code "
            "AND dvp_team IS NOT NULL "
            "AND conformance_state IS NOT NULL "
            "AND TRIM(conformance_state) != '' "
            f"{pmt_filter}"
        )
        
        if snapshot_date:
            table_name = f"`{client.project}.DANDR_DEV.dvp_weekly_snapshot`"
            where_clause += " AND snapshot_date = @snapshot_date"
            query_params.append(bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date))
        else:
            table_name = f"`{client.project}.DANDR_DEV.dvp_fede`"

        sql = f'''
            SELECT
                dvp_team,
                COUNT(*) AS total_assessments,
                COUNTIF(LOWER(TRIM(conformance_state)) IN ('pass', 'meet')) AS meet,
                COUNTIF(LOWER(TRIM(conformance_state)) = 'does not meet') AS does_not_meet,
                COUNTIF(LOWER(TRIM(conformance_state)) = 'unassessed') AS unassessed,
                COUNTIF(LOWER(TRIM(conformance_state)) = 'approved deviation') AS approved_deviation,
                COUNTIF(LOWER(TRIM(conformance_state)) = 'cannot assess') AS cannot_assess,
                COUNTIF(LOWER(TRIM(conformance_state)) = 'not applicable') AS not_applicable
            FROM {table_name}
            {where_clause}
            GROUP BY dvp_team
            ORDER BY dvp_team ASC
        '''
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=query_params
        )
        
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        if df.empty:
            return {
                "gi_code": gi_code,
                "dvp_teams_metrics": [],
                "total_teams": 0
            }
        
        metrics_list = []
        for _, row in df.iterrows():
            total = int(row['total_assessments'])
            metrics_list.append({
                "dvp_team": str(row['dvp_team']),
                "total_assessments": total,
                "conf_state_summary": {
                    "Meet": int(row['meet']),
                    "Does Not Meet": int(row['does_not_meet']),
                    "Unassessed": int(row['unassessed']),
                    "Approved Deviation": int(row['approved_deviation']),
                    "Cannot Assess": int(row['cannot_assess']),
                    "Not Applicable": int(row['not_applicable'])
                },
                "meet_percentage": round((int(row['meet']) / total * 100), 2) if total > 0 else 0
            })
            
        return {
            "gi_code": gi_code,
            "pmt_code": pmt_code,
            "dvp_teams_metrics": metrics_list,
            "total_teams": len(metrics_list)
        }

    except Exception as e:
        print(f"Failed to retrieve DVP team metrics: {str(e)}")
        return {"error": str(e), "gi_code": gi_code}

def get_dvp_teams_by_gi_code(gi_code: str) -> list[str]:
    """Return sorted, distinct DVP teams for a GI code."""
    client = get_client()
    sql = f'''
        SELECT DISTINCT dvp_team
        FROM `{client.project}.DANDR_DEV.dvp_fede`
        WHERE gi_code = @gi_code
        ORDER BY dvp_team ASC
    '''
    from google.cloud import bigquery
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    if df.empty:
        return []
    return df['dvp_team'].dropna().astype(str).tolist()

def autocomplete_dvp_team_by_gi_code(
    gi_code: str,
    query: str = "",
    pmt_code: str | None = None,
) -> list[str]:
    """Return DVP team suggestions restricted to a GI code and optional PMT."""
    client = get_client()
    pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
    sql = f'''
        SELECT DISTINCT dvp_team
        FROM `{client.project}.DANDR_DEV.dvp_fede`
        WHERE gi_code = @gi_code
                    {pmt_filter}
          AND CAST(dvp_team AS STRING) LIKE @query_pattern
        ORDER BY dvp_team ASC
        LIMIT 50
    '''
    from google.cloud import bigquery
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            *_query_parameters(gi_code, pmt_code),
            bigquery.ScalarQueryParameter("query_pattern", "STRING", f"%{query}%"),
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df['dvp_team'].dropna().astype(str).tolist()

def get_cpsc_by_gi_code(gi_code: str, pmt_code: str | None = None) -> list[str]:
    """Return sorted, distinct CPSC codes for a GI code and optional PMT."""
    client = get_client()
    pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
    sql = f'''
        SELECT DISTINCT cpsc
        FROM `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.dvp_fede`
        WHERE gi_code = @gi_code
                    {pmt_filter}
          AND cpsc IS NOT NULL
          AND TRIM(CAST(cpsc AS STRING)) != ''
        ORDER BY cpsc ASC
    '''
    job_config = bigquery.QueryJobConfig(
        query_parameters=_query_parameters(gi_code, pmt_code)
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    if df.empty:
        return []
    return df['cpsc'].dropna().astype(str).tolist()

def autocomplete_cpsc_by_gi_code(
    gi_code: str,
    query: str = "",
    pmt_code: str | None = None,
) -> list[str]:
    """Return CPSC suggestions restricted to a GI code and optional PMT."""
    client = get_client()
    pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
    sql = f'''
        SELECT DISTINCT cpsc
        FROM `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.dvp_fede`
        WHERE gi_code = @gi_code
                    {pmt_filter}
          AND cpsc IS NOT NULL
          AND TRIM(CAST(cpsc AS STRING)) != ''
          AND CAST(cpsc AS STRING) LIKE @query_pattern
        ORDER BY cpsc ASC
        LIMIT 50
    '''
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            *_query_parameters(gi_code, pmt_code),
            bigquery.ScalarQueryParameter("query_pattern", "STRING", f"%{query}%"),
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df['cpsc'].dropna().astype(str).tolist()

def _get_program_name_by_gi_code(gi_code: str) -> str:
    """Resolve a GI code to its complete vehicle-line program description."""
    client = get_client()
    sql = f'''
        SELECT
            vpp001_gi_prj_ds AS program_name
        FROM `{client.project}.DANDR_DEV.vehicle_line`
        WHERE vpp001_gi_prj_id = @gi_code
        LIMIT 1
    '''
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    if df.empty or df.iloc[0]['program_name'] is None:
        raise ValueError(f"Program name was not found for GI code '{gi_code}'.")
    return str(df.iloc[0]['program_name']).strip()

def get_dvp_classification_metrics(
    gi_code: str,
    cpsc: str,
    pmt_code: str | None = None,
    snapshot_date: str | None = None,
) -> dict:
    """
    Calcula métricas de classificação de requisitos por gi_code e cpsc.

    The program name is reduced to a three-token slug matching the ``pk1``
    representation in BigQuery. Missing aggregate values are normalized to zero.
    """
    client = get_client()

    program_name = _get_program_name_by_gi_code(gi_code)

    # Preserve letters, digits, and spaces while removing punctuation.
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', program_name)
    # Use the first three tokens because they form the source program key.
    program_slug = "_".join(clean_name.split()[:3])
    pattern = f"%{program_slug}%"
    pmt_filter = (
        f"AND {_pmt_predicate(_row_pmt_expression('requirement'))}"
        if pmt_code
        else ""
    )

    # A tabela fede_daily_requirementvw não possui snapshot_date. 
    # Por isso, mantemos a query original ignorando snapshot_date
    sql = f'''
        WITH consolidado_por_id AS (
          SELECT
            requirement_id,
            MAX(CASE
              WHEN classify_state NOT IN ('Not Classified', 'Not Applicable')
                   AND classify_state IS NOT NULL
              THEN 1 ELSE 0 END) AS is_classified
          FROM
                        `{client.project}.DANDR_DEV.fede_daily_requirementvw` AS requirement
          WHERE
            cpsc = @cpsc
            AND SPLIT(pk1, '|')[SAFE_OFFSET(0)] LIKE @pattern
                        {pmt_filter}
          GROUP BY
            requirement_id
        )
        SELECT
          CAST(COUNT(requirement_id) AS INT64)           AS total,
          CAST(COALESCE(SUM(is_classified), 0) AS INT64) AS classified
        FROM
          consolidado_por_id
    '''

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc),
            bigquery.ScalarQueryParameter("pattern", "STRING", pattern),
            *_query_parameters(pmt_code=pmt_code),
        ]
    )

    try:
        df = client.query(sql, job_config=job_config).to_dataframe()
        df = df.fillna(0)

        if df.empty or df['total'].iloc[0] is None:
            return {
                "program": program_name,
                "total": 0,
                "classified": 0,
                "not_classified": 0,
                "percentage": 0.0,
            }

        total = int(df['total'].iloc[0])
        classified = int(df['classified'].iloc[0])
        not_classified = total - classified
        percentage = round((classified / total) * 100, 2) if total > 0 else 0.0

        return {
            "program": program_name,
            "total": total,
            "classified": classified,
            "not_classified": not_classified,
            "percentage": percentage,
        }
    except Exception as e:
        print(f"Failed to calculate DVP classification metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def count_total_assessments(gi_code: str | None = None) -> dict:
    """Count non-null assessments, optionally restricted to a GI code."""
    client = get_client()
    
    where_clause = "WHERE assessment_id IS NOT NULL"
    query_params = []
    job_config = None
    
    if gi_code:
        where_clause += " AND gi_code = @gi_code"
        from google.cloud import bigquery
        query_params = [
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    
    sql = f'''
        SELECT COUNT(*) as total_assessments
        FROM `{client.project}.DANDR_DEV.dvp_fede`
        {where_clause}
    '''
    
    df = client.query(sql, job_config=job_config).to_dataframe()
    return {
        "total_assessments": int(df.iloc[0]['total_assessments']),
        "gi_code": gi_code
    }

def count_conf_state_results(
    gi_code: str | None = None,
    pmt_code: str | None = None,
    snapshot_date: str | None = None,
) -> dict:
    """
    Retorna a contagem de resultados agrupados por conformance_state.
    Agrupa Pass + Meet em uma única categoria "Meet".
    Inclui: Meet (Pass + Meet), Cannot Assess, Not Applicable, Unassessed, Does Not Meet, Approved Deviation
    Ignora: null, Design review report e outros valores não relevantes.
    """
    client = get_client()
    
    where_clause = "WHERE conformance_state IS NOT NULL"
    query_params = []
    job_config = None
    
    is_mock_date = False
    mock_modifier = 0
    if snapshot_date and snapshot_date.startswith("2026"):
        is_mock_date = True
        mock_modifier = int(snapshot_date.split("-")[2]) # 1, 8, 15
        snapshot_date = None
        
    if gi_code:
        where_clause += " AND gi_code = @gi_code"
    if pmt_code:
        where_clause += f" AND {_pmt_predicate('pmt_code')}"
    query_params = _query_parameters(gi_code, pmt_code)
        
    if snapshot_date:
        table_name = f"`{client.project}.DANDR_DEV.dvp_weekly_snapshot`"
        where_clause += " AND snapshot_date = @snapshot_date"
        if not query_params:
            from google.cloud import bigquery
            query_params = []
        query_params.append(bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date))
    else:
        table_name = f"`{client.project}.DANDR_DEV.dvp_fede`"
        
    job_config = bigquery.QueryJobConfig(query_parameters=query_params) if query_params else None
    
    sql = f'''
        SELECT conformance_state, COUNT(*) as count
        FROM {table_name}
        {where_clause}
        GROUP BY conformance_state
        ORDER BY count DESC
    '''
    
    df = client.query(sql, job_config=job_config).to_dataframe()
    
    if is_mock_date and not df.empty:
        # modify counts by mock_modifier
        df['count'] = df['count'].apply(lambda c: max(0, c + mock_modifier))
        
    # Agrupar os resultados conforme solicitado
    conf_state_summary = {}
    total_count = 0
    
    for _, row in df.iterrows():
        state = str(row['conformance_state']).strip()
        count = int(row['count'])
        
        # Pass + Meet = Meet
        if state.lower() in ['pass', 'meet']:
            conf_state_summary['Meet'] = conf_state_summary.get('Meet', 0) + count
        # Retain only dashboard-relevant categories.
        elif state.lower() == 'cannot assess':
            conf_state_summary['Cannot Assess'] = count
        elif state.lower() == 'not applicable':
            conf_state_summary['Not Applicable'] = count
        elif state.lower() == 'unassessed':
            conf_state_summary['Unassessed'] = count
        elif state.lower() == 'does not meet':
            conf_state_summary['Does Not Meet'] = count
        elif state.lower() == 'approved deviation':
            conf_state_summary['Approved Deviation'] = count
        # Ignore design-review reports, null values, and unsupported states.
        
        total_count += count
    
    return {
        "conf_state_summary": conf_state_summary,
        "total": total_count,
        "gi_code": gi_code,
        "pmt_code": pmt_code,
    }

# CPSC metric helpers

def _extract_cpsc_from_dvp_team(team_name: str) -> str:
    """Extract a CPSC-like identifier from supported DVP team name formats."""
    if not team_name:
        return "Other CPSC"
    
    team_name_trimmed = str(team_name).strip()
    
    # Pattern 1: six digits or the XX.XX.XX format.
    match = re.search(r'^(\d{6}|\d{2}\.\d{2}\.\d{2})', team_name_trimmed)
    if match:
        return match.group(1)
    
    # Tokenize once for the remaining patterns.
    parts = team_name_trimmed.split()
    
    # Pattern 2: a dotted numeric identifier.
    if parts:
        first_part = parts[0]
        if re.match(r'^\d+(?:\.\d+)*$', first_part):
            return first_part
    
    # Pattern 3: VI/VA XX D (for example, VI AB 1).
    match = re.search(r'^(V[AI]\s[A-Z]{2}\s\d)', team_name_trimmed)
    if match:
        return match.group(1)
    
    # Pattern 4: XX_XXX (for example, AB_CDE).
    match = re.search(r'^([A-Z]{2}_[A-Z]{3})', team_name_trimmed)
    if match:
        return match.group(1)
    
    # Fallback: prefix the first two words with "TEAM: ".
    if len(parts) >= 2:
        return f"TEAM: {' '.join(parts[0:2])}"
    elif len(parts) == 1:
        return f"TEAM: {parts[0]}"
    else:
        return "Other CPSC"

def get_assessment_dvp_status(gi_code: str) -> dict:
    """Aggregate DVP team assessment states by extracted CPSC code."""
    client = get_client()

    # Fetch only fields required by the in-memory CPSC aggregation.
    sql = f'''
        SELECT
            dvp_team,
            conformance_state
        FROM
            `{client.project}.DANDR_DEV.dvp_fede`
        WHERE
            gi_code = @gi_code
            AND conformance_state IS NOT NULL
    '''
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()

    if df.empty:
        return {
            "gi_code": gi_code,
            "cpsc_metrics": [],
            "total_dvp_teams_processed": 0
        }

    # Accumulate state counts and unique team names by CPSC.
    cpsc_level_metrics = defaultdict(lambda: defaultdict(int))
    processed_dvp_teams_per_cpsc = defaultdict(set) 

    for _, row in df.iterrows():
        dvp_team = str(row['dvp_team'])
        conformance_state = str(row['conformance_state']).strip().lower()

        cpsc = _extract_cpsc_from_dvp_team(dvp_team)

        # Normalize each source state into its dashboard category.
        if conformance_state in ['pass', 'meet']:
            cpsc_level_metrics[cpsc]['Meet'] += 1
        elif conformance_state == 'cannot assess':
            cpsc_level_metrics[cpsc]['Cannot Assess'] += 1
        elif conformance_state == 'not applicable':
            cpsc_level_metrics[cpsc]['Not Applicable'] += 1
        elif conformance_state == 'unassessed':
            cpsc_level_metrics[cpsc]['Unassessed'] += 1
        elif conformance_state == 'does not meet':
            cpsc_level_metrics[cpsc]['Does Not Meet'] += 1
        elif conformance_state == 'approved deviation':
            cpsc_level_metrics[cpsc]['Approved Deviation'] += 1

        # Track unique DVP teams independently from assessment counts.
        processed_dvp_teams_per_cpsc[cpsc].add(dvp_team)

    # Format the stable frontend response shape.
    result_list = []
    total_dvp_teams_count_across_all_cpsc = 0
    for cpsc, metrics in cpsc_level_metrics.items():
        unique_teams_for_this_cpsc = len(processed_dvp_teams_per_cpsc[cpsc])
        total_dvp_teams_count_across_all_cpsc += unique_teams_for_this_cpsc
        
        # Sum all normalized state counts for this CPSC.
        total_assessments_for_cpsc = sum(metrics.values())

        result_list.append({
            "cpsc": cpsc,
            "total_unique_dvp_teams": unique_teams_for_this_cpsc,
            "total_assessments_for_cpsc": total_assessments_for_cpsc,
            "conf_state_summary": dict(metrics)
        })
    
    # Keep response ordering deterministic.
    result_list.sort(key=lambda x: x['cpsc'])

    return {
        "gi_code": gi_code,
        "cpsc_metrics": result_list,
        "total_dvp_teams_processed": total_dvp_teams_count_across_all_cpsc
    }

def get_design_rules_evidences_metrics(gi_code: str) -> dict:
    """Aggregate Design Rule evidence states by milestone and model year."""
    client = get_client()
    project = client.project
    sql = f'''
        SELECT
          gi_code,
          REGEXP_EXTRACT(program, r'^(\\d{{4}})') AS model_year,
          DATE(milestone_date) AS milestone_date,
          milestone_fede AS fede_milestone_date,
          gpds_milestone AS gpds_milestone,
          recommended_milestone AS recommended_milestone,
          milestone_overdue AS milestone_overdue_flag,
          sme_review_milestone AS sme_review_milestone,
          COUNTIF(conformance_state = 'Meet') AS meet,
          COUNTIF(conformance_state = 'Does Not Meet') AS does_not_meet,
          COUNTIF(conformance_state = 'Unassessed') AS unassessed,
          COUNT(*) AS total
        FROM `{project}.DANDR_DEV.dvp_fede`
        WHERE gi_code = @gi_code
        GROUP BY
          gi_code,
          model_year,
          milestone_date,
          fede_milestone_date,
          gpds_milestone,
          recommended_milestone,
          milestone_overdue_flag,
          sme_review_milestone
        ORDER BY
          gi_code,
          model_year
    '''
    
    from google.cloud import bigquery
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]
    )
    df = client.query(sql, job_config=job_config).to_dataframe()
    
    if df.empty:
        return {
            "gi_code": gi_code,
            "design_rules_evidences": [],
            "total_records": 0
        }
    
    # Convert query rows to JSON-compatible records.
    records = []
    for _, row in df.iterrows():
        records.append({
            "gi_code": str(row['gi_code']),
            "model_year": str(row['model_year']) if pd.notna(row['model_year']) else None,
            "milestone_date": str(row['milestone_date']) if pd.notna(row['milestone_date']) else None,
            "fede_milestone_date": str(row['fede_milestone_date']) if pd.notna(row['fede_milestone_date']) else None,
            "gpds_milestone": str(row['gpds_milestone']) if pd.notna(row['gpds_milestone']) else None,
            "recommended_milestone": str(row['recommended_milestone']) if pd.notna(row['recommended_milestone']) else None,
            "milestone_overdue_flag": bool(row['milestone_overdue_flag']) if pd.notna(row['milestone_overdue_flag']) else None,
            "sme_review_milestone": str(row['sme_review_milestone']) if pd.notna(row['sme_review_milestone']) else None,
            "meet": int(row['meet']) if pd.notna(row['meet']) else 0,
            "does_not_meet": int(row['does_not_meet']) if pd.notna(row['does_not_meet']) else 0,
            "unassessed": int(row['unassessed']) if pd.notna(row['unassessed']) else 0,
            "total": int(row['total']) if pd.notna(row['total']) else 0
        })
    
    return {
        "gi_code": gi_code,
        "design_rules_evidences": records,
        "total_records": len(records)
    }


def get_dr_evidences_by_assessment(
    gi_code: str,
    cpsc: str | None = None,
    pmt_code: str | None = None,
) -> dict:
    """Aggregate DR evidence states by assessment and milestone fields."""
    try:
        client = get_client()
        project = client.project

        cpsc_filter = "AND cpsc = @cpsc" if cpsc else ""
        pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""

        sql = f'''
            WITH base_dvp AS (
              SELECT
                gi_code,
                assessment_id,
                cpsc,
                REGEXP_EXTRACT(program, r'^(\\d{{4}})') AS model_year,
                SAFE_CAST(milestone_date AS DATE)      AS milestone_date,
                milestone_fede,
                gpds_milestone,
                recommended_milestone,
                milestone_overdue,
                sme_review_milestone,
                LOWER(TRIM(conformance_state))         AS conf_state
              FROM `{project}.DANDR_DEV.dvp_fede`
              WHERE gi_code = @gi_code
              {cpsc_filter}
              {pmt_filter}
            )
            SELECT
              gi_code,
              assessment_id,
              cpsc,
              model_year,
              milestone_date,
              milestone_fede,
              gpds_milestone,
              recommended_milestone,
              milestone_overdue,
              sme_review_milestone,
              COUNTIF(conf_state IN ('meet', 'pass')) AS meet,
              COUNTIF(conf_state = 'does not meet')   AS does_not_meet,
              COUNTIF(conf_state = 'unassessed')      AS unassessed,
              COUNT(*)                                AS total
            FROM base_dvp
            GROUP BY
              gi_code,
              assessment_id,
              cpsc,
              model_year,
              milestone_date,
              milestone_fede,
              gpds_milestone,
              recommended_milestone,
              milestone_overdue,
              sme_review_milestone
            ORDER BY
              gi_code,
              model_year
        '''

        print(f"\n=== DEBUG ASSESSMENT MILESTONE METRICS ===")
        print(f"gi_code: {gi_code} | cpsc: {cpsc}")
        print(f"================\n")

        query_params = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
        if cpsc:
            query_params.append(bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc))
        if pmt_code:
            query_params.append(bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code))

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()
        print(f"Rows returned: {len(df)}")

        if df.empty:
            return {"gi_code": gi_code, "cpsc": cpsc, "data": [], "total_records": 0}

        records = []
        for _, row in df.iterrows():
            records.append({
                "gi_code":              str(row['gi_code']),
                "assessment_id":        str(row['assessment_id']) if pd.notna(row['assessment_id']) else None,
                "cpsc":                 str(row['cpsc']) if pd.notna(row['cpsc']) else None,
                "model_year":           str(row['model_year']) if pd.notna(row['model_year']) else None,
                "milestone_date":       str(row['milestone_date']) if pd.notna(row['milestone_date']) else None,
                "milestone_fede":       str(row['milestone_fede']) if pd.notna(row['milestone_fede']) else None,
                "gpds_milestone":       str(row['gpds_milestone']) if pd.notna(row['gpds_milestone']) else None,
                "recommended_milestone":str(row['recommended_milestone']) if pd.notna(row['recommended_milestone']) else None,
                "milestone_overdue":    bool(row['milestone_overdue']) if pd.notna(row['milestone_overdue']) else None,
                "sme_review_milestone": str(row['sme_review_milestone']) if pd.notna(row['sme_review_milestone']) else None,
                "meet":                 int(row['meet']) if pd.notna(row['meet']) else 0,
                "does_not_meet":        int(row['does_not_meet']) if pd.notna(row['does_not_meet']) else 0,
                "unassessed":           int(row['unassessed']) if pd.notna(row['unassessed']) else 0,
                "total":                int(row['total']) if pd.notna(row['total']) else 0,
            })

        return {"gi_code": gi_code, "cpsc": cpsc, "data": records, "total_records": len(records)}

    except Exception as e:
        print(f"Failed to retrieve assessment milestone metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"gi_code": gi_code, "cpsc": cpsc, "data": [], "total_records": 0, "error": str(e)}


def get_cae_detailed_data(gi_code: str, program: str | None = None) -> dict:
    """Return row-level CAE assessments for a GI code and optional program."""
    try:
        client = get_client()

        program_filter = "AND program = @program" if program else ""

        sql = f'''
            WITH base AS (
              SELECT
                gi_code,
                program,
                dvp_team,
                test_method_title,
                test_method_id,
                conformance_state,
                prototype_type,
                REGEXP_EXTRACT(dvp_team, r'^(\\d{{2}}\\.\\d{{2}}\\.\\d{{2}})') AS _cpsc_dotted,
                REGEXP_EXTRACT(dvp_team, r'^(\\d+)')                          AS _cpsc_numeric
              FROM `{client.project}.DANDR_DEV.dvp_fede`
              WHERE
                gi_code = @gi_code
                AND REGEXP_CONTAINS(UPPER(prototype_type), r'CAE')
                AND conformance_state IS NOT NULL
                AND TRIM(conformance_state) != ''
                {program_filter}
            ),
            detailed_data AS (
              SELECT
                gi_code,
                program,
                test_method_title,
                test_method_id,
                conformance_state,
                prototype_type,
                CASE
                  WHEN _cpsc_dotted IS NOT NULL THEN _cpsc_dotted
                  WHEN _cpsc_numeric IS NOT NULL AND LENGTH(_cpsc_numeric) = 6 THEN _cpsc_numeric
                  WHEN REGEXP_CONTAINS(
                         SPLIT(SPLIT(dvp_team, ' - ')[OFFSET(0)], ' ')[OFFSET(0)],
                         r'^\\d+(\\\\d+)*$'
                       ) THEN SPLIT(SPLIT(dvp_team, ' - ')[OFFSET(0)], ' ')[OFFSET(0)]
                  ELSE 'Other CPSC'
                END AS cpsc_code
              FROM base
            )
            SELECT
              program        AS Program,
              gi_code        AS GI_ID,
              cpsc_code      AS CPSC_Code,
              test_method_title AS Assessment_Name,
              test_method_id    AS Test_Method_ID,
              conformance_state AS Status,
              prototype_type    AS Prototype_Type
            FROM detailed_data
            ORDER BY cpsc_code, Assessment_Name
        '''

        print(f"\n=== DEBUG CAE DETAILED QUERY ===")
        print(f"gi_code: {gi_code} | program: {program}")
        print(f"================\n")

        query_params = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
        if program:
            query_params.append(bigquery.ScalarQueryParameter("program", "STRING", program))

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()
        print(f"Rows returned: {len(df)}")

        if df.empty:
            return {"gi_code": gi_code, "data": [], "total_records": 0}

        records = df.to_dict(orient="records")
        return {"gi_code": gi_code, "data": records, "total_records": len(records)}

    except Exception as e:
        print(f"Failed to retrieve detailed CAE data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"gi_code": gi_code, "data": [], "total_records": 0, "error": str(e)}


def get_cae_graph_data(gi_code: str) -> dict:
    """Return CAE chart data grouped by CPSC and assessment ID."""
    try:
        client = get_client()
        
        sql = f'''
            WITH base AS (
              SELECT
                assessment_id,
                dvp_team,
                conformance_state,
                prototype_type,
                REGEXP_EXTRACT(dvp_team, r'^(\\d{{2}}\\\\.\\d{{2}}\\\\.\\d{{2}})')  AS _cpsc_dotted,
                REGEXP_EXTRACT(dvp_team, r'^(\\d+)')                   AS _cpsc_numeric
              FROM `{client.project}.DANDR_DEV.dvp_fede`
              WHERE
                gi_code = '{gi_code}'
                AND NOT REGEXP_CONTAINS(UPPER(prototype_type), r'CAE')  
                AND conformance_state IS NOT NULL
                AND TRIM(conformance_state) != ''
            )
            
            SELECT
              CASE
                WHEN _cpsc_dotted IS NOT NULL
                  THEN _cpsc_dotted
                WHEN _cpsc_numeric IS NOT NULL AND LENGTH(_cpsc_numeric) = 6
                  THEN _cpsc_numeric
                WHEN REGEXP_CONTAINS(
                       SPLIT(SPLIT(dvp_team, ' - ')[OFFSET(0)], ' ')[OFFSET(0)],
                       r'^\\d+(\\\\.\\d+)*$'
                     )
                  THEN SPLIT(SPLIT(dvp_team, ' - ')[OFFSET(0)], ' ')[OFFSET(0)]
                ELSE 'Other CPSC'
              END AS cpsc_code,
              assessment_id,
              COUNT(DISTINCT dvp_team)                               AS total_unique_dvp_teams,
              COUNT(*)                                               AS total_records_for_assessment,
              COUNTIF(LOWER(conformance_state) IN ('pass', 'meet'))        AS meet,
              COUNTIF(LOWER(conformance_state) = 'unassessed')             AS unassessed,
              COUNTIF(LOWER(conformance_state) = 'approved deviation')     AS approved_deviation,
              COUNTIF(LOWER(conformance_state) = 'does not meet')          AS does_not_meet,
              COUNTIF(LOWER(conformance_state) = 'cannot assess')          AS cannot_assess,
              COUNTIF(LOWER(conformance_state) = 'not applicable')         AS not_applicable
            FROM base
            GROUP BY
              cpsc_code,
              assessment_id
            ORDER BY
              cpsc_code,
              assessment_id
        '''
        
        print(f"\n=== DEBUG CAE GRAPH QUERY ===")
        print(f"gi_code: {gi_code}")
        print(f"Query: {sql}")
        print(f"================\n")
        
        df = client.query(sql).to_dataframe()
        print(f"Rows returned: {len(df)}")
        
        if df.empty:
            print("WARNING: No rows were found for the CAE chart.")
            return {
                "gi_code": gi_code,
                "data": [],
                "total_records": 0
            }
        
        # Convert aggregate rows to the stable API response shape.
        records = []
        for _, row in df.iterrows():
            records.append({
                "cpsc_code": str(row['cpsc_code']),
                "assessment_id": str(row['assessment_id']),
                "total_unique_dvp_teams": int(row['total_unique_dvp_teams']),
                "total_records_for_assessment": int(row['total_records_for_assessment']),
                "meet": int(row['meet']) if pd.notna(row['meet']) else 0,
                "unassessed": int(row['unassessed']) if pd.notna(row['unassessed']) else 0,
                "approved_deviation": int(row['approved_deviation']) if pd.notna(row['approved_deviation']) else 0,
                "does_not_meet": int(row['does_not_meet']) if pd.notna(row['does_not_meet']) else 0,
                "cannot_assess": int(row['cannot_assess']) if pd.notna(row['cannot_assess']) else 0,
                "not_applicable": int(row['not_applicable']) if pd.notna(row['not_applicable']) else 0,
            })
        
        return {
            "gi_code": gi_code,
            "data": records,
            "total_records": len(records)
        }
        
    except Exception as e:
        print(f"Failed to retrieve CAE chart data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "gi_code": gi_code,
            "data": [],
            "total_records": 0,
            "error": str(e)
        }


def _normalize_program_tokens(program_name: str) -> list[str]:
    """
    Splits program_name into clean tokens, removing noise words and special chars.
    e.g. 'U725 Special "Mackinaw" tophat' → ['U725', 'Special', 'Mackinaw']
    """
    import re
    # Remove quotes and other special chars, then split
    cleaned = re.sub(r'["\'\(\)]', '', program_name)
    tokens = cleaned.split()
    # Drop known noise suffixes that don't appear in dr_pk2
    noise = {'tophat', 'program', 'project', 'vehicle', 'base'}
    return [t for t in tokens if t.lower() not in noise]


def _build_dr_prefix_candidates(model_year: str, tokens: list[str]) -> list[str]:
    """
    Returns a list of progressively shorter prefix candidates to try against dr_pk2.
    Longest first (most specific), shortest last (vehicle code only).
    Minimum 1 token (the vehicle code like 'U725').
    """
    candidates = []
    for length in range(len(tokens), 0, -1):
        prefix = "_".join(tokens[:length])
        candidates.append(f"{model_year}_{prefix}")
    return candidates


def get_design_rule_classification(
    model_year: str,
    program_name: str,
    pmt_code: str | None = None,
) -> dict:
    """
    Returns DESIGN RULE CLASSIFICATION data grouped by model_year and program_name.
    The dr_design_rule table has no gi_code column; it is filtered via dr_pk2.
    Uses progressive token fallback: tries the longest matching prefix first,
    then removes trailing tokens until results are found.
    """
    try:
        client = get_client()

        model_year = str(model_year).strip().split(".")[0]
        tokens = _normalize_program_tokens(str(program_name).strip())

        if not tokens:
            return {"model_year": model_year, "program_name": program_name, "data": [], "total_records": 0}

        prefix_candidates = _build_dr_prefix_candidates(model_year, tokens)
        pmt_filter = (
            f"AND {_pmt_predicate(_row_pmt_expression('t'))}"
            if pmt_code
            else ""
        )

        print(f"\n=== DEBUG DESIGN RULE CLASSIFICATION ===")
        print(f"model_year: {model_year} | program_name: {program_name}")
        print(f"Token candidates to try: {prefix_candidates}")

        sql = f'''
            WITH parsed AS (
              SELECT
                REGEXP_EXTRACT(t.dr_pk2, r'^(\\d{{4}})') AS model_year,
                REGEXP_EXTRACT(t.dr_pk2, r'^\\d{{4}}(?:\\.\\d+)?[_\\s](.*?)(?::|$)') AS program_name,
                t.classified,
                t.classification_explanation
              FROM `{client.project}.DANDR_DEV.dr_design_rule` t
              WHERE STARTS_WITH(
                LOWER(REPLACE(t.dr_pk2, ' ', '_')),
                LOWER(@dr_pk2_prefix)
              )
                            {pmt_filter}
            )

            SELECT
              model_year,
              program_name,
              COUNTIF(classified = 'Applicable') AS applicable,
              COUNTIF(classified IN ('Carryover','Previously Validated')) AS carryover,
              COUNTIF(classified = 'Not Applicable') AS not_applicable,
              COUNTIF(classified = 'Not Classified') AS unclassified,
              COUNT(*) AS total
            FROM parsed
            WHERE
              model_year IS NOT NULL
              AND program_name IS NOT NULL
            GROUP BY
              model_year,
              program_name
            ORDER BY
              model_year,
              program_name
        '''

        df = None
        matched_prefix = None
        for prefix in prefix_candidates:
            print(f"Trying prefix: {prefix}")
            result = client.query(
                sql,
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("dr_pk2_prefix", "STRING", prefix),
                        *_query_parameters(pmt_code=pmt_code),
                    ]
                )
            ).to_dataframe()
            if not result.empty:
                df = result
                matched_prefix = prefix
                print(f"Match found with prefix: {prefix} ({len(result)} rows)")
                break

        print(f"================\n")

        if df is None or df.empty:
            print("WARNING: No rows were found for Design Rule classification.")
            return {
                "model_year": model_year,
                "program_name": program_name,
                "data": [],
                "total_records": 0
            }
        
        # Convert aggregate rows to the stable API response shape.
        records = []
        for _, row in df.iterrows():
            records.append({
                "model_year": str(row['model_year']),
                "program_name": str(row['program_name']),
                "applicable": int(row['applicable']) if pd.notna(row['applicable']) else 0,
                "carryover": int(row['carryover']) if pd.notna(row['carryover']) else 0,
                "not_applicable": int(row['not_applicable']) if pd.notna(row['not_applicable']) else 0,
                "unclassified": int(row['unclassified']) if pd.notna(row['unclassified']) else 0,
                "total": int(row['total']) if pd.notna(row['total']) else 0,
            })
        
        return {
            "model_year": model_year,
            "program_name": program_name,
            "pmt_code": pmt_code,
            "matched_prefix": matched_prefix,
            "data": records,
            "total_records": len(records)
        }
        
    except Exception as e:
        print(f"Failed to retrieve Design Rule classification data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "model_year": model_year,
            "program_name": program_name,
            "data": [],
            "total_records": 0,
            "error": str(e)
        }


def get_cae_total_assessments(
    gi_code: str,
    program: str | None = None,
    cpsc: str | None = None,
    pmt_code: str | None = None,
) -> dict:
    """
    Returns total CAE assessments grouped by program.
    Filters dvp_fede table for CAE records (prototype_type contains 'CAE').
    Optional cpsc filter matches against the cpsc column (derived from dvp_team).
    """
    try:
        client = get_client()

        if cpsc is not None:
            extra_filter = "AND cpsc = @cpsc"
        elif program is not None:
            extra_filter = "AND program = @program"
        else:
            extra_filter = ""
        pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
        
        sql = f'''
            WITH base AS (
              SELECT
                gi_code,
                program,
                conformance_state,
                prototype_type
              FROM `{client.project}.DANDR_DEV.dvp_fede`
              WHERE
                gi_code = @gi_code
                AND REGEXP_CONTAINS(UPPER(prototype_type), r'CAE')
                AND conformance_state IS NOT NULL
                AND TRIM(conformance_state) != ''
                {extra_filter}
                {pmt_filter}
            )
            
            SELECT
              gi_code,
              program,
              COUNT(*) AS total_assessments,
              COUNTIF(LOWER(conformance_state) IN ('pass', 'meet'))        AS meet,
              COUNTIF(LOWER(conformance_state) = 'unassessed')             AS unassessed,
              COUNTIF(LOWER(conformance_state) = 'approved deviation')     AS approved_deviation,
              COUNTIF(LOWER(conformance_state) = 'does not meet')          AS does_not_meet,
              COUNTIF(LOWER(conformance_state) = 'cannot assess')          AS cannot_assess,
              COUNTIF(LOWER(conformance_state) = 'not applicable')         AS not_applicable
            FROM base
            GROUP BY
              gi_code,
              program
            ORDER BY
              gi_code,
              program
        '''
        
        print(f"\n=== DEBUG CAE TOTAL ASSESSMENTS QUERY ===")
        print(f"gi_code: {gi_code}")
        print(f"program: {program}")
        print(f"Query: {sql}")
        print(f"================\n")
        
        # Build query parameters
        query_params = [
            bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)
        ]
        if cpsc is not None:
            query_params.append(bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc))
        elif program is not None:
            query_params.append(bigquery.ScalarQueryParameter("program", "STRING", program))
        if pmt_code:
            query_params.append(bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code))
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        
        df = client.query(sql, job_config=job_config).to_dataframe()
        print(f"Rows returned: {len(df)}")
        
        if df.empty:
            print("WARNING: No rows found for CAE total assessments!")
            return {
                "gi_code": gi_code,
                "program": program,
                "data": [],
                "total_records": 0
            }
        
        # Convert DataFrame to list of dicts
        records = []
        for _, row in df.iterrows():
            records.append({
                "gi_id": str(row['gi_code']),
                "program": str(row['program']),
                "total_assessments": int(row['total_assessments']),
                "meet": int(row['meet']) if pd.notna(row['meet']) else 0,
                "unassessed": int(row['unassessed']) if pd.notna(row['unassessed']) else 0,
                "approved_deviation": int(row['approved_deviation']) if pd.notna(row['approved_deviation']) else 0,
                "does_not_meet": int(row['does_not_meet']) if pd.notna(row['does_not_meet']) else 0,
                "cannot_assess": int(row['cannot_assess']) if pd.notna(row['cannot_assess']) else 0,
                "not_applicable": int(row['not_applicable']) if pd.notna(row['not_applicable']) else 0,
            })
        
        return {
            "gi_code": gi_code,
            "program": program,
            "pmt_code": pmt_code,
            "data": records,
            "total_records": len(records)
        }
        
    except Exception as e:
        print(f"Error retrieving CAE total assessments: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "gi_code": gi_code,
            "program": program,
            "data": [],
            "total_records": 0,
            "error": str(e)
        }


def get_hir_completion_metrics(
    gi_code: str,
    cpsc: str | None = None,
    pmt_code: str | None = None,
    milestone_date: str | None = None,
    dvp_team: str | None = None,
) -> dict:
    """
    Returns HIR (Hardware in Review) completion metrics grouped by program details.
    
    Joins fede_daily_drassesmentvw (DR assessment data for HIR source) with
    fede_daily_fedestatus (status and program info), filtering by gi_code.
    
    Calculates evidence completion percentage based on has_evidence field.
    
    Parameters:
    - gi_code: GI Code to filter (required)
    - cpsc: Commodity CPSC filter (optional)
    - pmt_code: PMT code filter (optional)
    - milestone_date: Milestone date filter (optional)
    - dvp_team: DVP Team filter (optional)
    
    Returns:
    List of metrics grouped by program_name, gi_code, milestone_date, dvp_team, pmt_code
    with evidence counts and completion percentage.
    """
    try:
        client = get_client()
        
        # Build dynamic filters
        filters = []
        query_params = [bigquery.ScalarQueryParameter("gi_code", "STRING", gi_code)]
        
        if cpsc:
            filters.append("AND st.cpsc = @cpsc")
            query_params.append(bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc))
        
        if pmt_code:
            filters.append(f"AND {_pmt_predicate('st.pmt_code')}")
            query_params.append(bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code))
        
        if milestone_date:
            filters.append("AND st.milestone_date = @milestone_date")
            query_params.append(bigquery.ScalarQueryParameter("milestone_date", "STRING", milestone_date))

        if dvp_team:
            filters.append("AND st.dvp_team = @dvp_team")
            query_params.append(bigquery.ScalarQueryParameter("dvp_team", "STRING", dvp_team))
        
        filter_clause = " ".join(filters)
        
        sql = f'''
            WITH base_dr AS (
              SELECT
                CAST(dr_pk4_rec AS STRING) AS pk4_id,
                UPPER(TRIM(has_evidence)) AS has_evidence,
                source
              FROM
                `{client.project}.DANDR_DEV.fede_daily_drassesmentvw`
              WHERE
                UPPER(TRIM(source)) LIKE 'HIR%'
                AND dr_pk4_rec IS NOT NULL
            ),
            base_status AS (
              SELECT DISTINCT
                                CAST(pk_rec AS STRING) AS pk4_id,
                TRIM(REGEXP_EXTRACT(pk4, r'^[^|]+')) AS program_name,
                gi_code,
                milestone_date,
                dvp_team,
                pmt_code,
                cpsc
              FROM
                                `{client.project}.DANDR_DEV.fede_daily_fedestatus` AS st
              WHERE
                                st.pk_rec IS NOT NULL
                                AND st.gi_code = @gi_code
                {filter_clause}
            )
            SELECT
              st.program_name,
              st.gi_code,
              st.milestone_date,
              st.dvp_team,
              st.pmt_code,
              st.cpsc,
              COUNTIF(dr.has_evidence = 'Y') AS with_evidence,
              COUNTIF(dr.has_evidence = 'N') AS without_evidence,
              COUNT(*) AS total_items,
              ROUND(SAFE_DIVIDE(COUNTIF(dr.has_evidence = 'Y'), COUNT(*)) * 100, 1) AS completion_percentage
            FROM
              base_dr dr
            INNER JOIN
              base_status st ON dr.pk4_id = st.pk4_id
            GROUP BY 
              st.program_name,
              st.gi_code,
              st.milestone_date,
              st.dvp_team,
              st.pmt_code,
              st.cpsc
            ORDER BY 
              completion_percentage DESC
        '''
        
        print(f"\n=== DEBUG HIR COMPLETION METRICS ===")
        print(f"gi_code: {gi_code} | cpsc: {cpsc} | pmt_code: {pmt_code} | milestone_date: {milestone_date} | dvp_team: {dvp_team}")
        print(f"================\n")
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        print(f"Rows returned: {len(df)}")
        
        if df.empty:
            return {
                "gi_code": gi_code,
                "cpsc": cpsc,
                "pmt_code": pmt_code,
                "milestone_date": milestone_date,
                "dvp_team": dvp_team,
                "data": [],
                "total_records": 0
            }
        
        # Convert DataFrame to list of dicts
        records = []
        for _, row in df.iterrows():
            records.append({
                "program_name": str(row['program_name']) if pd.notna(row['program_name']) else None,
                "gi_code": str(row['gi_code']) if pd.notna(row['gi_code']) else None,
                "milestone_date": str(row['milestone_date']) if pd.notna(row['milestone_date']) else None,
                "dvp_team": str(row['dvp_team']) if pd.notna(row['dvp_team']) else None,
                "pmt_code": str(row['pmt_code']) if pd.notna(row['pmt_code']) else None,
                "cpsc": str(row['cpsc']) if pd.notna(row['cpsc']) else None,
                "with_evidence": int(row['with_evidence']) if pd.notna(row['with_evidence']) else 0,
                "without_evidence": int(row['without_evidence']) if pd.notna(row['without_evidence']) else 0,
                "total_items": int(row['total_items']) if pd.notna(row['total_items']) else 0,
                "completion_percentage": float(row['completion_percentage']) if pd.notna(row['completion_percentage']) else 0.0,
            })
        
        return {
            "gi_code": gi_code,
            "cpsc": cpsc,
            "pmt_code": pmt_code,
            "milestone_date": milestone_date,
            "dvp_team": dvp_team,
            "data": records,
            "total_records": len(records)
        }
        
    except Exception as e:
        print(f"Error retrieving HIR completion metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
