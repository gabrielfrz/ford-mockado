from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

class EffectivePoint(Base):
    __tablename__ = "effective_point"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_line_id = Column(Integer, ForeignKey("vehicle_lines.id"), unique=True)
    effective_point = Column(String)
    status = Column(String)

    vehicle_line = relationship("VehicleLine", back_populates="effective_point", uselist=False)
