from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.effective_point import EffectivePoint
from app.schemas.effective_point import EffectivePointSchema
from app.core.database import SessionLocal
from typing import List

router = APIRouter(prefix="/effective-point", tags=["Effective Point"])

mock_effective_points = [
    {"id": 1, "effective_point": "S4PVBS", "status": "active"},
    {"id": 2, "effective_point": "A1B2C3", "status": "inactive"},
]

@router.get("/")
def get_all_effective_points():
    return mock_effective_points

@router.get("/search/")
def check_effective_point_exists(code: str):
    exists = any(ep["effective_point"] == code for ep in mock_effective_points)
    return {"effective_point": code, "exists": exists}