"""Expose cross-deliverable milestone-readiness metrics."""

from fastapi import APIRouter, HTTPException, Path, Query
from app.services.milestone_readiness_service import (
    get_milestone_readiness,
    VALID_MILESTONES,
)

router = APIRouter(prefix="/api/v1", tags=["Milestone Readiness"])


@router.get(
    "/milestone-readiness/{gi_code}",
    summary="Milestone Readiness",
    description=(
        "Calculate milestone readiness for a GI code by aggregating DVP, CAE, "
        "and Design Rule metrics in parallel."
    ),
)
def milestone_readiness(
    gi_code: str = Path(..., description="Vehicle-line GI code (for example, VF123456)"),
    milestone: str = Query(
        ...,
        description=(
            "Milestone key matching a vehicle-line table column. "
            f"Accepted values: {', '.join(VALID_MILESTONES)}"
        ),
    ),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Calculate Milestone Readiness for a given GI Code and milestone key.

    Path parameter:
        gi_code: GI Code identifier from the vehicle_line table.

    Query parameter:
        milestone: Column name of the milestone in vehicle_line
                   (e.g. 'mr', 'ps', 'psc', 'fpd', 'fc1' ...).

    Response:
        gi_code        – GI Code queried.
        program        – Full program name from vehicle_line.
        milestone      – Milestone key used.
        milestone_date – ISO date fetched from vehicle_line for this milestone.
        metrics        – Array with one entry per deliverable source:
            source     – 'DVP' | 'CAE' | 'Design Rules'
            target     – Total items due on or before the milestone date.
            actual     – Items with a completion status.
            percentage – actual / target × 100 (0.0 when target = 0).
            status     – 'Green' (>=100%) | 'Yellow' (>=80%) | 'Red' (<80%).

    Status rules:
        Green  : percentage >= 100 %
        Yellow : 80 % <= percentage < 100 %
        Red    : percentage < 80 %
    """
    try:
        return get_milestone_readiness(gi_code, milestone, pmt_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate milestone readiness: {exc}",
        )
