from pydantic import BaseModel
from typing import List, Optional

class KeyData(BaseModel):
    event: str
    date: str

class VehicleLineSummary(BaseModel):
    vehicle_line: str  
    affected_plant: str 
    plant_code: str  
    key_datas: Optional[List[KeyData]] = None

    model_config = {"from_attributes": True}

