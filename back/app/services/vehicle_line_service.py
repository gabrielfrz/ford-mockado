"""Query vehicle-line filters, program metadata, and milestone summaries."""

import pandas as pd
from app.schemas.vehicle_line import VehicleLineSchema
from app.services.bigquery_client import get_client

EXTRA_COLS = [
    "mr","ps","psc","fpd","fc1","fc2","fc3","fc4","fc5",
    "k3","k5","upv0","upv1","upv2","pa","fdj","dcv","pec","fec","lr","ls","j1",
    "oktb","fsr","faa","ept","ept_ipd","tt_ipd","tt","pp","mp1","mp2","_pcf1",
    "_tcb1","_tcb2","tmr","tps","tsc","tdc","ttc","tdj","tpv","unv0","unv1",
    "unv2","xm","aa1","vp","_dtm",
]


# Helpers
def _as_none(value: object):
    """Convert blank and pandas-style missing values to ``None``."""
    if value is None:
        return None
    s = str(value).strip()
    return None if s == "" or s.lower() in ("nan", "none", "nat") else s


def _clean(value: object) -> str:
    """Convert blank values to the display placeholder used by the API."""
    if value is None:
        return "-"
    s = str(value).strip()
    if s == "" or s.lower() in ("nan", "none", "nat"):
        return "-"
    return s

def _format_date(value):
    """Format date-like values as MM/DD/YYYY and preserve other values."""
    if value is None:
        return None

    try:
        # Coerce supported date-like values while preserving non-dates.
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return value
        return dt.strftime("%m/%d/%Y")
    except Exception:
        return value


# Autocomplete functions

def get_model_years(query: str = "") -> list[str]:
    """Return distinct model years matching an optional search term."""
    client = get_client()
    sql = f"""
        SELECT DISTINCT SAFE_CAST(vpp001_veh_mdl_yr AS FLOAT64) AS model_year
        FROM `{client.project}.DANDR_DEV.vehicle_line`
        WHERE SAFE_CAST(vpp001_veh_mdl_yr AS FLOAT64) IS NOT NULL
        ORDER BY model_year
    """
    years = {f"{float(row.model_year):g}" for row in client.query(sql).result()}
    if query:
        normalized_query = query.strip().lower()
        years = {year for year in years if normalized_query in year.lower()}
    return sorted(years, key=float)


def get_program_names(model_year: str = "", query: str = "") -> list[str]:
    """Return program names for an optional model year and search term."""
    try:
        client = get_client()
        
        where_clauses = []
        
        if model_year:
            where_clauses.append(f"SAFE_CAST(vpp001_veh_mdl_yr AS FLOAT64) = {model_year}")
        
        if query:
            where_clauses.append(f"LOWER(vpp001_gi_prod_pgm_ds) LIKE '%{query.lower()}%'")
        else:
            where_clauses.append("1=1")  # Preserve an unrestricted name query.
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        sql = f'''
            SELECT DISTINCT vpp001_gi_prod_pgm_ds
            FROM `{client.project}.DANDR_DEV.vehicle_line`
            WHERE {where_clause}
            ORDER BY vpp001_gi_prod_pgm_ds ASC
        '''
        
        print(f"Query: {sql}")  # Debug
        df = client.query(sql).to_dataframe()
        result = df["vpp001_gi_prod_pgm_ds"].tolist()
        print(f"Result: {result}")  # Debug
        return result
    except Exception as e:
        import traceback
        print(f"Failed to retrieve program names: {str(e)}")
        traceback.print_exc()
        return []


def get_program_codes(model_year: str = "", program_name: str = "", query: str = "") -> list[str]:
    """Return project descriptions for the supplied vehicle-line filters."""
    try:
        client = get_client()
        
        where_clauses = []
        
        if model_year:
            where_clauses.append(f"SAFE_CAST(vpp001_veh_mdl_yr AS FLOAT64) = {model_year}")
        
        if program_name:
            clean_program_name = program_name.replace('"', '').lower()
            where_clauses.append(f"LOWER(vpp001_gi_prod_pgm_ds) LIKE '%{clean_program_name}%'")
        # A program name is optional so project descriptions can load independently.
        
        if query:
            clean_query = query.replace('"', '').lower()
            where_clauses.append(f"LOWER(vpp001_gi_prj_ds) LIKE '%{clean_query}%'")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        sql = f'''
            SELECT DISTINCT vpp001_gi_prj_ds
            FROM `{client.project}.DANDR_DEV.vehicle_line`
            WHERE {where_clause}
            ORDER BY vpp001_gi_prj_ds ASC
        '''
        
        print(f"Query: {sql}")  # Debug
        df = client.query(sql).to_dataframe()
        result = df["vpp001_gi_prj_ds"].tolist()
        print(f"Result: {result}")  # Debug
        return result
    except Exception as e:
        import traceback
        print(f"Failed to retrieve program codes: {str(e)}")
        traceback.print_exc()
        return []


