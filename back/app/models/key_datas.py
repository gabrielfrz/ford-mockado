from sqlalchemy import Column, Date, ForeignKey, Integer, String
from app.core.database import Base

class KeyDatas(Base):
    __tablename__ = "key_datas"

    id = Column(Integer, primary_key=True, index=True)
    effective_point_id = Column(Integer, ForeignKey("effective_point.id"))
    milestone_name = Column(String)
    milestone_date = Column(Date)
