from pydantic import BaseModel
from typing import Optional

class EffectivePointSchema(BaseModel):
    id: Optional[int] = None
    effective_point: str
    status: Optional[str] = None

    model_config = {"from_attributes": True}

