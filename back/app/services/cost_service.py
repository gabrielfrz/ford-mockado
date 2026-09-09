"""Query and aggregate tooling- and piece-cost data from BigQuery."""

from app.services.bigquery_client import get_client, get_table_path
from app.routes.pmt_routes import resolve_pmt
from google.cloud import bigquery


BOM_PIECE_TABLE = 'ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.bom_piece_cost'
BOM_TOOLING_TABLE = 'ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.bom_tooling_cost'


def get_cpsc_by_effective_point(effectivein: str) -> list[str]:
    """
    Busca todos os CPSCs únicos para um effective point específico.
    """
    client = get_client()
    
    sql = f'''
        SELECT DISTINCT cpsc
        FROM `{BOM_PIECE_TABLE}`
        WHERE effectivein = @effectivein
          AND cpsc IS NOT NULL
          AND TRIM(cpsc) != ''
        ORDER BY cpsc ASC
    '''
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)
        ]
    )
    
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df['cpsc'].dropna().astype(str).tolist()


def autocomplete_cpsc_by_effective_point(effectivein: str, query: str = "") -> list[str]:
    """
    Autocomplete de CPSC filtrado por effective point.
    """
    client = get_client()
    
    query_filter = ""
    if query:
        query_filter = f"AND LOWER(CAST(cpsc AS STRING)) LIKE LOWER('%{query}%')"
    
    sql = f'''
        SELECT DISTINCT cpsc
        FROM `{BOM_PIECE_TABLE}`
        WHERE effectivein = @effectivein
          AND cpsc IS NOT NULL
          AND TRIM(cpsc) != ''
          {query_filter}
        ORDER BY cpsc ASC
        LIMIT 50
    '''
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)
        ]
    )
    
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df['cpsc'].dropna().astype(str).tolist()


def get_pmt_by_effective_point(effectivein: str, cpsc: str = None) -> list[str]:
    """
    Busca todos os PMTs únicos para um effective point, opcionalmente filtrado por CPSC.
    """
    client = get_client()
    
    cpsc_filter = ""
    query_params = [bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)]
    
    if cpsc:
        cpsc_filter = "AND cpsc = @cpsc"
        query_params.append(bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc))
    
    sql = f'''
        SELECT DISTINCT pmt
        FROM `{BOM_PIECE_TABLE}`
        WHERE effectivein = @effectivein
          AND pmt IS NOT NULL
          AND TRIM(pmt) != ''
          {cpsc_filter}
        ORDER BY pmt ASC
    '''
    
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df['pmt'].dropna().astype(str).tolist()


def get_partnumber_list(effectivein: str, q: str = None) -> list[str]:
    """
    Retorna lista de part numbers únicos para popular o select do frontend.
    """
    client = get_client()

    filters = [
        "effectivein = @effectivein",
        "(effectiveout IS NULL OR effectiveout = '')",
        "partnumber IS NOT NULL",
        "TRIM(partnumber) != ''",
    ]
    query_params = [
        bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)
    ]

    if q:
        filters.append("LOWER(partnumber) LIKE LOWER(@q)")
        query_params.append(bigquery.ScalarQueryParameter("q", "STRING", f"%{q}%"))

    where_clause = " AND ".join(filters)

    sql = f'''
        SELECT DISTINCT partnumber
        FROM `{BOM_PIECE_TABLE}`
        WHERE {where_clause}
        ORDER BY partnumber ASC
        LIMIT 200
    '''

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df['partnumber'].dropna().astype(str).tolist()


