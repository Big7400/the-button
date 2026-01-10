from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Notification
from app.schemas import NotificationCreate, NotificationResponse
from app.core.security import get_current_user, get_current_admin

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=list[NotificationResponse])
def get_my_notifications(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get notifications for current user"""
    return db.query(Notification).filter(Notification.user_id == current_user.id).all()

@router.post("/", response_model=NotificationResponse)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Admin can send notifications to any user"""
    notif = Notification(**payload.model_dump())
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
