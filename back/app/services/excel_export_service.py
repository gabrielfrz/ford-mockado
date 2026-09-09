"""Generate styled Excel workbooks for dashboard deliverable exports."""

import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from app.services.bigquery_client import get_client
from google.cloud import bigquery
from io import BytesIO
from app.services.dvp_glidepath_service import get_dvp_glidepath_data, get_dvp_glidepath_aggregated_data
from fastapi.responses import StreamingResponse
import pandas as pd


def export_dvp_team_assessment_excel(
    gi_id: str,
    dvp_team: str = None,
    pmt_code: str = None,
    snapshot_date: str = None,
) -> tuple[BytesIO, str]:
    """
    Export DVP Team assessment data to Excel format with professional styling.
    
    Layout:
    - Line 1: Merged header (A1:C1) - DVP TEAM ASSESSMENT REPORT
    - Line 2: GI ID info
    - Line 3: Extraction Date
    - Line 5: Metrics summary
    - Line 7+: Data table with CPSC, DVP Team, Status
    
    Args:
        gi_id: GI ID for filtering results (required)
        dvp_team: Optional DVP Team name to filter (if None, returns all teams)
        pmt_code: Optional canonical PMT code
        snapshot_date: Optional weekly snapshot date
    
    Returns:
        Tuple of (BytesIO, filename)
    
    Raises:
        ValueError: If gi_id is empty
        Exception: If BigQuery query fails
    """
    if not gi_id or not gi_id.strip():
        raise ValueError("gi_id parameter is required")
    
    client = get_client()
    from app.services.fede_status_service import _pmt_predicate

    dvp_team_filter = "AND dvp_team = @dvp_team" if dvp_team else ""
    pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
    
    is_mock_date = False
    mock_modifier = 0
    if snapshot_date and snapshot_date.startswith("2026"):
        is_mock_date = True
        mock_modifier = int(snapshot_date.split("-")[2])
        snapshot_date = None
        
    table_name = f"`{client.project}.DANDR_DEV.dvp_weekly_snapshot`" if snapshot_date else f"`{client.project}.DANDR_DEV.dvp_fede`"
    snapshot_filter = "AND snapshot_date = @snapshot_date" if snapshot_date else ""

    sql = f'''
                SELECT
                        CASE 
                                WHEN REGEXP_CONTAINS(dvp_team, r'^(\d{{6}}|\d{{2}}\.\d{{2}}\.\d{{2}})') 
                                THEN REGEXP_EXTRACT(dvp_team, r'^(\d{{6}}|\d{{2}}\.\d{{2}}\.\d{{2}})')
                                ELSE 'Other' 
                        END AS CPSC,
                        REGEXP_REPLACE(dvp_team, r'^\d+\s*-\s*', '') AS dvp_team,
                        CASE 
                                WHEN LOWER(TRIM(conformance_state)) IN ('pass', 'meet') THEN 'Meet'
                                WHEN conformance_state IS NULL OR TRIM(conformance_state) = '' THEN 'Unassessed'
                                ELSE TRIM(conformance_state)
                        END AS Status,
                        milestone_overdue,
                        milestone_date,
                        recommended_milestone,
                        requirement_id,
                        program
                FROM {table_name}
                WHERE gi_code = @gi_id
                    AND dvp_team IS NOT NULL
                    {dvp_team_filter}
                    {pmt_filter}
                    {snapshot_filter}
                ORDER BY dvp_team ASC
    '''
    
    query_params = [bigquery.ScalarQueryParameter("gi_id", "STRING", gi_id)]
    if dvp_team:
        query_params.append(bigquery.ScalarQueryParameter("dvp_team", "STRING", dvp_team))
    if pmt_code:
        query_params.append(bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code))
    if snapshot_date:
        query_params.append(bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date))

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    
    try:
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        if is_mock_date and not df.empty:
            # slightly shuffle status to mock changes
            statuses = ['Meet', 'Does Not Meet', 'Unassessed', 'Not Applicable']
            for i in range(min(mock_modifier * 5, len(df))):
                df.at[i, 'Status'] = statuses[i % len(statuses)]
                
        if df.empty:
            raise ValueError("No data found for the specified GI ID")
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "DVP Assessment"

        program_name = str(df.iloc[0]['program']) if 'program' in df.columns and df.iloc[0]['program'] else gi_id
        safe_program = str(program_name).strip()
        status_counts = df['Status'].value_counts().to_dict()
        
        # Define colors and styles
        dark_blue = "002060"
        light_gray = "D9D9D9"
        white_text = "FFFFFF"
        green_bg = "C6EFCE"
        green_text = "006100"
        red_bg = "FFC7CE"
        red_text = "9C0006"
        yellow_bg = "FFEB9C"
        brown_text = "9C6500"
        
        header_font = Font(name='Calibri', size=12, bold=True, color=white_text)
        title_font = Font(name='Calibri', size=14, bold=True, color=white_text)
        bold_font = Font(name='Calibri', size=11, bold=True)
        normal_font = Font(name='Calibri', size=11)
        green_font = Font(name='Calibri', size=11, color=green_text)
        red_font = Font(name='Calibri', size=11, color=red_text)
        brown_font = Font(name='Calibri', size=11, color=brown_text)
        
        dark_blue_fill = PatternFill(start_color=dark_blue, end_color=dark_blue, fill_type="solid")
        gray_fill = PatternFill(start_color=light_gray, end_color=light_gray, fill_type="solid")
        green_fill = PatternFill(start_color=green_bg, end_color=green_bg, fill_type="solid")
        red_fill = PatternFill(start_color=red_bg, end_color=red_bg, fill_type="solid")
        yellow_fill = PatternFill(start_color=yellow_bg, end_color=yellow_bg, fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
        left_alignment = Alignment(horizontal='left', vertical='center', wrap_text=False)
        
        ws.merge_cells('A1:G1')
        cell_header = ws['A1']
        cell_header.value = 'DVP TEAM ASSESSMENT\nASSESSMENT REPORT'
        cell_header.font = title_font
        cell_header.fill = dark_blue_fill
        cell_header.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.row_dimensions[1].height = 35
        
        ws['A2'] = f'GI ID: {gi_id}'
        ws['A2'].font = bold_font
        ws['A2'].alignment = left_alignment
        
        ws['A3'] = f'Extraction Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        ws['A3'].font = normal_font
        ws['A3'].alignment = left_alignment
        
        # Line 4: Metrics Summary
        metrics_parts = []
        for status in sorted(status_counts.keys()):
            metrics_parts.append(f'Total {status}: {status_counts[status]}')
        
        ws.merge_cells('A5:G5')
        ws['A5'] = ' | '.join(metrics_parts)
        ws['A5'].font = bold_font
        metrics_alignment = Alignment(horizontal='left', vertical='center', wrap_text=False)
        ws['A5'].alignment = metrics_alignment
        
        headers = ['Req ID', 'Status', 'Milestone Overdue', 'Milestone Date', 'Rec. Milestone', 'DVP Team', 'CPSC']
        header_row = 7
        
        # Alignment for data rows with wrap text
        center_alignment_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left_alignment_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = gray_fill
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
            cell.alignment = header_alignment
            cell.border = thin_border
        
        data_row = 8
        for _, row in df.iterrows():
            # Column 1: Req ID
            cell = ws.cell(row=data_row, column=1)
            cell.value = str(row['requirement_id']) if pd.notna(row['requirement_id']) else ''
            cell.font = normal_font
            cell.alignment = center_alignment_wrap
            cell.border = thin_border

            # Column 2: Status
            cell = ws.cell(row=data_row, column=2)
            cell.value = row['Status']
            if row['Status'] == 'Meet':
                cell.font = green_font
                cell.fill = green_fill
            elif row['Status'] == 'Unassessed':
                cell.font = red_font
                cell.fill = red_fill
            elif row['Status'] == 'Approved Deviation':
                cell.font = brown_font
                cell.fill = yellow_fill
            else:
                cell.font = normal_font
            cell.alignment = center_alignment_wrap
            cell.border = thin_border

            # Column 3: Milestone Overdue (Yes/No)
            cell = ws.cell(row=data_row, column=3)
            cell.value = 'Yes' if row['milestone_overdue'] else 'No'
            cell.font = normal_font
            cell.alignment = center_alignment_wrap
            cell.border = thin_border

            # Column 4: Milestone Date
            cell = ws.cell(row=data_row, column=4)
            cell.value = str(row['milestone_date']) if pd.notna(row['milestone_date']) else ''
            cell.font = normal_font
            cell.alignment = left_alignment_wrap
            cell.border = thin_border

            # Column 5: Recommended Milestone
            cell = ws.cell(row=data_row, column=5)
            cell.value = str(row['recommended_milestone']) if pd.notna(row['recommended_milestone']) else ''
            cell.font = normal_font
            cell.alignment = left_alignment_wrap
            cell.border = thin_border

            # Column 6: DVP Team — remove numeric prefix
            dvp_team_raw = str(row['dvp_team']) if row['dvp_team'] is not None else ''
            dvp_team_clean = re.sub(r'^\d+\s*-\s*', '', dvp_team_raw)
            cell = ws.cell(row=data_row, column=6)
            cell.value = dvp_team_clean
            cell.font = normal_font
            cell.alignment = left_alignment_wrap
            cell.border = thin_border

            # Column 7: CPSC
            cell = ws.cell(row=data_row, column=7)
            cell.value = row['CPSC']
            cell.font = normal_font
            cell.alignment = center_alignment_wrap
            cell.border = thin_border

            data_row += 1
        
        ws.column_dimensions['A'].width = 20  # Req ID
        ws.column_dimensions['B'].width = 25  # Status
        ws.column_dimensions['C'].width = 18  # Milestone Overdue
        ws.column_dimensions['D'].width = 18  # Milestone Date
        ws.column_dimensions['E'].width = 18  # Rec. Milestone
        ws.column_dimensions['F'].width = 70  # DVP Team
        ws.column_dimensions['G'].width = 15  # CPSC
        
        ws.auto_filter.ref = f'A7:G{data_row - 1}'
        
        ws.freeze_panes = 'A8'
        
        # Save to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        filename = f"DVP_Report_{safe_program}.xlsx" if not dvp_team else f"DVP_Report_{safe_program}_{str(dvp_team).strip()}.xlsx"
        return excel_buffer, filename
        
    except Exception as e:
        raise Exception(f"Error generating Excel: {str(e)}")


def export_cae_status_excel(gi_id: str, pmt_code: str = None) -> BytesIO:
    """
    Export CAE status data to Excel format with professional styling.
    
    Layout:
    - Line 1: Merged header (A1:D1) - CAE STATUS REPORT
    - Line 2: Vehicle Line info
    - Line 3: GI ID and Extraction Date
    - Line 5: Metrics summary
    - Line 7+: Data table with CPSC, Assessment Name, Status, Program
    
    Args:
        gi_id: GI ID for filtering results (required)
    
    Returns:
        BytesIO object containing Excel file
    
    Raises:
        ValueError: If gi_id is empty
        Exception: If BigQuery query fails
    """
    if not gi_id or not gi_id.strip():
        raise ValueError("gi_id parameter is required")
    
    client = get_client()
    from app.services.fede_status_service import _pmt_predicate
    pmt_filter = f"AND {_pmt_predicate('pmt_code')}" if pmt_code else ""
    
    sql = f'''
    WITH base AS (
      SELECT gi_code, program, dvp_team, conformance_state, prototype_type,
        REGEXP_EXTRACT(dvp_team, r'^(\d{{2}}\.\d{{2}}\.\d{{2}})') AS _cpsc_dotted,
        REGEXP_EXTRACT(dvp_team, r'^(\d+)') AS _cpsc_numeric
      FROM `{client.project}.DANDR_DEV.dvp_fede`
      WHERE gi_code = @gi_id
                {pmt_filter}
        AND REGEXP_CONTAINS(UPPER(prototype_type), r'CAE')
        AND conformance_state IS NOT NULL AND TRIM(conformance_state) != ''
    )
    SELECT program AS Program,
      (CASE 
        WHEN _cpsc_dotted IS NOT NULL THEN _cpsc_dotted
        WHEN _cpsc_numeric IS NOT NULL AND LENGTH(_cpsc_numeric) = 6 THEN _cpsc_numeric
        WHEN REGEXP_CONTAINS(SPLIT(SPLIT(dvp_team, ' - ')[OFFSET(0)], ' ')[OFFSET(0)], r'^\d+(\.\d+)*$')
        THEN SPLIT(SPLIT(dvp_team, ' - ')[OFFSET(0)], ' ')[OFFSET(0)]
        ELSE 'Other CPSC'
      END) AS CPSC,
      dvp_team AS Assessment_Name, conformance_state AS Status
    FROM base ORDER BY CPSC, dvp_team
    '''
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("gi_id", "STRING", gi_id),
            *(
                [bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code)]
                if pmt_code
                else []
            ),
        ]
    )
    
    try:
        df = client.query(sql, job_config=job_config).to_dataframe()
        
        if df.empty:
            raise ValueError("No data found for the specified GI ID")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "CAE Status"
        
        program_name = df.iloc[0]['Program']
        safe_program = str(program_name).strip() if program_name else gi_id
        status_counts = df['Status'].value_counts().to_dict()
        
        dark_blue = "002060"
        light_gray = "D9D9D9"
        white_text = "FFFFFF"
        green_bg = "C6EFCE"
        green_text = "006100"
        red_bg = "FFC7CE"
        red_text = "9C0006"
        yellow_bg = "FFEB9C"
        brown_text = "9C6500"
        
        header_font = Font(name='Calibri', size=12, bold=True, color=white_text)
        title_font = Font(name='Calibri', size=14, bold=True, color=white_text)
        bold_font = Font(name='Calibri', size=11, bold=True)
        normal_font = Font(name='Calibri', size=11)
        green_font = Font(name='Calibri', size=11, color=green_text)
        red_font = Font(name='Calibri', size=11, color=red_text)
        brown_font = Font(name='Calibri', size=11, color=brown_text)
        
        dark_blue_fill = PatternFill(start_color=dark_blue, end_color=dark_blue, fill_type="solid")
        gray_fill = PatternFill(start_color=light_gray, end_color=light_gray, fill_type="solid")
        green_fill = PatternFill(start_color=green_bg, end_color=green_bg, fill_type="solid")
        red_fill = PatternFill(start_color=red_bg, end_color=red_bg, fill_type="solid")
        yellow_fill = PatternFill(start_color=yellow_bg, end_color=yellow_bg, fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
        left_alignment = Alignment(horizontal='left', vertical='center', wrap_text=False)
        
        ws.merge_cells('A1:D1')
        cell_header = ws['A1']
        cell_header.value = 'CAE STATUS\nCAE STATUS REPORT'
        cell_header.font = title_font
        cell_header.fill = dark_blue_fill
        cell_header.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.row_dimensions[1].height = 35
        
        ws['A2'] = f'Vehicle Line: {program_name}'
        ws['A2'].font = bold_font
        ws['A2'].alignment = left_alignment
        
        ws['A3'] = f'GI ID: {gi_id}'
        ws['A3'].font = normal_font
        ws['A3'].alignment = left_alignment
        ws['C3'] = f'Extraction Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        ws['C3'].font = normal_font
        ws['C3'].alignment = left_alignment
        
        metrics_parts = []
        for status in sorted(status_counts.keys()):
            metrics_parts.append(f'Total {status}: {status_counts[status]}')
        
        ws.merge_cells('A5:D5')
        ws['A5'] = ' | '.join(metrics_parts)
        ws['A5'].font = bold_font
        metrics_alignment = Alignment(horizontal='left', vertical='center', wrap_text=False)
        ws['A5'].alignment = metrics_alignment
        
        headers = ['CPSC', 'Assessment Name', 'Status', 'Program']
        header_row = 7
        
        center_alignment_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left_alignment_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = gray_fill
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
            cell.alignment = header_alignment
            cell.border = thin_border
        
        data_row = 8
        for _, row in df.iterrows():
            cell = ws.cell(row=data_row, column=1)
            cell.value = row['CPSC']
            cell.font = normal_font
            cell.alignment = center_alignment_wrap
            cell.border = thin_border
            
            cell = ws.cell(row=data_row, column=2)
            cell.value = row['Assessment_Name']
            cell.font = normal_font
            cell.alignment = left_alignment_wrap
            cell.border = thin_border
            
            cell = ws.cell(row=data_row, column=3)
            cell.value = row['Status']
            
            if row['Status'] == 'Meet':
                cell.font = green_font
                cell.fill = green_fill
            elif row['Status'] == 'Unassessed':
                cell.font = red_font
                cell.fill = red_fill
            elif row['Status'] == 'Approved Deviation':
                cell.font = brown_font
                cell.fill = yellow_fill
            else:
                cell.font = normal_font
            
            cell.alignment = center_alignment_wrap
            cell.border = thin_border
            
            cell = ws.cell(row=data_row, column=4)
            cell.value = row['Program']
            cell.font = normal_font
            cell.alignment = left_alignment_wrap
            cell.border = thin_border
            
            data_row += 1
        
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 70
        ws.column_dimensions['C'].width = 25
        ws.column_dimensions['D'].width = 40
        
        ws.auto_filter.ref = f'A7:D{data_row - 1}'
        ws.freeze_panes = 'A8'
        
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        filename = f"CAE_Report_{safe_program}.xlsx"
        return excel_buffer, filename
        
    except Exception as e:
        raise Exception(f"Error generating Excel: {str(e)}")


def export_design_rule_excel(
    model_year: str,
    program_name: str,
    pmt_code: str = None,
) -> tuple[BytesIO, str]:
    """
    Export Design Rule classification data to Excel format with professional styling.

    Layout:
    - Row 1: Merged header - DESIGN RULE CLASSIFICATION REPORT
    - Row 2: Program info
    - Row 3: Model Year and Extraction Date
    - Row 5: Metrics summary (Applicable | Carryover | Not Applicable | Unclassified | Total)
    - Row 7+: Data table with Classification and Explanation columns

    Args:
        model_year: Model year for filtering (required)
        program_name: Program name for filtering via dr_pk2 prefix match (required)

    Returns:
        Tuple of (BytesIO, filename)

    Raises:
        ValueError: If model_year or program_name is empty, or no data is found
        Exception: If BigQuery query fails
    """
    if not model_year or not str(model_year).strip():
        raise ValueError("model_year parameter is required")
    if not program_name or not program_name.strip():
        raise ValueError("program_name parameter is required")

    from app.services.fede_status_service import (
        _build_dr_prefix_candidates,
        _normalize_program_tokens,
        _pmt_predicate,
        _row_pmt_expression,
    )

    client = get_client()

    model_year_clean = str(model_year).strip().split(".")[0]
    tokens = _normalize_program_tokens(program_name.strip())

    if not tokens:
        raise ValueError(f"program_name '{program_name}' could not be parsed into search tokens")

    prefix_candidates = _build_dr_prefix_candidates(model_year_clean, tokens)
    pmt_filter = (
        f"AND {_pmt_predicate(_row_pmt_expression('t'))}"
        if pmt_code
        else ""
    )

    sql = f'''
        SELECT
          REGEXP_EXTRACT(t.dr_pk2, r'^(\\d{{4}})') AS model_year,
          REGEXP_EXTRACT(t.dr_pk2, r'^\\d{{4}}(?:\\.\\d+)?[_\\s](.*?)(?::|$)') AS program_name,
          t.classified AS classification,
          t.classification_explanation AS explanation
        FROM `{client.project}.DANDR_DEV.dr_design_rule` t
        WHERE STARTS_WITH(
          LOWER(REPLACE(t.dr_pk2, \' \', \'_\')),
          LOWER(@dr_pk2_prefix)
        )
                {pmt_filter}
        ORDER BY t.classified, t.classification_explanation
    '''

    df = None
    matched_prefix = None
    for prefix in prefix_candidates:
        result = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("dr_pk2_prefix", "STRING", prefix),
                    *(
                        [bigquery.ScalarQueryParameter("pmt_code", "STRING", pmt_code)]
                        if pmt_code
                        else []
                    ),
                ]
            )
        ).to_dataframe()
        if not result.empty:
            df = result
            matched_prefix = prefix
            break

    if df is None or df.empty:
        raise LookupError(f"No design rule data found for model_year='{model_year_clean}' and program_name='{program_name}'")

    wb = Workbook()
    ws = wb.active
    ws.title = "Design Rule"

    dark_blue = "002060"
    light_gray = "D9D9D9"
    white_text = "FFFFFF"
    green_bg = "C6EFCE"
    green_text = "006100"
    yellow_bg = "FFEB9C"
    brown_text = "9C6500"
    red_bg = "FFC7CE"
    red_text = "9C0006"
    blue_bg = "DDEEFF"
    blue_text = "003478"

    title_font = Font(name="Calibri", size=14, bold=True, color=white_text)
    header_font = Font(name="Calibri", size=12, bold=True, color=white_text)
    bold_font = Font(name="Calibri", size=11, bold=True)
    normal_font = Font(name="Calibri", size=11)
    green_font = Font(name="Calibri", size=11, color=green_text)
    brown_font = Font(name="Calibri", size=11, color=brown_text)
    red_font = Font(name="Calibri", size=11, color=red_text)
    blue_font = Font(name="Calibri", size=11, color=blue_text)

    dark_blue_fill = PatternFill(start_color=dark_blue, end_color=dark_blue, fill_type="solid")
    gray_fill = PatternFill(start_color=light_gray, end_color=light_gray, fill_type="solid")
    green_fill = PatternFill(start_color=green_bg, end_color=green_bg, fill_type="solid")
    yellow_fill = PatternFill(start_color=yellow_bg, end_color=yellow_bg, fill_type="solid")
    red_fill = PatternFill(start_color=red_bg, end_color=red_bg, fill_type="solid")
    blue_fill = PatternFill(start_color=blue_bg, end_color=blue_bg, fill_type="solid")

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    center_align = Alignment(horizontal="center", vertical="center", wrap_text=False)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=False)
    left_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Row 1 – merged title header
    ws.merge_cells("A1:B1")
    cell = ws["A1"]
    cell.value = "DESIGN RULE CLASSIFICATION REPORT"
    cell.font = title_font
    cell.fill = dark_blue_fill
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
    ws.row_dimensions[1].height = 30

    # Row 2 – program info
    ws["A2"] = f"Program: {program_name}"
    ws["A2"].font = bold_font
    ws["A2"].alignment = left_align

    # Row 3 – model year and extraction date
    ws["A3"] = f"Model Year: {model_year_clean}"
    ws["A3"].font = normal_font
    ws["A3"].alignment = left_align
    ws["B3"] = f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws["B3"].font = normal_font
    ws["B3"].alignment = left_align

    # Row 5 – metrics summary
    classification_counts = df["classification"].value_counts().to_dict()
    applicable = classification_counts.get("Applicable", 0)
    carryover = sum(v for k, v in classification_counts.items() if k in ("Carryover", "Previously Validated"))
    not_applicable = classification_counts.get("Not Applicable", 0)
    unclassified = classification_counts.get("Not Classified", 0)
    total = len(df)

    ws.merge_cells("A5:B5")
    ws["A5"] = (
        f"Applicable: {applicable} | Carryover/Previously Validated: {carryover} | "
        f"Not Applicable: {not_applicable} | Not Classified: {unclassified} | Total: {total}"
    )
    ws["A5"].font = bold_font
    ws["A5"].alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)

    # Row 7 – column headers
    headers = ["Classification", "Explanation"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = gray_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Row 8+ – data rows
    data_row = 8
    for _, row in df.iterrows():
        classification = str(row["classification"]) if pd.notna(row["classification"]) else ""
        explanation = str(row["explanation"]) if pd.notna(row["explanation"]) else ""

        # Classification cell with conditional formatting
        cell_cls = ws.cell(row=data_row, column=1)
        cell_cls.value = classification
        cell_cls.alignment = center_align
        cell_cls.border = thin_border

        if classification == "Applicable":
            cell_cls.font = green_font
            cell_cls.fill = green_fill
        elif classification in ("Carryover", "Previously Validated"):
            cell_cls.font = brown_font
            cell_cls.fill = yellow_fill
        elif classification == "Not Applicable":
            cell_cls.font = blue_font
            cell_cls.fill = blue_fill
        elif classification == "Not Classified":
            cell_cls.font = red_font
            cell_cls.fill = red_fill
        else:
            cell_cls.font = normal_font

        # Explanation cell
        cell_exp = ws.cell(row=data_row, column=2)
        cell_exp.value = explanation
        cell_exp.font = normal_font
        cell_exp.alignment = left_wrap
        cell_exp.border = thin_border

        data_row += 1

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 50

    ws.auto_filter.ref = f"A7:B{data_row - 1}"
    ws.freeze_panes = "A8"

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    safe_program = re.sub(r'[^\w\-]', '_', program_name.strip())
    filename = f"DesignRule_{model_year_clean}_{safe_program}.xlsx"
    return excel_buffer, filename


from app.services.dpa5_service import get_dpa5_data


def export_dpa5_excel(gi_code: str, cpsc_filter: str = None, pmt_filter: str = None, snapshot_date: str = None) -> tuple[BytesIO, str]:
    """
    Export DPA5 K-PAC data to Excel format with professional styling.

    Layout:
    - Row 1: Merged header - DPA5 K-PAC REPORT
    - Row 2: GI Code info
    - Row 3: Filters and Extraction Date
    - Row 5: Metrics summary (Total K-PAC | Total Issues | Compliant | Not Compliant | ...)
    - Row 7+: Data table with CPSC, Lead PMT, Program, K-PAC ID, Mfg Area, status counts

    Args:
        gi_code: GI Code from vehicle_line (required)
        cpsc_filter: Optional single CPSC code filter
        pmt_filter: Optional PMT code filter (e.g. '200')

    Returns:
        Tuple of (BytesIO, filename)

    Raises:
        ValueError: If gi_code is empty
        LookupError: If no data is found for the given parameters
        Exception: If BigQuery query fails
    """
    if not gi_code or not gi_code.strip():
        raise ValueError("gi_code parameter is required")

    result = get_dpa5_data(gi_code=gi_code, cpsc_filter=cpsc_filter, pmt_filter=pmt_filter, snapshot_date=snapshot_date)
    records = result.get("data", [])

    if not records:
        raise LookupError(f"No DPA5 data found for gi_code='{gi_code}'")

    df = pd.DataFrame(records)

    wb = Workbook()
    ws = wb.active
    ws.title = "DPA5 K-PAC"

    program_name = str(df.iloc[0]['program']) if 'program' in df.columns and df.iloc[0]['program'] else gi_code
    safe_program = re.sub(r'[^\w\-]', '_', str(program_name).strip())

    dark_blue = "002060"
    light_gray = "D9D9D9"
    white_text = "FFFFFF"
    green_bg = "C6EFCE"
    green_text = "006100"
    red_bg = "FFC7CE"
    red_text = "9C0006"
    blue_bg = "DDEEFF"
    blue_text = "003478"
    yellow_bg = "FFEB9C"
    brown_text = "9C6500"

    title_font = Font(name='Calibri', size=14, bold=True, color=white_text)
    header_font = Font(name='Calibri', size=12, bold=True, color=white_text)
    bold_font = Font(name='Calibri', size=11, bold=True)
    normal_font = Font(name='Calibri', size=11)
    green_font = Font(name='Calibri', size=11, color=green_text)
    red_font = Font(name='Calibri', size=11, color=red_text)
    blue_font = Font(name='Calibri', size=11, color=blue_text)
    brown_font = Font(name='Calibri', size=11, color=brown_text)

    dark_blue_fill = PatternFill(start_color=dark_blue, end_color=dark_blue, fill_type="solid")
    gray_fill = PatternFill(start_color=light_gray, end_color=light_gray, fill_type="solid")
    green_fill = PatternFill(start_color=green_bg, end_color=green_bg, fill_type="solid")
    red_fill = PatternFill(start_color=red_bg, end_color=red_bg, fill_type="solid")
    blue_fill = PatternFill(start_color=blue_bg, end_color=blue_bg, fill_type="solid")
    yellow_fill = PatternFill(start_color=yellow_bg, end_color=yellow_bg, fill_type="solid")

    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    center_align = Alignment(horizontal='center', vertical='center', wrap_text=False)
    left_align = Alignment(horizontal='left', vertical='center', wrap_text=False)
    center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # Row 1 – merged title header
    ws.merge_cells('A1:L1')
    cell = ws['A1']
    cell.value = 'DPA5 K-PAC REPORT'
    cell.font = title_font
    cell.fill = dark_blue_fill
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
    ws.row_dimensions[1].height = 30

    # Row 2 – GI Code / Program info
    ws['A2'] = f'GI Code: {gi_code}'
    ws['A2'].font = bold_font
    ws['A2'].alignment = left_align
    ws['D2'] = f'Program: {program_name}'
    ws['D2'].font = bold_font
    ws['D2'].alignment = left_align

    # Row 3 – filters + extraction date
    filters_txt = f"CPSC Filter: {cpsc_filter or 'All'} | PMT Filter: {pmt_filter or 'All'}"
    ws['A3'] = filters_txt
    ws['A3'].font = normal_font
    ws['A3'].alignment = left_align
    ws['D3'] = f'Extraction Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    ws['D3'].font = normal_font
    ws['D3'].alignment = left_align

    # Row 5 – metrics summary
    total_kpac = len(df)
    total_issues = int(df['total_issues'].sum())
    total_compliant = int(df['total_green_compliant'].sum())
    total_not_compliant = int(df['total_red_not_compliant'].sum())
    total_cannot_assess = int(df['total_blue_cannot_assess'].sum())
    total_na = int(df['total_na_not_applicable'].sum())
    total_non_scorable = int(df['total_non_scorable'].sum())
    total_not_evaluated = int(df['total_not_evaluated'].sum())

    ws.merge_cells('A5:L5')
    ws['A5'] = (
        f'Total K-PAC: {total_kpac} | Total Issues: {total_issues} | Compliant: {total_compliant} | '
        f'Not Compliant: {total_not_compliant} | Cannot Assess: {total_cannot_assess} | '
        f'Not Applicable: {total_na} | Non Scorable: {total_non_scorable} | Not Evaluated: {total_not_evaluated}'
    )
    ws['A5'].font = bold_font
    ws['A5'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=False)

    # Row 7 – column headers
    headers = [
        'CPSC', 'Lead PMT', 'Program', 'K-PAC ID', 'Mfg Functional Area', 'Total Issues',
        'Compliant', 'Not Compliant', 'Cannot Assess', 'Not Applicable', 'Non Scorable', 'Not Evaluated'
    ]
    header_row = 7
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = gray_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Row 8+ – data rows
    data_row = 8
    for _, row in df.iterrows():
        values = [
            row.get('cpsc'), row.get('lead_pmt'), row.get('program'), row.get('k_pac_id'),
            row.get('mfg_functional_area'), row.get('total_issues'),
            row.get('total_green_compliant'), row.get('total_red_not_compliant'),
            row.get('total_blue_cannot_assess'), row.get('total_na_not_applicable'),
            row.get('total_non_scorable'), row.get('total_not_evaluated'),
        ]
        for col_num, value in enumerate(values, 1):
            cell = ws.cell(row=data_row, column=col_num)
            cell.value = value if value is not None else ''
            cell.border = thin_border

            if col_num in (3, 5):  # Program, Mfg Functional Area -> left aligned
                cell.font = normal_font
                cell.alignment = left_wrap
            else:
                cell.font = normal_font
                cell.alignment = center_wrap

            # Conditional formatting on status count columns
            if col_num == 7 and isinstance(value, (int, float)) and value > 0:      # Compliant
                cell.font = green_font
                cell.fill = green_fill
            elif col_num == 8 and isinstance(value, (int, float)) and value > 0:    # Not Compliant
                cell.font = red_font
                cell.fill = red_fill
            elif col_num == 9 and isinstance(value, (int, float)) and value > 0:    # Cannot Assess
                cell.font = blue_font
                cell.fill = blue_fill
            elif col_num == 10 and isinstance(value, (int, float)) and value > 0:   # Not Applicable
                cell.font = brown_font
                cell.fill = yellow_fill

        data_row += 1

    widths = [12, 30, 40, 20, 30, 12, 12, 14, 14, 15, 14, 14]
    for i, width in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=header_row, column=i).column_letter].width = width

    ws.auto_filter.ref = f'A7:L{data_row - 1}'
    ws.freeze_panes = 'A8'

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    suffix = ""
    if cpsc_filter:
        suffix += f"_{cpsc_filter}"
    if pmt_filter:
        suffix += f"_PMT{pmt_filter}"
    filename = f"DPA5_Report_{safe_program}{suffix}.xlsx"
    return excel_buffer, filename


