from app.schemas.vehicle_line import VehicleLineSchema

def get_vehicle_line_summary(program_code: str, model_year: int, program_name: str):
    """
    Simulando a consolidação dos dados. Em um cenário real, aqui serão consultas via SQL 
    às tabelas vpp001_glb_integrator_prj_vw, vpp002_mfg_veh_pgm_vw, vpp005_prj_timing_pivot_vw, etc.
    """

    mock_effective_point = "S4PVBS"
    mock_affected_plant = "Michigan Assembly Plant"
    mock_plant_code = "NA02"

    vehicle_line = f"{model_year} {program_code} {program_name}"
    summary = f"{vehicle_line} ({mock_affected_plant.split()[0]}) - {mock_effective_point}"

    return VehicleLineSchema(
        program_code=program_code,
        model_year=model_year,
        program_name=program_name,
        vehicle_line=vehicle_line,
        affected_plant=mock_affected_plant,
        plant_code=mock_plant_code,
        summary=summary,
        effective_point={"effective_point": mock_effective_point}
    )
