"""Expose vehicle-line summary and autocomplete endpoints."""

from fastapi import APIRouter, Query, HTTPException
from app.schemas.vehicle_line import VehicleLineSchema
from app.services.vehicle_line_service import (
    get_vehicle_line_summary,
    get_model_years,
    get_program_names,
    get_program_codes
)

router = APIRouter()

@router.get(
    "/vehicle-line/",
    tags=["Vehicle Line"],
    response_model=VehicleLineSchema,
)
def vehicle_line_summary(
    model_year: float = Query(..., description="Model year (for example, 2027)"),
    program_codes: str = Query(..., description="Project description (for example, U725 Special \"Mackinaw\" tophat)"),
    program_names: str = Query("", description="Optional vehicle or program name filter (for example, Bronco)"),
    selected_index: int | None = Query(
        None,
        description="Row index to select when multiple options exist (for example, 0)"
    ),
):
    """
    Retrieve vehicle line summary filtered by model year and program criteria.
    
    Args:
        model_year: Model year value (required)
        program_codes: Program code for filtering (required)
        program_names: Program name/vehicle name for additional filtering (optional)
        selected_index: Optional index for selecting specific row when multiple matches exist
    
    Metrics:
        - gi_code: GI code identifier
        - vehicle_line: Full vehicle line name
        - model_year: Model year value
        - program_code: Program code identifier
        - summary: Structured summary data
        - milestones: Milestone dates and status
    
    Rules:
        - model_year and program_codes are required
        - program_names is optional and acts as additional filter when provided
        - Implements AND logic for filtering when multiple parameters are provided
        - Program codes normalized for exact matching (special characters removed, lowercase)
        - Returns 404 if no matches found
    """
    try:
        result = get_vehicle_line_summary(model_year, program_names, program_codes, selected_index)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in vehicle_line_summary: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
    if result is None:
        raise HTTPException(status_code=404, detail="No vehicle line found for the given parameters.")
    return result

# Autocomplete endpoints

@router.get("/search/model-years", tags=["Vehicle Line"])
def search_model_years(query: str = Query("", description="Model-year search term")):
    """
    Execute model year autocomplete search.
    
    Args:
        query: Search term for filtering model years
    
    Metrics:
        - model_years: List of matching model year values
        - count: Total count of results
    
    Rules:
        - Case-insensitive keyword matching
        - Returns unique values only
        - Sorted in ascending order
    """
    return get_model_years(query)

@router.get("/search/program-names", tags=["Vehicle Line"])
def search_program_names(
    model_year: str = Query("", description="Selected model year"),
    query: str = Query("", description="Program-name search term")
):
    """
    Execute program name autocomplete search filtered by model year.
    
    Args:
        model_year: Model year for filtering results (optional)
        query: Search term for program names
    
    Metrics:
        - program_names: List of matching program name values
        - count: Total count of results
    
    Rules:
        - Optionally filters by model year if provided
        - Case-insensitive LIKE matching
        - Returns unique values only
        - Limited to 50 results
    """
    return get_program_names(model_year, query)

@router.get("/search/program-codes", tags=["Vehicle Line"])
def search_program_codes(
    model_year: str = Query("", description="Selected model year"),
    program_name: str = Query("", description="Selected program name"),
    query: str = Query("", description="Project-description search term")
):
    """
    Execute program code autocomplete search filtered by model year and program name.
    
    Args:
        model_year: Model year for filtering results (optional)
        program_name: Program name for filtering results (optional)
        query: Search term for program codes
    
    Metrics:
        - program_codes: List of matching program code values
        - count: Total count of results
    
    Rules:
        - Optionally filters by model year and program name if provided
        - Case-insensitive LIKE matching
        - Returns unique values only
        - Program codes normalized (special characters removed, lowercase)
        - Limited to 50 results
    """
    return get_program_codes(model_year, program_name, query)