def get_commodity_list(effectivein: str, q: str = None) -> list[dict]:
    """
    Retorna lista de commodities (cpsc + nome) únicas.
    """
    client = get_client()

    filters = [
        "effectivein = @effectivein",
        "(effectiveout IS NULL OR effectiveout = '')",
        "cpsc IS NOT NULL",
        "TRIM(cpsc) != ''",
    ]
    query_params = [
        bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)
    ]

    if q:
        filters.append("(LOWER(CAST(cpsc AS STRING)) LIKE LOWER(@q) OR LOWER(cpsc_name) LIKE LOWER(@q))")
        query_params.append(bigquery.ScalarQueryParameter("q", "STRING", f"%{q}%"))

    where_clause = " AND ".join(filters)

    sql = f'''
        SELECT DISTINCT
            cpsc,
            cpsc_name
        FROM `{BOM_PIECE_TABLE}`
        WHERE {where_clause}
        ORDER BY cpsc ASC
        LIMIT 200
    '''

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    df = client.query(sql, job_config=job_config).to_dataframe()

    results = []
    for _, row in df.iterrows():
        results.append({
            "cpsc": str(row['cpsc']) if row['cpsc'] else None,
            "name": str(row['cpsc_name']) if row['cpsc_name'] else None
        })
    return results


def get_vehicleline_list(effectivein: str, q: str = None) -> list[str]:
    """
    Retorna lista de vehicle lines únicos.
    """
    client = get_client()

    filters = [
        "effectivein = @effectivein",
        "(effectiveout IS NULL OR effectiveout = '')",
        "vehicleline IS NOT NULL",
        "TRIM(vehicleline) != ''",
    ]
    query_params = [
        bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)
    ]

    if q:
        filters.append("LOWER(vehicleline) LIKE LOWER(@q)")
        query_params.append(bigquery.ScalarQueryParameter("q", "STRING", f"%{q}%"))

    where_clause = " AND ".join(filters)

    sql = f'''
        SELECT DISTINCT vehicleline
        FROM `{BOM_PIECE_TABLE}`
        WHERE {where_clause}
        ORDER BY vehicleline ASC
        LIMIT 200
    '''

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df['vehicleline'].dropna().astype(str).tolist()


def get_dropdown_data(effectivein: str) -> dict:
    """
    Retorna partnumbers, commodities e vehicle lines em uma única query BigQuery.
    """
    client = get_client()

    sql = f'''
        SELECT DISTINCT
            partnumber,
            cpsc,
            cpsc_name,
            vehicleline
        FROM `{BOM_PIECE_TABLE}`
        WHERE effectivein = @effectivein
          AND (effectiveout IS NULL OR effectiveout = '')
        LIMIT 500
    '''

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)
        ]
    )

    df = client.query(sql, job_config=job_config).to_dataframe()

    partnumbers = sorted({
        str(v) for v in df['partnumber'].dropna() if str(v).strip()
    })

    commodities_seen: dict[str, str | None] = {}
    for _, row in df.iterrows():
        cpsc = str(row['cpsc']) if row['cpsc'] and str(row['cpsc']).strip() else None
        name = str(row['cpsc_name']) if row['cpsc_name'] and str(row['cpsc_name']).strip() else None
        if cpsc and cpsc not in commodities_seen:
            commodities_seen[cpsc] = name
    commodities = [
        {"cpsc": k, "name": v} for k, v in sorted(commodities_seen.items())
    ]

    vehicle_lines = sorted({
        str(v) for v in df['vehicleline'].dropna() if str(v).strip()
    })

    return {
        "partnumbers": partnumbers,
        "commodities": commodities,
        "vehicle_lines": vehicle_lines,
    }


