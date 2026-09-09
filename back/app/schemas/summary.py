"""Pydantic response schema for dashboard summaries."""

from pydantic import BaseModel
from typing import Optional, Dict

class SummarySchema(BaseModel):
    """Serialize the high-level vehicle and Effective Point summary."""

    vehicle_line: str
    affected_plant: str
    plant_code: str
    effective_point: Dict[str, str]

    model_config = {"from_attributes": True}
