"""Coordinate summary requests with the vehicle-line service."""

from app.services.vehicle_line_service import get_vehicle_line_summary

def summary_controller(model_year: float, program_names: str, program_codes: str, selected_index: int | None = None):
    """Return the vehicle-line summary selected by the supplied filters."""
    return get_vehicle_line_summary(model_year, program_names, program_codes, selected_index)