def get_tooling_cost_metrics(effectivein: str, cpsc: str = None, pmt_code: str = None) -> dict:
    """
    Retorna métricas de custos de tooling.
    """
    try:
        client = get_client()

        resolved_pmt = resolve_pmt(pmt_code, "cost") if pmt_code else None
        effective_pmt = resolved_pmt or pmt_code

        filters = [
            "effectivein = @effectivein",
            "(effectiveout IS NULL OR effectiveout = '')"
        ]
        query_params = [
            bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein)
        ]

        if cpsc:
            filters.append("cpsc = @cpsc")
            query_params.append(bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc))

        if effective_pmt:
            filters.append("pmt = @pmt_code")
            query_params.append(bigquery.ScalarQueryParameter("pmt_code", "STRING", effective_pmt))

        where_clause = " AND ".join(filters)

        sql = f'''
            SELECT
                partnumber,
                program,
                vehicleline,
                pmt,
                cpsc,
                cpsc_name AS commodityname,
                plant AS costplant,
                funding_source AS source_reference,
                actual_tooling_cost,
                currency,
                target_tooling_cost,
                target_currency,
                (SAFE_CAST(actual_tooling_cost AS FLOAT64) - SAFE_CAST(target_tooling_cost AS FLOAT64)) AS gap,
                '["' || effectivein || '"]' AS effectivein_json
            FROM `{BOM_TOOLING_TABLE}`
            WHERE {where_clause}
              AND SAFE_CAST(actual_tooling_cost AS FLOAT64) > 0
            ORDER BY cpsc, partnumber
        '''

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()

        if df.empty:
            return {
                "cost_type": "tooling",
                "total_records": 0,
                "total_cost": 0,
                "data": []
            }

        import math

        def _safe_float(val):
            try:
                f = float(val)
                return 0 if math.isnan(f) else f
            except (TypeError, ValueError):
                return 0

        records = []
        for _, row in df.iterrows():
            records.append({
                "partnumber": str(row['partnumber']) if row['partnumber'] else None,
                "program": str(row['program']) if row['program'] else None,
                "vehicleline": str(row['vehicleline']) if row['vehicleline'] else None,
                "pmt": str(row['pmt']) if row['pmt'] else None,
                "cpsc": str(row['cpsc']) if row['cpsc'] else None,
                "cpsc_name": str(row['commodityname']) if row['commodityname'] else None,
                "costplant": str(row['costplant']) if row['costplant'] else None,
                "source_reference": str(row['source_reference']) if row['source_reference'] else None,
                "actual_tooling_cost": _safe_float(row['actual_tooling_cost']),
                "currency": str(row['currency']) if row['currency'] else None,
                "target_tooling_cost": _safe_float(row['target_tooling_cost']),
                "target_currency": str(row['target_currency']) if row['target_currency'] else None,
                "gap": _safe_float(row['gap']),
                "effectivein_json": str(row['effectivein_json']) if row['effectivein_json'] else None,
            })

        total_cost = sum(_safe_float(row['actual_tooling_cost']) for _, row in df.iterrows())

        return {
            "cost_type": "tooling",
            "total_records": len(records),
            "total_cost": _safe_float(total_cost),
            "data": records
        }

    except Exception as e:
        print(f"Failed to retrieve tooling-cost metrics: {str(e)}")
        return {"error": str(e)}


