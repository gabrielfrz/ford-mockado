"""Expose tooling- and piece-cost endpoints with Effective Point filters."""

from fastapi import APIRouter, Query, HTTPException
from app.services.cost_service import (
    get_cpsc_by_effective_point,
    autocomplete_cpsc_by_effective_point,
    get_pmt_by_effective_point,
    get_partnumber_list,
    get_commodity_list,
    get_vehicleline_list,
    get_dropdown_data,
    get_tooling_cost_metrics,
    get_piece_cost_metrics,
    get_combined_cost_metrics
)

router = APIRouter(prefix="/cost", tags=["Cost Metrics"])


@router.get("/cpsc/list", summary="List CPSCs by Effective Point")
def list_cpsc_by_effective_point(
    effectivein: str = Query(..., description="Effective Point code (for example, S4PVBS)")
):
    """Return the distinct CPSCs associated with an Effective Point."""
    try:
        cpsc_list = get_cpsc_by_effective_point(effectivein)
        return {
            "effectivein": effectivein,
            "cpsc_codes": cpsc_list,
            "count": len(cpsc_list)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve CPSCs for Effective Point '{effectivein}': {str(e)}"
        )


@router.get("/cpsc/autocomplete", summary="Autocomplete CPSC by Effective Point")
def autocomplete_cpsc(
    effectivein: str = Query(..., description="Effective Point code (for example, S4PVBS)"),
    q: str = Query("", description="Case-insensitive CPSC search term")
):
    """Return up to 50 CPSC suggestions for an Effective Point."""
    try:
        results = autocomplete_cpsc_by_effective_point(effectivein, q)
        
        if not results and q:
            # Fetch the unfiltered count to provide useful empty-result context.
            all_cpsc = autocomplete_cpsc_by_effective_point(effectivein, "")
            return {
                "effectivein": effectivein,
                "cpsc_codes": [],
                "count": 0,
                "message": f"No CPSC for Effective Point '{effectivein}' contains '{q}'. Available: {len(all_cpsc)}"
            }
        
        return {
            "effectivein": effectivein,
            "cpsc_codes": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CPSC autocomplete failed: {str(e)}"
        )


@router.get("/pmt/list", summary="List PMTs by Effective Point")
def list_pmt_by_effective_point(
    effectivein: str = Query(..., description="Effective Point code (for example, S4PVBS)"),
    cpsc: str = Query(None, description="Optional CPSC filter")
):
    """Return distinct PMTs for an Effective Point and optional CPSC."""
    try:
        pmt_list = get_pmt_by_effective_point(effectivein, cpsc)
        return {
            "effectivein": effectivein,
            "cpsc": cpsc,
            "pmt_codes": pmt_list,
            "count": len(pmt_list)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve PMTs: {str(e)}"
        )


@router.get("/dropdowns", summary="Load all cost dropdowns in one query")
def get_dropdowns(
    effectivein: str = Query(..., description="Effective Point code (for example, VBS)")
):
    """Load part numbers, commodities, and vehicle lines in one query."""
    try:
        data = get_dropdown_data(effectivein)
        return {
            "effectivein": effectivein,
            "partnumbers": data["partnumbers"],
            "commodities": data["commodities"],
            "vehicle_lines": data["vehicle_lines"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load cost dropdowns: {str(e)}"
        )


@router.get("/partnumber/list", summary="List part numbers")
def list_partnumbers(
    effectivein: str = Query(..., description="Effective Point code (for example, VBS)"),
    q: str = Query(None, description="Optional case-insensitive part-number search")
):
    """Return distinct part numbers for a frontend selector."""
    try:
        items = get_partnumber_list(effectivein=effectivein, q=q)
        return {
            "effectivein": effectivein,
            "q": q,
            "part_numbers": items,
            "count": len(items)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve part numbers: {str(e)}"
        )


@router.get("/commodity/list", summary="List commodities")
def list_commodities(
    effectivein: str = Query(..., description="Effective Point code (for example, VBS)"),
    q: str = Query(None, description="Optional commodity code or name search")
):
    """Return distinct CPSC and commodity-name pairs for a selector."""
    try:
        items = get_commodity_list(effectivein=effectivein, q=q)
        return {
            "effectivein": effectivein,
            "q": q,
            "commodities": items,
            "count": len(items)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve commodities: {str(e)}"
        )


@router.get("/vehicleline/list", summary="List vehicle lines")
def list_vehiclelines(
    effectivein: str = Query(..., description="Effective Point code (for example, VBS)"),
    q: str = Query(None, description="Optional vehicle-line search")
):
    """Return distinct vehicle lines for a frontend selector."""
    try:
        items = get_vehicleline_list(effectivein=effectivein, q=q)
        return {
            "effectivein": effectivein,
            "q": q,
            "vehicle_lines": items,
            "count": len(items)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve vehicle lines: {str(e)}"
        )


@router.get("/metrics/tooling", summary="Tooling cost metrics")
def get_tooling_metrics(
    effectivein: str = Query(..., description="Effective Point code (for example, VBS)"),
    cpsc: str = Query(None, description="Optional CPSC filter"),
    pmt_code: str = Query(None, description="Optional PMT filter")
):
    """Return tooling-cost metrics for the supplied filters."""
    try:
        metrics = get_tooling_cost_metrics(effectivein, cpsc, pmt_code)
        
        if "error" in metrics:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate tooling-cost metrics: {metrics['error']}"
            )

        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve tooling-cost metrics: {str(e)}"
        )


@router.get("/metrics/piece", summary="Piece cost metrics")
def get_piece_metrics(
    effectivein: str = Query(..., description="Effective Point code (for example, VBS)"),
    partnumber: str = Query(None, description="Optional part-number filter"),
    cpsc: str = Query(None, description="Optional CPSC filter"),
    pmt_code: str = Query(None, description="Optional PMT filter")
):
    """Return piece-cost metrics for the supplied filters."""
    try:
        metrics = get_piece_cost_metrics(effectivein, partnumber=partnumber, cpsc=cpsc, pmt_code=pmt_code)
        
        if "error" in metrics:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate piece-cost metrics: {metrics['error']}"
            )
        
        if metrics.get("total_records", 0) == 0:
            raise HTTPException(
                status_code=404,
                detail="No piece-cost data matched the supplied filters"
            )
        
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve piece-cost metrics: {str(e)}"
        )


@router.get("/metrics/combined", summary="Combined cost metrics")
def get_combined_metrics(
    effectivein: str = Query(..., description="Effective Point code (for example, S4PVBS)"),
    cpsc: str = Query(None, description="Optional CPSC filter"),
    pmt_code: str = Query(None, description="Optional PMT filter")
):
    """Return combined tooling- and piece-cost metrics."""
    try:
        metrics = get_combined_cost_metrics(effectivein, cpsc, pmt_code)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve combined cost metrics: {str(e)}"
        )
