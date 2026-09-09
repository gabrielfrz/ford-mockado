"""Pydantic response schema for Effective Point records."""

from pydantic import BaseModel
from typing import Optional

class EffectivePointSchema(BaseModel):
    """Serialize an Effective Point record for API responses."""

    id: Optional[int]
    effective_point: str
    status: Optional[str]

    model_config = {"from_attributes": True}
