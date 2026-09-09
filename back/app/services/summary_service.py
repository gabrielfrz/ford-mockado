from sqlalchemy.orm import Session
from app.models.vehicle_line import VehicleLine

def get_vehicle_summary(db: Session, program_code: str, program_name: str, model_year: int):
    vehicle = (
        db.query(VehicleLine)
        .filter(
            VehicleLine.program_code == program_code,
            VehicleLine.program_name == program_name,
            VehicleLine.model_year == model_year
        )
        .first()
    )

    if not vehicle:
        return None

    summary = {
        "vehicle_line": f"{vehicle.model_year}MY {vehicle.program_code} {vehicle.program_name} - {vehicle.effective_point}",
        "affected_plant": vehicle.affected_plant,
        "plant_code": vehicle.plant_code,
        "key_datas": [
            {"event": kd.event, "date": kd.date.strftime("%Y-%m-%d")}
            for kd in getattr(vehicle, "key_datas", [])
        ],
    }

    return summary