def export_dvp_glidepath_excel(
    gi_code: str,
    pmt: str = None,
    milestone: str = None,
    snapshot_date: str = None
):
    """
    Gera arquivo Excel para os dados de DVP Glidepath.
    """

    try:
        result = get_dvp_glidepath_aggregated_data(
            gi_code=gi_code,
            pmt=pmt,
            milestone=milestone,
            snapshot_date=snapshot_date
        )

        data = result.get("data", [])

        if not data:
            raise ValueError("No data found for the specified GI Code and filters")

        total_meet = sum(item["metrics"].get("meet", 0) for item in data)
        total_does_not_meet = sum(
            item["metrics"].get("does_not_meet", 0)
            for item in data
        )
        total_unassessed = sum(
            item["metrics"].get("unassessed", 0)
            for item in data
        )
        total_items = sum(item["metrics"].get("total", 0) for item in data)

        assessed_total = total_meet + total_does_not_meet

        assessment_rate = (
            assessed_total / total_items
            if total_items > 0
            else 0
        )

        compliance_rate = (
            total_meet / assessed_total
            if assessed_total > 0
            else 0
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "DVP Glidepath"

        # Cores Ford
        ford_blue = "003478"
        light_blue = "D9EAF7"
        header_blue = "1F4E78"

        green_fill = "C6EFCE"
        green_text = "006100"

        red_fill = "FFC7CE"
        red_text = "9C0006"

        yellow_fill = "FFEB9C"
        yellow_text = "9C6500"

        gray_fill = "D9E1F2"

        thin_gray = Side(style="thin", color="B7B7B7")


        ws.merge_cells("A1:L1")
        ws["A1"] = "DVP GLIDEPATH REPORT"
        ws["A1"].font = Font(
            name="Arial",
            size=16,
            bold=True,
            color="FFFFFF"
        )
        ws["A1"].fill = PatternFill(
            fill_type="solid",
            fgColor=ford_blue
        )
        ws["A1"].alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        ws.row_dimensions[1].height = 28

        ws["A2"] = "GI Code:"
        ws["B2"] = gi_code

        ws["D2"] = "PMT Filter:"
        ws["E2"] = pmt if pmt else "All"

        ws["G2"] = "Milestone Filter:"
        ws["H2"] = milestone if milestone else "All"

        ws["J2"] = "Export Date:"
        ws["K2"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        for cell in ["A2", "D2", "G2", "J2"]:
            ws[cell].font = Font(bold=True, color="FFFFFF")
            ws[cell].fill = PatternFill(
                fill_type="solid",
                fgColor=header_blue
            )

        for cell in ["B2", "E2", "H2", "K2"]:
            ws[cell].fill = PatternFill(
                fill_type="solid",
                fgColor=light_blue
            )

        summary_items = [
            ("Total Items", total_items, gray_fill, "000000"),
            ("Meet", total_meet, green_fill, green_text),
            ("Does Not Meet", total_does_not_meet, red_fill, red_text),
            ("Unassessed", total_unassessed, yellow_fill, yellow_text),
            ("Assessment %", assessment_rate, light_blue, "000000"),
            ("Compliance %", compliance_rate, light_blue, "000000"),
        ]

        start_col = 1

        for label, value, fill_color, font_color in summary_items:
            label_cell = ws.cell(row=5, column=start_col)
            value_cell = ws.cell(row=5, column=start_col + 1)

            label_cell.value = label
            value_cell.value = value

            label_cell.font = Font(bold=True, color="FFFFFF")
            label_cell.fill = PatternFill(
                fill_type="solid",
                fgColor=header_blue
            )
            label_cell.alignment = Alignment(horizontal="center")

            value_cell.font = Font(bold=True, color=font_color)
            value_cell.fill = PatternFill(
                fill_type="solid",
                fgColor=fill_color
            )
            value_cell.alignment = Alignment(horizontal="center")

            if label in ["Assessment %", "Compliance %"]:
                value_cell.number_format = "0.0%"

            start_col += 2

        headers = [
            "GI Code",
            "PMT Code",
            "Model Year",
            "Milestone",
            "Scheduled Finished",
            "Actual Finished",
            "Meet",
            "Does Not Meet",
            "Unassessed",
            "Total",
            "Assessment %",
            "Compliance %",
        ]

        header_row = 7

        for col_index, header in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col_index)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor=header_blue
            )
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True
            )
            cell.border = Border(
                left=thin_gray,
                right=thin_gray,
                top=thin_gray,
                bottom=thin_gray
            )

        ws.row_dimensions[header_row].height = 32


        data_start_row = 8

        for row_index, item in enumerate(data, start=data_start_row):
            metrics = item.get("metrics", {})

            meet = metrics.get("meet", 0)
            does_not_meet = metrics.get("does_not_meet", 0)
            unassessed = metrics.get("unassessed", 0)
            total = metrics.get("total", 0)

            assessed = meet + does_not_meet

            row_assessment_rate = assessed / total if total > 0 else 0
            row_compliance_rate = meet / assessed if assessed > 0 else 0

            row_values = [
                item.get("gi_code"),
                item.get("pmt_code"),
                item.get("model_year"),
                item.get("milestone"),
                item.get("scheduled_finished"),
                item.get("actual_finished"),
                meet,
                does_not_meet,
                unassessed,
                total,
                row_assessment_rate,
                row_compliance_rate,
            ]

            for col_index, value in enumerate(row_values, start=1):
                cell = ws.cell(row=row_index, column=col_index)
                cell.value = value
                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center"
                )
                cell.border = Border(
                    left=thin_gray,
                    right=thin_gray,
                    top=thin_gray,
                    bottom=thin_gray
                )

            # Formato de porcentagem
            ws.cell(row=row_index, column=11).number_format = "0.0%"
            ws.cell(row=row_index, column=12).number_format = "0.0%"

            # Cores das métricas
            ws.cell(row=row_index, column=7).fill = PatternFill(
                fill_type="solid",
                fgColor=green_fill
            )
            ws.cell(row=row_index, column=7).font = Font(
                color=green_text
            )

            ws.cell(row=row_index, column=8).fill = PatternFill(
                fill_type="solid",
                fgColor=red_fill
            )
            ws.cell(row=row_index, column=8).font = Font(
                color=red_text
            )

            ws.cell(row=row_index, column=9).fill = PatternFill(
                fill_type="solid",
                fgColor=yellow_fill
            )
            ws.cell(row=row_index, column=9).font = Font(
                color=yellow_text
            )


        ws.freeze_panes = "A8"

        ws.auto_filter.ref = (
            f"A7:L{data_start_row + len(data) - 1}"
        )

        column_widths = {
            "A": 15,
            "B": 12,
            "C": 13,
            "D": 15,
            "E": 20,
            "F": 18,
            "G": 12,
            "H": 18,
            "I": 14,
            "J": 12,
            "K": 16,
            "L": 16,
        }

        for column, width in column_widths.items():
            ws.column_dimensions[column].width = width

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        safe_gi_code = gi_code.replace("/", "_").replace("\\", "_")
        safe_pmt = pmt.replace("/", "_").replace("\\", "_") if pmt else "ALL"

        filename = f"DVP_Glidepath_{safe_gi_code}_PMT_{safe_pmt}.xlsx"

        return StreamingResponse(
            output,
            media_type=(
                "application/"
                "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ValueError:
        raise

    except Exception as e:
        raise Exception(f"Error generating DVP Glidepath Excel: {str(e)}")


from app.services.fede_status_service import get_hir_completion_metrics


def export_hir_excel(
    gi_code: str,
    cpsc: str = None,
    pmt_code: str = None,
    milestone_date: str = None
) -> tuple[BytesIO, str]:
    """
    Export HIR (Hardware in Review) completion data to Excel format with professional styling.

    Layout:
    - Row 1: Merged header - HIR COMPLETION REPORT
    - Row 2: GI Code / Program info
    - Row 3: Filters and Extraction Date
    - Row 5: Metrics summary (Total Items | With Evidence | Without Evidence | Completion %)
    - Row 7+: Data table with program_name, gi_code, dvp_team, pmt_code, cpsc,
              milestone_date, with_evidence, without_evidence, total_items, completion_percentage

    Args:
        gi_code: GI Code from vehicle_line (required)
        cpsc: Optional CPSC code filter
        pmt_code: Optional PMT code filter
        milestone_date: Optional milestone date filter

    Returns:
        Tuple of (BytesIO, filename)

    Raises:
        ValueError: If gi_code is empty
        LookupError: If no data is found for the given parameters
        Exception: If BigQuery query fails
    """
    if not gi_code or not gi_code.strip():
        raise ValueError("gi_code parameter is required")

    result = get_hir_completion_metrics(
        gi_code=gi_code,
        cpsc=cpsc,
        pmt_code=pmt_code,
        milestone_date=milestone_date
    )
    records = result.get("data", [])

    if not records:
        raise LookupError(f"No HIR data found for gi_code='{gi_code}'")

    df = pd.DataFrame(records)

    wb = Workbook()
    ws = wb.active
    ws.title = "HIR Completion"

    program_name = str(df.iloc[0]['program_name']) if 'program_name' in df.columns and df.iloc[0]['program_name'] else gi_code
    safe_program = re.sub(r'[^\w\-]', '_', str(program_name).strip())

    # --- Color palette (Ford standard) ---
    dark_blue = "002060"
    light_gray = "D9D9D9"
    white_text = "FFFFFF"
    green_bg = "C6EFCE"
    green_text = "006100"
    red_bg = "FFC7CE"
    red_text = "9C0006"
    yellow_bg = "FFEB9C"
    brown_text = "9C6500"

    title_font = Font(name='Calibri', size=14, bold=True, color=white_text)
    header_font = Font(name='Calibri', size=12, bold=True, color=white_text)
    bold_font = Font(name='Calibri', size=11, bold=True)
    normal_font = Font(name='Calibri', size=11)
    green_font = Font(name='Calibri', size=11, color=green_text)
    red_font = Font(name='Calibri', size=11, color=red_text)
    brown_font = Font(name='Calibri', size=11, color=brown_text)

    dark_blue_fill = PatternFill(start_color=dark_blue, end_color=dark_blue, fill_type="solid")
    gray_fill = PatternFill(start_color=light_gray, end_color=light_gray, fill_type="solid")
    green_fill = PatternFill(start_color=green_bg, end_color=green_bg, fill_type="solid")
    red_fill = PatternFill(start_color=red_bg, end_color=red_bg, fill_type="solid")
    yellow_fill = PatternFill(start_color=yellow_bg, end_color=yellow_bg, fill_type="solid")

    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    center_align = Alignment(horizontal='center', vertical='center', wrap_text=False)
    left_align = Alignment(horizontal='left', vertical='center', wrap_text=False)
    left_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
    center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)

    num_cols = 10
    last_col_letter = 'J'
    ws.merge_cells(f'A1:{last_col_letter}1')
    cell = ws['A1']
    cell.value = 'HIR COMPLETION REPORT'
    cell.font = title_font
    cell.fill = dark_blue_fill
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
    ws.row_dimensions[1].height = 30

    ws['A2'] = f'GI Code: {gi_code}'
    ws['A2'].font = bold_font
    ws['A2'].alignment = left_align
    ws['D2'] = f'Program: {program_name}'
    ws['D2'].font = bold_font
    ws['D2'].alignment = left_align

    filters_txt = f"CPSC: {cpsc or 'All'} | PMT: {pmt_code or 'All'} | Milestone: {milestone_date or 'All'}"
    ws['A3'] = filters_txt
    ws['A3'].font = normal_font
    ws['A3'].alignment = left_align
    ws['G3'] = f'Extraction Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    ws['G3'].font = normal_font
    ws['G3'].alignment = left_align

    total_items = int(df['total_items'].sum())
    total_with = int(df['with_evidence'].sum())
    total_without = int(df['without_evidence'].sum())
    avg_completion = round(df['completion_percentage'].mean(), 1) if not df.empty else 0.0

    ws.merge_cells(f'A5:{last_col_letter}5')
    ws['A5'] = (
        f'Total Items: {total_items} | With Evidence: {total_with} | '
        f'Without Evidence: {total_without} | Avg Completion: {avg_completion}%'
    )
    ws['A5'].font = bold_font
    ws['A5'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=False)

    headers = [
        'Program Name', 'GI Code', 'DVP Team', 'PMT Code', 'CPSC',
        'Milestone Date', 'With Evidence', 'Without Evidence', 'Total Items', 'Completion %'
    ]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = gray_fill
        cell.alignment = center_align
        cell.border = thin_border

    data_row = 8
    for _, row in df.iterrows():
        values = [
            row.get('program_name'), row.get('gi_code'), row.get('dvp_team'),
            row.get('pmt_code'), row.get('cpsc'), row.get('milestone_date'),
            row.get('with_evidence'), row.get('without_evidence'),
            row.get('total_items'), row.get('completion_percentage'),
        ]
        for col_num, value in enumerate(values, 1):
            cell = ws.cell(row=data_row, column=col_num)
            cell.value = value if value is not None else ''
            cell.border = thin_border
            if col_num in (1, 3):
                cell.font = normal_font
                cell.alignment = left_wrap
            else:
                cell.font = normal_font
                cell.alignment = center_wrap
            if col_num == 7 and isinstance(value, (int, float)) and value > 0:
                cell.font = green_font
                cell.fill = green_fill
            elif col_num == 8 and isinstance(value, (int, float)) and value > 0:
                cell.font = red_font
                cell.fill = red_fill
            elif col_num == 10:
                pct = float(value) if value else 0.0
                if pct >= 80:
                    cell.font = green_font
                    cell.fill = green_fill
                elif pct >= 50:
                    cell.font = brown_font
                    cell.fill = yellow_fill
                else:
                    cell.font = red_font
                    cell.fill = red_fill
        data_row += 1

    widths = [40, 14, 50, 12, 12, 16, 16, 18, 14, 16]
    for i, width in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=7, column=i).column_letter].width = width

    ws.auto_filter.ref = f'A7:{last_col_letter}{data_row - 1}'
    ws.freeze_panes = 'A8'

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    suffix = ""
    if cpsc:
        suffix += f"_{cpsc}"
    if pmt_code:
        suffix += f"_PMT{pmt_code}"
    filename = f"HIR_Report_{safe_program}{suffix}.xlsx"
    return excel_buffer, filename

