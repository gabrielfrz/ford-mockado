from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.key_datas import KeyDatas
from app.schemas.key_datas import KeyDataSchema
from app.core.database import SessionLocal
from typing import List

router = APIRouter(prefix="/key-datas", tags=["Key Datas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[KeyDataSchema])
def list_key_datas(effective_point_id: int = None, db: Session = Depends(get_db)):
    query = db.query(KeyDatas)
    if effective_point_id:
        query = query.filter(KeyDatas.effective_point_id == effective_point_id)
    return query.all()
