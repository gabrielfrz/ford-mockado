"""Pydantic response schema for vehicle-line program details."""

from typing import Optional, Dict
from pydantic import BaseModel

class VehicleLineSchema(BaseModel):
    """Serialize vehicle-line metadata and normalized milestone dates."""

    program_code: str
    gi_code: Optional[str] = None
    model_year: int
    vehicle_line: str
    affected_plant: Optional[str] = None
    plant_code: Optional[str] = None
    plant_name: Optional[str] = None
    wers_plant: Optional[str] = None
    effective_point_code: Optional[str] = None
    summary: Optional[str] = None
    effective_point: Optional[dict] = None

    milestones: Optional[Dict[str, Optional[str]]] = None

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (), 
    }
