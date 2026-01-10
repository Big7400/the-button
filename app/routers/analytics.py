from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AnalyticsCreate, AnalyticsResponse
from app.models import Analytics
from app.core.security import get_current_user, get_current_admin

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/", response_model=list[AnalyticsResponse])
def get_analytics(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Admin-only: get all analytics"""
    return db.query(Analytics).all()

@router.post("/", response_model=AnalyticsResponse)
def create_analytics(payload: AnalyticsCreate, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    record = Analytics(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