# Main Summary Function

def get_vehicle_line_summary(
    model_year: str,
    program_names: str,
    program_codes: str,
    selected_index: int | None = None
) -> VehicleLineSchema:
    """Return the selected vehicle-line summary and normalized milestones."""

    try:
        client = get_client()
        
        where_clauses = []
        
        if model_year:
            # Model year is an exact numeric match.
            where_clauses.append(f"SAFE_CAST(vpp001_veh_mdl_yr AS INT64) = {int(float(model_year))}")
        
        if program_names:
            # Program name uses a case-insensitive partial match.
            clean_program_names = program_names.replace('"', '').lower()
            where_clauses.append(f"LOWER(vpp001_gi_prod_pgm_ds) LIKE '%{clean_program_names}%'")
        
        if program_codes:
            # Project description uses an exact normalized match.
            clean_program_codes = program_codes.replace('"', '').lower()
            # Normalize whitespace after removing punctuation in SQL.
            normalized_input = clean_program_codes.strip()
            normalized_input = ' '.join(normalized_input.split())
            where_clauses.append(f"REGEXP_REPLACE(LOWER(vpp001_gi_prj_ds), r'[^a-z0-9 ]', '') = '{normalized_input}'")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        sql = f'''
            SELECT *
            FROM `{client.project}.DANDR_DEV.vehicle_line`
            WHERE {where_clause}
            ORDER BY vpp001_veh_mdl_yr, vpp001_veh_nm_plte_nm ASC
        '''
        
        print(f"\n=== DEBUG QUERY ===")
        print(f"model_year: {model_year}")
        print(f"program_names: {program_names}")
        print(f"program_codes: {program_codes}")
        print(f"Query: {sql}")
        print(f"================\n")
        
        df = client.query(sql).to_dataframe()
        print(f"Rows returned: {len(df)}")
        
        if df.empty:
            print("WARNING: No vehicle-line rows were found.")
            raise ValueError("No vehicle-line data matched the supplied filters.")
        
        if selected_index is not None:
            if selected_index < 0 or selected_index >= len(df):
                raise IndexError("Invalid row index")
            row = df.iloc[selected_index]
        else:
            row = df.iloc[0]
        
        # Core program metadata
        program_code = _clean(row.get("vpp001_gi_prj_ds"))  # PROGRAM CODE
        gi_code = _clean(row.get("vpp001_gi_prj_id"))  # GI CODE
        program_name = _clean(row.get("vpp001_gi_prod_pgm_ds"))  # PROGRAM NAME
        ptvl = _clean(row.get("vpp001_engnrng_ptvl_cd"))
        ptvl_desc = _clean(row.get("vpp001_engnrng_ptvl_ds"))
        eff_point = _clean(row.get("vpp001_prj_eff_in_pnt_cd"))
        vehicle_np = _clean(row.get("vpp001_veh_nm_plte_nm"))
        model_year_val = _clean(row.get("vpp001_veh_mdl_yr"))
        plant_code_val = _clean(row.get("plant_code"))
        plant_name_val = _clean(row.get("plant_name"))
        wers_plant_val = _clean(row.get("wers_plant"))

        summary = (
            f"GI Code: {gi_code} | "
            f"Project Description: {program_code} | "
            f"PTVL: {ptvl} | "
            f"PTVL Description: {ptvl_desc} | "
            f"Program Name: {program_name} | "
            f"Effective Point: {eff_point} | "
            f"Vehicle Nameplate: {vehicle_np} | "
            f"Model Year: {model_year_val}"
        )

        # Milestones
        milestones = {}
        for col in EXTRA_COLS:
            raw_val = _as_none(row.get(col))
            milestones[col] = _format_date(raw_val)

        return VehicleLineSchema(
            program_code=program_code,
            gi_code=gi_code if gi_code != "-" else None,
            model_year=int(float(model_year_val)) if model_year_val != "-" else int(float(model_year)),
            vehicle_line=program_name,
            affected_plant=ptvl_desc,
            plant_code=plant_code_val if plant_code_val != "-" else None,
            plant_name=plant_name_val if plant_name_val != "-" else None,
            wers_plant=wers_plant_val if wers_plant_val != "-" else None,
            effective_point_code=eff_point if eff_point != "-" else None,
            summary=summary,
            effective_point={"effective_point": eff_point} if eff_point != "-" else None,
            milestones=milestones,
        )
    except Exception as e:
        print(f"Failed to retrieve the vehicle-line summary: {str(e)}")
        import traceback
        traceback.print_exc()
