"""Expose DPA5 K-PAC data, summary, and filter endpoints."""

from fastapi import APIRouter, Query, HTTPException
from app.services.dpa5_service import get_dpa5_data, get_dpa5_summary, get_dpa5_cpsc_list, get_dpa5_snapshots

router = APIRouter(prefix="/dpa5", tags=["DPA5"])


@router.get(
    "/data",
    summary="DPA5 K-PAC Data",
    description=(
        "Returns DPA5 K-PAC aggregated data with glidepath milestones, "
        "filtered by the CPSC codes associated with the given GI Code."
    ),
)
def get_dpa5(
    gi_code: str = Query(..., description="GI Code from vehicle_line"),
    cpsc:    str = Query(None,  description="Single CPSC code filter (optional)"),
    page:    int = Query(1,     description="Page number (1-based)", ge=1),
    limit:   int = Query(100,   description="Records per page (max 500)", ge=1, le=500),
    snapshot_date: str = Query(None, description="Date for historical snapshot (optional)")
):
    """
    Retrieve DPA5 K-PAC data for a vehicle program.

    Args:
        gi_code: GI Code used to resolve the CPSC list from dvp_fede (required)
        cpsc: Narrow results to a single CPSC code (optional)
        page: Page number for pagination (default 1)
        limit: Records per page (default 100, max 500)
    """
    try:
        result = get_dpa5_data(gi_code, cpsc, snapshot_date=snapshot_date)
        # Apply pagination
        all_data = result.get("data", [])
        start = (page - 1) * limit
        end   = start + limit
        result["data"]          = all_data[start:end]
        result["page"]          = page
        result["limit"]         = limit
        result["total_records"] = len(all_data)
        result["total_pages"]   = max(1, -(-len(all_data) // limit))  # ceiling div
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving DPA5 data: {str(e)}")


@router.get(
    "/summary",
    summary="DPA5 Summary + Glidepath",
    description=(
        "Returns DPA5 aggregated totals (for donut chart) and glidepath goal curves "
        "per milestone date (for the glidepath chart)."
    ),
)
def get_dpa5_summary_route(
    gi_code: str = Query(..., description="GI Code from vehicle_line"),
    cpsc:    str = Query(None,  description="Single CPSC code filter (optional)"),
    pmt:     str = Query(None,  description="PMT code filter e.g. '200' (optional)"),
    snapshot_date: str = Query(None, description="Date for historical snapshot (optional)")
):
    """Return DPA5 status totals and milestone glidepath curves."""
    try:
        return get_dpa5_summary(gi_code=gi_code, cpsc_filter=cpsc, pmt_filter=pmt, snapshot_date=snapshot_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving DPA5 summary: {str(e)}")


@router.get("/cpsc-list", summary="DPA5 CPSC List")
def get_dpa5_cpsc_list_route(
    gi_code: str = Query(..., description="GI Code from vehicle_line"),
    pmt:     str = Query(None, description="PMT code filter e.g. '200' (optional)"),
):
    """Return DPA5 CPSC values available for the supplied filters."""
    try:
        cpsc_codes = get_dpa5_cpsc_list(gi_code=gi_code, pmt_filter=pmt)
        return {"gi_code": gi_code, "pmt_filter": pmt, "cpsc_codes": cpsc_codes, "count": len(cpsc_codes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving DPA5 CPSC list: {str(e)}")


@router.get("/snapshots", summary="DPA5 Available Snapshots")
def get_dpa5_snapshots_route(
    gi_code: str = Query(..., description="GI Code from vehicle_line"),
):
    try:
        snapshots = get_dpa5_snapshots(gi_code=gi_code)
        return {"gi_code": gi_code, "snapshots": snapshots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving DPA5 snapshots: {str(e)}")
