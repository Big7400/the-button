from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from app import models

router = APIRouter(
    prefix="/settings",
    tags=["settings"]
)

@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    return db.query(models.UserSettings).all()

@router.post("/")
def create_setting(
    user_id: int,
    key: str,
    value: str,
    db: Session = Depends(get_db)
):
    setting = models.UserSettings(
        user_id=user_id,
        key=key,
        value=value
    )
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
