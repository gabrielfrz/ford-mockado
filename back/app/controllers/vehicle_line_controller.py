from app.services.vehicle_line_service import get_vehicle_line_summary

def fetch_vehicle_line_summary(program_code: str, model_year: int, program_name: str):
    """
    Controller responsável por orquestrar a obtenção do resumo do Vehicle Line.
    """
    return get_vehicle_line_summary(program_code, model_year, program_name)
