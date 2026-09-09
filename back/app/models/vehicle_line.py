from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class VehicleLine(Base):
    __tablename__ = "vehicle_lines"

    id = Column(Integer, primary_key=True, index=True)
    program_code = Column(String, index=True)
    model_year = Column(Integer)
    program_name = Column(String, index=True)
    vehicle_line = Column(String)
    affected_plant = Column(String)
    plant_code = Column(String)
    summary = Column(String)
    effective_point = relationship(
        "EffectivePoint",
        back_populates="vehicle_line",
        uselist=False,
        cascade="all, delete-orphan"
    )
