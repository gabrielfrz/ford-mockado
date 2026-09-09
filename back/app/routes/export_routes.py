"""Expose formatted Excel exports for dashboard deliverables."""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from app.services.excel_export_service import (
    export_cae_status_excel,
    export_dvp_team_assessment_excel,
    export_design_rule_excel,
    export_dpa5_excel,
    export_dvp_glidepath_excel,
    export_hir_excel,
    export_costs_excel,
)

from io import BytesIO

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/cae-status", summary="Export CAE Status to Excel", description="Export CAE assessment data for a specific GI Code as professional Excel file")
def export_cae_status_endpoint(
    gi_id: str = Query(..., description="GI ID for filtering CAE status records"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Export CAE status data to professional Excel format with styling and filters.
    
    Args:
        gi_id: GI ID for filtering results (required)
    
    Metrics:
        - CPSC: CPSC code extracted from DVP team name
        - Assessment Name: Full DVP team name
        - Status: Conformance status (Meet=Green, Does Not Meet=Red)
        - Program: Program name
        - GI_ID: GI code identifier
    
    Rules:
        - Excel file with professional styling (Ford Blue header)
        - Main header: Merged cells, Ford Blue (#003478), White Bold 16pt
        - Vehicle Line and GI ID information in rows 2-3
        - Metrics summary in row 5
        - Data table starting at row 7 with Auto-Filter enabled
        - Zebra striping (alternating row colors)
        - Conditional formatting: Meet=Green text, Does Not Meet=Red text
        - Filters by gi_id matching the provided value
        - INCLUDES ONLY records where prototype_type contains 'CAE'
        - Requires conf_state to be non-null and non-empty
        - CPSC code extraction logic: uses dotted format (XX.XX.XX), numeric 6-digit, or first numeric segment
        - Returns file with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    try:
        if not gi_id or not gi_id.strip():
            raise HTTPException(status_code=400, detail="gi_id parameter is required")
        
        excel_buffer, filename = export_cae_status_excel(gi_id, pmt_code)
        
        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CAE status: {str(e)}")


@router.get("/dvp-team-assessment", summary="Export DVP Team Assessment to Excel", description="Export DVP Team assessment data for a specific GI Code as professional Excel file")
def export_dvp_team_assessment_endpoint(
    gi_id: str = Query(..., description="GI ID for filtering DVP Team assessment records"),
    dvp_team: str = Query(None, description="Optional DVP Team name to filter (if not provided, exports all teams)"),
    snapshot_date: str = Query(None, description="Optional Snapshot date filter")
):
    """
    Export DVP Team assessment data to professional Excel format with styling and filters.
    
    Args:
        gi_id: GI ID for filtering results (required)
        dvp_team: Optional DVP team filter
        snapshot_date: Optional snapshot date filter
    
    Metrics:
        - CPSC: CPSC code extracted from DVP team name
        - DVP Team: Full DVP team name
        - Status: Standardized conformance status
        - GI_ID: GI code identifier
    
    Rules:
        - Excel file with professional styling (Ford Blue header)
        - Main header: Merged cells, Ford Blue (#003478), White Bold 16pt
        - GI ID and extraction date in rows 2-3
        - Metrics summary in row 5
        - Data table starting at row 7 with Auto-Filter enabled
        - Conditional formatting: Meet=Green text, Unassessed=Red text, Approved Deviation=Yellow
        - Filters by gi_id matching the provided value
        - Includes all assessment rows with non-null dvp_team
        - Standardizes status: Pass/Meet -> Meet, null/empty -> Unassessed
        - CPSC extraction logic: uses dotted format (XX.XX.XX) or 6-digit prefix, otherwise Other
        - Returns file with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    try:
        if not gi_id or not gi_id.strip():
            raise HTTPException(status_code=400, detail="gi_id parameter is required")
        
        excel_buffer, filename = export_dvp_team_assessment_excel(gi_id, dvp_team=dvp_team, snapshot_date=snapshot_date)
        
        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting DVP Team assessment: {str(e)}")


@router.get("/design-rule", summary="Export Design Rule Classification to Excel", description="Export Design Rule classification data for a specific model year and program as a professional Excel file")
def export_design_rule_endpoint(
    model_year: str = Query(..., description="Model year (e.g. 2027)"),
    program_name: str = Query(..., description="Program name used to locate Design Rule records (e.g. 'U725 Special Mackinaw tophat')"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Export Design Rule classification data to professional Excel format with styling and filters.

    Args:
        model_year: Model year for filtering (required)
        program_name: Program name for filtering via dr_pk2 prefix match (required)

    Metrics:
        - Classification: Applicable, Carryover, Previously Validated, Not Applicable, Not Classified
        - Explanation: Classification explanation text
        - Summary counts in header (Applicable | Carryover | Not Applicable | Unclassified | Total)

    Rules:
        - Excel file with professional styling (Ford Blue header)
        - Main header: Merged cells, Ford Blue (#002060), White Bold 14pt
        - Program and Model Year info in rows 2-3
        - Metrics summary in row 5
        - Data table starting at row 7 with Auto-Filter and frozen header enabled
        - Conditional formatting per classification value
        - Uses progressive token fallback to match dr_pk2 prefix
        - Returns 404 if no data found for the given parameters
        - Returns file with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    try:
        excel_buffer, filename = export_design_rule_excel(model_year, program_name, pmt_code)

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in export_design_rule_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error exporting Design Rule data. Please try again later.")


@router.get("/dpa5", summary="Export DPA5 K-PAC Data to Excel", description="Export DPA5 K-PAC aggregated data for a specific GI Code as professional Excel file")
def export_dpa5_endpoint(
    gi_code: str = Query(..., description="GI Code from vehicle_line"),
    cpsc: str = Query(None, description="Single CPSC code filter (optional)"),
    pmt: str = Query(None, description="PMT code filter e.g. '200' (optional)"),
    snapshot_date: str = Query(None, description="Snapshot date filter (optional)")
):
    """
    Export DPA5 K-PAC data to professional Excel format with styling and filters.

    Args:
        gi_code: GI Code used to resolve CPSC/dashboard scope (required)
        cpsc: Narrow results to a single CPSC code (optional)
        pmt: PMT code filter (optional)

    Rules:
        - Excel file with professional styling (Ford Blue header)
        - Data table with CPSC, Lead PMT, Program, K-PAC ID, Mfg Functional Area,
          Total Issues and the 6 status counts (Compliant/Not Compliant/Cannot Assess/
          Not Applicable/Non Scorable/Not Evaluated)
        - Conditional formatting per status column
        - Returns 404 if no data found for the given parameters
        - Returns file with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    try:
        excel_buffer, filename = export_dpa5_excel(gi_code, cpsc_filter=cpsc, pmt_filter=pmt, snapshot_date=snapshot_date)

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in export_dpa5_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error exporting DPA5 data. Please try again later.")


@router.get(
    "/dvp-glidepath",
    summary="Export DVP Glidepath Excel",
    description=(
        "Export DVP Glidepath consolidated data to Excel, "
        "with optional filters by PMT and Milestone."
    )
)
def export_dvp_glidepath(
    gi_code: str = Query(
        ...,
        description="GI Code from vehicle_line. Example: GI-10199"
    ),
    pmt: str = Query(
        None,
        description="Optional PMT Code filter. Example: 200"
    ),
    milestone: str = Query(
        None,
        description="Optional Milestone filter. Format: YYYY-MM-DD"
    ),
    snapshot_date: str = Query(
        None,
        description="Optional Snapshot date filter"
    )
):
    """
    Export DVP Glidepath consolidated data to professional Excel format.

    Args:
        gi_code: GI Code for filtering (required)
        pmt: PMT Code filter (optional)
        milestone: Milestone date filter (optional, format YYYY-MM-DD)

    Rules:
        - Excel file with Ford Blue professional styling
        - Summary metrics in row 5 (Total Items, Meet, Does Not Meet, Unassessed, Assessment %, Compliance %)
        - Data table from row 7 with Auto-Filter and frozen header
        - Conditional formatting: Meet=Green, Does Not Meet=Red, Unassessed=Yellow
        - Returns 404 if no data found for the given parameters
        - Returns file with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    try:
        return export_dvp_glidepath_excel(
            gi_code=gi_code,
            pmt=pmt,
            milestone=milestone,
            snapshot_date=snapshot_date
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting DVP Glidepath: {str(e)}"
        )


@router.get(
    "/hir",
    summary="Export HIR Completion to Excel",
    description="Export HIR (Hardware in Review) completion data for a specific GI Code as professional Excel file"
)
def export_hir_endpoint(
    gi_code: str = Query(..., description="GI Code from vehicle_line"),
    cpsc: str = Query(None, description="CPSC code filter (optional)"),
    pmt_code: str = Query(None, description="PMT code filter (optional)"),
    milestone_date: str = Query(None, description="Milestone date filter (optional, format YYYY-MM-DD)"),
):
    """
    Export HIR completion data to professional Excel format with styling and filters.

    Args:
        gi_code: GI Code used to filter HIR records (required)
        cpsc: CPSC code filter (optional)
        pmt_code: PMT code filter (optional)
        milestone_date: Milestone date filter (optional)

    Metrics:
        - Program Name, GI Code, DVP Team, PMT Code, CPSC
        - Milestone Date, With Evidence, Without Evidence, Total Items, Completion %

    Rules:
        - Excel file with professional styling (Ford Blue header #002060)
        - Main header: Merged cells A1:J1, White Bold 14pt
        - GI Code and Program info in row 2
        - Filters and Extraction Date in row 3
        - Summary metrics in row 5 (Total Items | With Evidence | Without Evidence | Avg Completion)
        - Data table from row 7 with Auto-Filter and frozen header at row 8
        - Conditional formatting:
            * With Evidence column: Green when > 0
            * Without Evidence column: Red when > 0
            * Completion % >= 80: Green, >= 50: Yellow, < 50: Red
        - Returns 404 if no data found for the given parameters
        - Returns file with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    try:
        excel_buffer, filename = export_hir_excel(
            gi_code=gi_code,
            cpsc=cpsc,
            pmt_code=pmt_code,
            milestone_date=milestone_date
        )

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in export_hir_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error exporting HIR data. Please try again later.")


@router.get(
    "/costs",
    summary="Export Costs to Excel",
    description="Export Tooling and Piece Cost data for a specific Effective Point as professional Excel file with two sheets"
)
def export_costs_endpoint(
    effectivein: str = Query(..., description="Effective Point code (e.g. S4PVBS)"),
    cpsc: str = Query(None, description="CPSC code filter (optional)"),
    pmt_code: str = Query(None, description="PMT code filter (optional)"),
    cost_type: str = Query("both", description="Cost type: 'tooling', 'piece', or 'both' (default: both)"),
):
    try:
        excel_buffer, filename = export_costs_excel(
            effectivein=effectivein,
            cpsc=cpsc,
            pmt_code=pmt_code,
            cost_type=cost_type
        )

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in export_costs_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error exporting Costs data. Please try again later.")
