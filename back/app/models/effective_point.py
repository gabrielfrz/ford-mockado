"""SQLAlchemy model for Effective Point milestone records."""

from sqlalchemy import Column, Integer, String, Date
from app.core.database import Base

class EffectivePoint(Base):
    """Persist an Effective Point status and associated milestone."""

    __tablename__ = "effective_point"

    id = Column(Integer, primary_key=True, index=True)
    effective_point = Column(String, nullable=False)
    status = Column(String)
    milestone_name = Column(String)
    milestone_date = Column(Date)
