"""Expose the temporary Effective Point lookup API."""

from fastapi import APIRouter
from typing import List

router = APIRouter(prefix="/effective-point", tags=["Effective Point"])

mock_effective_points = [
    {"id": 1, "effective_point": "S4PVBS", "status": "active"},
    {"id": 2, "effective_point": "A1B2C3", "status": "inactive"},
]

@router.get("/")
def get_all_effective_points():
    """Return all configured mock Effective Points."""
    return mock_effective_points

@router.get("/search/")
def check_effective_point_exists(code: str):
    """Report whether an Effective Point code exists in the mock dataset."""
    exists = any(ep["effective_point"] == code for ep in mock_effective_points)
    return {"effective_point": code, "exists": exists}
