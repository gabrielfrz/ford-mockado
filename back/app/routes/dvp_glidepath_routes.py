"""Expose DVP glidepath metrics and filter metadata."""

from fastapi import APIRouter, Query, HTTPException
from app.services.dvp_glidepath_service import (
    get_dvp_glidepath_data,
    get_available_pmts,
    get_available_milestones,
    get_dvp_snapshots
)

router = APIRouter(prefix="/api/v1/dvp-glidepath", tags=["DVP Glidepath"])


@router.get(
    "/data",
    summary="DVP Glidepath Data",
    description=(
        "Return DVP glidepath data aggregated by GI code, model year, and date. "
        "The response includes compliance metrics and milestone, scheduled-finish, "
        "and actual-finish timelines."
    )
)
def get_glidepath_data(
    gi_code: str = Query(..., description="Vehicle-line GI code (for example, GI-10001)"),
    pmt: str = Query(None, description="Optional PMT filter (for example, 200)"),
    milestone: str = Query(None, description="Optional milestone date in YYYY-MM-DD format")
):
    """Return aggregated DVP glidepath chart data for the supplied filters."""
    try:
        return get_dvp_glidepath_data(gi_code, pmt, milestone)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DVP glidepath data: {str(e)}")


@router.get(
    "/pmts",
    summary="Available PMTs",
    description="Return distinct PMT codes available for a GI code."
)
def list_available_pmts(
    gi_code: str = Query(..., description="Vehicle-line GI code in GI-xxxxx format")
):
    """Return all distinct PMT codes available for a GI code."""
    try:
        pmts = get_available_pmts(gi_code)
        return {
            "gi_code": gi_code,
            "pmts": pmts,
            "total": len(pmts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve PMTs: {str(e)}")


@router.get(
    "/milestones",
    summary="Available milestones",
    description="Return distinct milestones for a GI code, optionally filtered by PMT."
)
def list_available_milestones(
    gi_code: str = Query(..., description="Vehicle-line GI code in GI-xxxxx format"),
    pmt: str = Query(None, description="Optional PMT filter (for example, 200)")
):
    """Return available milestone dates for a GI code and optional PMT."""
    try:
        milestones = get_available_milestones(gi_code, pmt)
        return {
            "gi_code": gi_code,
            "pmt": pmt,
            "milestones": milestones,
            "total": len(milestones)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar milestones: {str(e)}")

@router.get(
    "/snapshots",
    summary="Snapshots Disponíveis",
    description="Retorna lista de snapshots disponíveis"
)
def list_available_snapshots(
    gi_code: str = Query(..., description="GI Code do vehicle_line")
):
    try:
        snapshots = get_dvp_snapshots(gi_code)
        return {
            "gi_code": gi_code,
            "snapshots": snapshots,
            "total": len(snapshots)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar snapshots: {str(e)}")
