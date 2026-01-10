from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user

router = APIRouter(prefix="/trading", tags=["trading"])

def is_admin(user: models.User) -> bool:
    return user.role is not None and user.role.name == "admin"

# Strategy CRUD
@router.post("/strategies", response_model=schemas.StrategyTemplateOut)
def create_strategy(payload: schemas.StrategyTemplateCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    st = models.StrategyTemplate(user_id=user.id, **payload.model_dump())
    db.add(st)
    db.commit()
    db.refresh(st)
    return st

@router.get("/strategies", response_model=list[schemas.StrategyTemplateOut])
def list_strategies(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.StrategyTemplate).filter(models.StrategyTemplate.user_id == user.id).order_by(models.StrategyTemplate.id.desc()).all()

# Risk Profile CRUD
@router.post("/risk-profiles", response_model=schemas.RiskProfileOut)
def create_risk_profile(payload: schemas.RiskProfileCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if payload.is_default:
        db.query(models.RiskProfile).filter(models.RiskProfile.user_id == user.id).update({"is_default": False})
    rp = models.RiskProfile(user_id=user.id, **payload.model_dump())
    db.add(rp)
    db.commit()
    db.refresh(rp)
    return rp

@router.get("/risk-profiles", response_model=list[schemas.RiskProfileOut])
def list_risk_profiles(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.RiskProfile).filter(models.RiskProfile.user_id == user.id).order_by(models.RiskProfile.id.desc()).all()
# Phase 4.2: User Reset Today
@router.post("/metrics/reset-today")
def reset_today(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """User-facing endpoint to reset today's metrics (clears lockout + counters)"""
    from datetime import datetime, timezone
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    dm = db.query(models.DailyMetric).filter(
        models.DailyMetric.user_id == user.id,
        models.DailyMetric.day == day
    ).first()
    
    if not dm:
        dm = models.DailyMetric(
            user_id=user.id,
            day=day,
            realized_pnl=0.0,
            locked_out=False,
            trades_today=0,
            consecutive_losses=0
        )
        db.add(dm)
    else:
        dm.realized_pnl = 0.0
        dm.locked_out = False
        dm.trades_today = 0
        dm.consecutive_losses = 0
    
    db.commit()
    db.refresh(dm)
    return {"status": "today metrics reset", "day": day}