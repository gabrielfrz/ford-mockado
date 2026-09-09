"""System endpoints used by API catalogs and availability checks."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    """Represent a successful API health response."""

    status: str = Field(min_length=2, max_length=2, pattern="^ok$")

    model_config = ConfigDict(extra="forbid")


@router.get(
    "/test",
    response_model=HealthResponse,
    responses={200: {"description": "OK"}},
    summary="Test API availability",
    description="Returns HTTP 200 when the API is available.",
)
def test_api_availability() -> HealthResponse:
    """Return a minimal response confirming that the API is available."""
    return HealthResponse(status="ok")
