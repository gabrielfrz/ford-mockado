from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.controllers.summary_controller import fetch_summary
from app.core.database import SessionLocal

router = APIRouter(prefix="/summary", tags=["Summary"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def read_summary(program_code: str, model_year: int, program_name: str, db: Session = Depends(get_db)):
    """
    Vehicle Line summary combining:
    - Vehicle Line
    - Effective Points 
    - Key Datas
    """
    return fetch_summary(db, program_code, model_year, program_name)