from app.services.cost_service import get_tooling_cost_metrics, get_piece_cost_metrics


def export_costs_excel(
    effectivein: str,
    cpsc: str = None,
    pmt_code: str = None,
    cost_type: str = "both"
) -> tuple[BytesIO, str]:
    """
    Export Costs (Tooling and/or Piece Cost) data to Excel with two sheets.

    Layout (per sheet):
    - Row 1: Merged header with Ford Blue (#002060)
    - Row 2: Effective Point and filters
    - Row 3: Extraction Date
    - Row 5: Summary metrics
    - Row 7+: Data table with AutoFilter and frozen header

    Args:
        effectivein: Effective Point code (required)
        cpsc: CPSC filter (optional)
        pmt_code: PMT code filter (optional)
        cost_type: 'tooling', 'piece', or 'both' (default 'both')

    Returns:
        Tuple of (BytesIO, filename)
    """
    if not effectivein or not effectivein.strip():
        raise ValueError("effectivein parameter is required")

    dark_blue = "002060"
    light_gray = "D9D9D9"
    white_text = "FFFFFF"
    green_bg = "C6EFCE"
    green_text = "006100"
    red_bg = "FFC7CE"
    red_text = "9C0006"
    yellow_bg = "FFEB9C"
    brown_text = "9C6500"

    title_font = Font(name='Calibri', size=14, bold=True, color=white_text)
    header_font = Font(name='Calibri', size=12, bold=True, color=white_text)
    bold_font = Font(name='Calibri', size=11, bold=True)
    normal_font = Font(name='Calibri', size=11)
    green_font = Font(name='Calibri', size=11, color=green_text)
    red_font = Font(name='Calibri', size=11, color=red_text)
    brown_font = Font(name='Calibri', size=11, color=brown_text)

    dark_blue_fill = PatternFill(start_color=dark_blue, end_color=dark_blue, fill_type="solid")
    gray_fill = PatternFill(start_color=light_gray, end_color=light_gray, fill_type="solid")
    green_fill = PatternFill(start_color=green_bg, end_color=green_bg, fill_type="solid")
    red_fill = PatternFill(start_color=red_bg, end_color=red_bg, fill_type="solid")
    yellow_fill = PatternFill(start_color=yellow_bg, end_color=yellow_bg, fill_type="solid")

    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    center_align = Alignment(horizontal='center', vertical='center', wrap_text=False)
    left_align = Alignment(horizontal='left', vertical='center', wrap_text=False)
    left_wrap = Alignment(horizontal='left', vertical='center', wrap_text=True)
    center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)

    wb = Workbook()
    wb.remove(wb.active)

    def _write_header(ws, title: str, col_count: int):
        last_col = ws.cell(row=1, column=col_count).column_letter
        ws.merge_cells(f'A1:{last_col}1')
        cell = ws['A1']
        cell.value = title
        cell.font = title_font
        cell.fill = dark_blue_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30

        ws['A2'] = f'Effective Point: {effectivein}'
        ws['A2'].font = bold_font
        ws['A2'].alignment = left_align
        ws['D2'] = f'CPSC: {cpsc or "All"} | PMT: {pmt_code or "All"}'
        ws['D2'].font = bold_font
        ws['D2'].alignment = left_align

        ws['A3'] = f'Extraction Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        ws['A3'].font = normal_font
        ws['A3'].alignment = left_align

    def _write_col_headers(ws, headers: list, row: int = 7):
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = gray_fill
            cell.alignment = center_align
            cell.border = thin_border

    if cost_type in ("both", "tooling"):
        tooling_result = get_tooling_cost_metrics(effectivein, cpsc=cpsc, pmt_code=pmt_code)
        tooling_records = tooling_result.get("data", [])

        if tooling_records:
            ws_t = wb.create_sheet("Tooling Cost")
            tooling_headers = [
                'Part Number', 'Program', 'Vehicle Line', 'PMT', 'CPSC', 'CPSC Name',
                'Cost Plant', 'Source Ref', 'Actual Cost', 'Currency',
                'Target Cost', 'Target Currency', 'Gap'
            ]
            _write_header(ws_t, 'TOOLING COST REPORT', len(tooling_headers))

            total_actual = sum(r.get('actual_tooling_cost', 0) or 0 for r in tooling_records)
            total_target = sum(r.get('target_tooling_cost', 0) or 0 for r in tooling_records)
            total_gap = sum(r.get('gap', 0) or 0 for r in tooling_records)

            last_col = ws_t.cell(row=5, column=len(tooling_headers)).column_letter
            ws_t.merge_cells(f'A5:{last_col}5')
            ws_t['A5'] = (
                f'Total Records: {len(tooling_records)} | '
                f'Total Actual: {total_actual:,.2f} | '
                f'Total Target: {total_target:,.2f} | '
                f'Total Gap: {total_gap:,.2f}'
            )
            ws_t['A5'].font = bold_font
            ws_t['A5'].alignment = Alignment(horizontal='left', vertical='center')

            _write_col_headers(ws_t, tooling_headers)

            data_row = 8
            for r in tooling_records:
                values = [
                    r.get('partnumber'), r.get('program'), r.get('vehicleline'),
                    r.get('pmt'), r.get('cpsc'), r.get('cpsc_name'),
                    r.get('costplant'), r.get('source_reference'),
                    r.get('actual_tooling_cost'), r.get('currency'),
                    r.get('target_tooling_cost'), r.get('target_currency'),
                    r.get('gap')
                ]
                for col_num, value in enumerate(values, 1):
                    cell = ws_t.cell(row=data_row, column=col_num)
                    cell.value = value if value is not None else ''
                    cell.border = thin_border
                    cell.font = normal_font
                    cell.alignment = left_wrap if col_num in (1, 2, 3, 5, 6, 7) else center_wrap

                    gap = r.get('gap', 0) or 0
                    if col_num == 13:
                        if gap < 0:
                            cell.font = green_font
                            cell.fill = green_fill
                        elif gap > 0:
                            cell.font = red_font
                            cell.fill = red_fill
                data_row += 1

            last_data_col = ws_t.cell(row=7, column=len(tooling_headers)).column_letter
            ws_t.auto_filter.ref = f'A7:{last_data_col}{data_row - 1}'
            ws_t.freeze_panes = 'A8'

            widths = [22, 20, 16, 8, 12, 30, 14, 20, 16, 10, 14, 14, 14]
            for i, w in enumerate(widths, 1):
                ws_t.column_dimensions[ws_t.cell(row=7, column=i).column_letter].width = w

    if cost_type in ("both", "piece"):
        piece_result = get_piece_cost_metrics(effectivein, cpsc=cpsc, pmt_code=pmt_code)
        piece_records = piece_result.get("data", [])

        if piece_records:
            ws_p = wb.create_sheet("Piece Cost")
            piece_headers = [
                'Program', 'Vehicle Line', 'Effective In', 'PMT', 'Part Number',
                'CPSC', 'CPSC Name', 'Actual Cost', 'Currency',
                'Target Cost', 'Target Currency', 'Gap', 'Source Ref'
            ]
            _write_header(ws_p, 'PIECE COST REPORT', len(piece_headers))

            total_actual = sum(r.get('actual_piece_cost', 0) or 0 for r in piece_records)
            total_target = sum(r.get('target_piece_cost', 0) or 0 for r in piece_records)
            total_gap = sum(r.get('gap', 0) or 0 for r in piece_records)

            last_col = ws_p.cell(row=5, column=len(piece_headers)).column_letter
            ws_p.merge_cells(f'A5:{last_col}5')
            ws_p['A5'] = (
                f'Total Records: {len(piece_records)} | '
                f'Total Actual: {total_actual:,.2f} | '
                f'Total Target: {total_target:,.2f} | '
                f'Total Gap: {total_gap:,.2f}'
            )
            ws_p['A5'].font = bold_font
            ws_p['A5'].alignment = Alignment(horizontal='left', vertical='center')

            _write_col_headers(ws_p, piece_headers)

            data_row = 8
            for r in piece_records:
                values = [
                    r.get('program'), r.get('vehicleline'), r.get('effectivein'),
                    r.get('pmt'), r.get('partnumber'),
                    r.get('cpsc'), r.get('cpsc_name'),
                    r.get('actual_piece_cost'), r.get('currency'),
                    r.get('target_piece_cost'), r.get('target_currency'),
                    r.get('gap'), r.get('source_reference')
                ]
                for col_num, value in enumerate(values, 1):
                    cell = ws_p.cell(row=data_row, column=col_num)
                    cell.value = value if value is not None else ''
                    cell.border = thin_border
                    cell.font = normal_font
                    cell.alignment = left_wrap if col_num in (1, 2, 3, 5, 7, 13) else center_wrap

                    gap = r.get('gap', 0) or 0
                    if col_num == 12:
                        if gap < 0:
                            cell.font = green_font
                            cell.fill = green_fill
                        elif gap > 0:
                            cell.font = red_font
                            cell.fill = red_fill
                data_row += 1

            last_data_col = ws_p.cell(row=7, column=len(piece_headers)).column_letter
            ws_p.auto_filter.ref = f'A7:{last_data_col}{data_row - 1}'
            ws_p.freeze_panes = 'A8'

            widths = [20, 16, 16, 8, 22, 12, 30, 16, 10, 14, 14, 14, 20]
            for i, w in enumerate(widths, 1):
                ws_p.column_dimensions[ws_p.cell(row=7, column=i).column_letter].width = w

    if not wb.sheetnames:
        raise LookupError(f"No cost data found for effectivein='{effectivein}'")

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    safe_ep = re.sub(r'[^\w\-]', '_', effectivein.strip())
    suffix = ""
    if cpsc:
        suffix += f"_{cpsc}"
    if pmt_code:
        suffix += f"_PMT{pmt_code}"
    filename = f"Costs_Report_{safe_ep}{suffix}.xlsx"
    return excel_buffer, filename
