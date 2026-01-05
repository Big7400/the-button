from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
import models

router = APIRouter(prefix="/settings", tags=["settings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_settings(db: Session = Depends(get_db)):
    return db.query(models.UserSettings).all()

@router.post("/")
def create_setting(user_id: int, preference: str, db: Session = Depends(get_db)):
    setting = models.UserSettings(user_id=user_id, preference=preference)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
