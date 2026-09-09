from fastapi import APIRouter, Query
from app.services.vehicle_line_service import get_vehicle_line_summary
from app.schemas.vehicle_line import VehicleLineSchema

router = APIRouter(prefix="/vehicle-line", tags=["Vehicle Line"])

@router.get("/", response_model=VehicleLineSchema)
def get_vehicle_line(
    program_code: str = Query(..., description="Código do programa (ex: U727N)"),
    model_year: int = Query(..., description="Ano do modelo (ex: 2027)"),
    program_name: str = Query(..., description="Nome do programa (ex: Bronco)")
):
    """
    Retorna o resumo consolidado de um programa de veículo.
    """
    return get_vehicle_line_summary(program_code, model_year, program_name)
