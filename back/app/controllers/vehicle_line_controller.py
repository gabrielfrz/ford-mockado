"""Coordinate vehicle-line summary requests with the service layer."""

from app.services.vehicle_line_service import get_vehicle_line_summary

def fetch_vehicle_line_summary(program_code: str, model_year: int, program_name: str):
    """Return a vehicle-line summary for a program and model year."""
    return get_vehicle_line_summary(program_code, model_year, program_name)
