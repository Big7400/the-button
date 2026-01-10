
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    users = db.query(models.User).all()
    return [
        {"id": u.id, "email": u.email, "is_active": u.is_active, "role": u.role.name}
        for u in users
    ]

@router.patch("/users/{user_id}/role")
def update_role(
    user_id: int,
    payload: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    role = db.query(models.Role).filter(models.Role.name == payload.role_name).first()
    if not role:
        raise HTTPException(400, "Role not found")

    user.role_id = role.id
    db.commit()
    return {"status": "role updated", "user_id": user.id, "role": role.name}

@router.patch("/users/{user_id}/active")
def set_active(
    user_id: int,
    payload: schemas.ActiveUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = payload.is_active
    db.commit()
    return {"status": "active updated", "user_id": user.id, "is_active": user.is_active}
# Phase 4.2: Admin unlock user
@router.post("/users/{user_id}/unlock-today")
def unlock_today(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    """Admin endpoint to unlock a user's daily lockout"""
    from datetime import datetime, timezone
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dm = db.query(models.DailyMetric).filter(
        models.DailyMetric.user_id == user_id,
        models.DailyMetric.day == day
    ).first()
    
    if not dm:
        return {"status": "no metric for today", "user_id": user_id, "day": day}
    
    dm.locked_out = False
    db.commit()
    
    return {"status": "unlocked", "user_id": user_id, "day": day}