"""Expose the high-level vehicle summary endpoint."""

from fastapi import APIRouter, Query
from app.controllers.summary_controller import summary_controller
from app.schemas.summary import SummarySchema

router = APIRouter(prefix="/summary", tags=["Summary"])

@router.get("/", response_model=SummarySchema)
def get_summary(
    program_code: str = Query(...),
    model_year: int = Query(...),
    program_name: str = Query(...)
):
    """Return a summary for the selected program and model year."""
    return summary_controller(program_code, model_year, program_name)
