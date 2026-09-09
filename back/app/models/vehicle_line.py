"""SQLAlchemy model for vehicle-line program records."""

from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class VehicleLine(Base):
    """Persist vehicle-line metadata linked to an Effective Point."""

    __tablename__ = "vehicle_line"

    id = Column(Integer, primary_key=True, index=True)
    program_code = Column(String, nullable=False)
    model_year = Column(Integer, nullable=False)
    vehicle_line = Column(String, nullable=False)
    affected_plant = Column(String, nullable=False)
    plant_code = Column(String, nullable=False)

    id_effective_point = Column(Integer, ForeignKey("effective_point.id"))
