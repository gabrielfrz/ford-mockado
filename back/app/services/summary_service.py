"""Build high-level dashboard summary response objects."""

from app.schemas.summary import SummarySchema

def build_vehicle_line_summary(vehicle_line_obj, effective_point_obj):
    """Combine vehicle-line and Effective Point models into a summary schema."""
    return SummarySchema(
        vehicle_line=vehicle_line_obj.vehicle_line,
        affected_plant=vehicle_line_obj.affected_plant,
        plant_code=vehicle_line_obj.plant_code,
        effective_point={"effective_point": effective_point_obj.effective_point}
    )