def get_piece_cost_metrics(effectivein: str, partnumber: str = None, cpsc: str = None, pmt_code: str = None) -> dict:
    """
    Retorna métricas de custos de peça (piece cost).
    """
    try:
        client = get_client()

        resolved_pmt = resolve_pmt(pmt_code, "cost") if pmt_code else None
        effective_pmt = resolved_pmt or pmt_code

        filters = [
            "effectivein = @effectivein",
            "(effectiveout IS NULL OR effectiveout = '')"
        ]
        query_params = [
            bigquery.ScalarQueryParameter("effectivein", "STRING", effectivein),
        ]

        if partnumber:
            filters.append("partnumber = @partnumber")
            query_params.append(bigquery.ScalarQueryParameter("partnumber", "STRING", partnumber))

        if cpsc:
            filters.append("cpsc = @cpsc")
            query_params.append(bigquery.ScalarQueryParameter("cpsc", "STRING", cpsc))

        if effective_pmt:
            filters.append("pmt = @pmt_code")
            query_params.append(bigquery.ScalarQueryParameter("pmt_code", "STRING", effective_pmt))

        where_clause = " AND ".join(filters)

        sql = f'''
            SELECT
                program,
                vehicleline,
                effectivein,
                effectiveout,
                pmt,
                partnumber,
                cpsc,
                cpsc_name,
                actual_piece_cost,
                currency,
                target_piece_cost,
                target_currency,
                (SAFE_CAST(actual_piece_cost AS FLOAT64) - SAFE_CAST(target_piece_cost AS FLOAT64)) AS gap,
                source_reference
            FROM `{BOM_PIECE_TABLE}`
            WHERE {where_clause}
              AND SAFE_CAST(actual_piece_cost AS FLOAT64) > 0
            ORDER BY cpsc, partnumber
        '''

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        df = client.query(sql, job_config=job_config).to_dataframe()

        if df.empty:
            return {
                "effectivein": effectivein,
                "partnumber": partnumber if partnumber else None,
                "cpsc": cpsc,
                "pmt_code": pmt_code,
                "cost_type": "piece",
                "total_records": 0,
                "total_cost": 0,
                "data": []
            }
        
        import math

        def _safe_float(val):
            try:
                f = float(val)
                return 0 if math.isnan(f) else f
            except (TypeError, ValueError):
                return 0

        # Convert BigQuery rows into the stable API response shape.
        records = []
        for _, row in df.iterrows():
            records.append({
                "program": str(row['program']) if row['program'] else None,
                "vehicleline": str(row['vehicleline']) if row['vehicleline'] else None,
                "effectivein": str(row['effectivein']) if row['effectivein'] else None,
                "effectiveout": str(row['effectiveout']) if row['effectiveout'] else None,
                "pmt": str(row['pmt']) if row['pmt'] else None,
                "partnumber": str(row['partnumber']) if row['partnumber'] else None,
                "cpsc": str(row['cpsc']) if row['cpsc'] else None,
                "cpsc_name": str(row['cpsc_name']) if row['cpsc_name'] else None,
                "actual_piece_cost": _safe_float(row['actual_piece_cost']),
                "currency": str(row['currency']) if row['currency'] else None,
                "target_piece_cost": _safe_float(row['target_piece_cost']),
                "target_currency": str(row['target_currency']) if row['target_currency'] else None,
                "gap": _safe_float(row['gap']),
                "source_reference": str(row['source_reference']) if row['source_reference'] else None
            })

        total_cost = sum(_safe_float(row['actual_piece_cost']) for _, row in df.iterrows())
        
        return {
            "effectivein": effectivein,
            "partnumber": partnumber,
            "cpsc": cpsc,
            "pmt_code": pmt_code,
            "cost_type": "piece",
            "total_records": len(records),
            "total_cost": _safe_float(total_cost),
            "data": records
        }

    except Exception as e:
        print(f"Failed to retrieve piece-cost metrics: {str(e)}")
        return {"error": str(e), "effectivein": effectivein}


def get_combined_cost_metrics(effectivein: str, cpsc: str = None, pmt_code: str = None) -> dict:
    """
    Retorna métricas combinadas de tooling e piece cost.
    """
    tooling_metrics = get_tooling_cost_metrics(effectivein, cpsc, pmt_code)
    piece_metrics = get_piece_cost_metrics(effectivein, partnumber=None, cpsc=cpsc, pmt_code=pmt_code)
    
    return {
        "effectivein": effectivein,
        "cpsc": cpsc,
        "pmt_code": pmt_code,
        "tooling_cost": tooling_metrics,
        "piece_cost": piece_metrics,
        "summary": {
            "total_tooling_cost": tooling_metrics.get("total_cost", 0),
            "total_piece_cost": piece_metrics.get("total_cost", 0),
            "grand_total_cost": tooling_metrics.get("total_cost", 0) + piece_metrics.get("total_cost", 0),
            "total_tooling_records": tooling_metrics.get("total_records", 0),
            "total_piece_records": piece_metrics.get("total_records", 0)
        }
    }
