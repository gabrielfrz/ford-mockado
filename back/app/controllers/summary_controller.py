from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.vehicle_line import VehicleLine
from app.models.effective_point import EffectivePoint
from app.models.key_datas import KeyDatas

def fetch_summary(db: Session, program_code: str, model_year: int, program_name: str):
    vehicle_line = (
        db.query(VehicleLine)
        .filter(
            VehicleLine.program_code == program_code,
            VehicleLine.model_year == model_year,
            VehicleLine.program_name == program_name
        )
        .first()
    )

    if not vehicle_line:
        raise HTTPException(status_code=404, detail="Vehicle line not found.")

    milestones = (
        db.query(EffectivePoint)
        .filter(EffectivePoint.vehicle_line_id == vehicle_line.id)
        .all()
    )

    vehicle_line_str = (
        f"{vehicle_line.model_year}MY {vehicle_line.program_code} "
        f"{vehicle_line.program_name} ({vehicle_line.tg_code}) - {vehicle_line.effective_point}"
    )

    summary_text = (
        vehicle_line.summary
        or f"Resumo do programa {vehicle_line.program_name} ({vehicle_line.program_code}), "
           f"fase {vehicle_line.effective_point}, em {vehicle_line.affected_plant}."
    )

    return {
        "vehicle_line": vehicle_line_str,
        "affected_plant": vehicle_line.affected_plant,
        "plant_code": vehicle_line.plant_code,
        "summary": summary_text,
        "key_datas": [
            {
                "milestone": m.milestone_name,
                "date": m.milestone_date.isoformat() if m.milestone_date else None,
                "status": m.status
            }
            for m in milestones
        ]
    }
