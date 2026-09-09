from pydantic import BaseModel
from typing import Optional
from app.schemas.effective_point import EffectivePointSchema

class VehicleLineSchema(BaseModel):
    id: Optional[int] = None
    program_code: str
    model_year: int
    program_name: str
    vehicle_line: str
    affected_plant: str
    plant_code: str
    summary: str
    effective_point: Optional[EffectivePointSchema] = None

    model_config = {"from_attributes": True}
