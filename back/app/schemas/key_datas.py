from pydantic import BaseModel
from datetime import date
from typing import Optional

class KeyDataSchema(BaseModel):
    id: Optional[int] = None
    effective_point_id: int
    milestone_name: str
    milestone_date: date

    model_config = {"from_attributes": True}

