from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime, timezone

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user

router = APIRouter(prefix="/engine", tags=["engine"])

def round_money(x: float | None, nd: int = 2):
    if x is None:
        return None
    return round(float(x), nd)

def round_price(x: float | None, nd: int = 6):
    if x is None:
        return None
    return round(float(x), nd)

def utc_day_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def is_admin(user: models.User) -> bool:
    return user.role is not None and user.role.name == "admin"

def get_default_risk_profile(db: Session, user_id: int):
    rp = db.query(models.RiskProfile).filter(
        models.RiskProfile.user_id == user_id,
        models.RiskProfile.is_default == True
    ).first()
    if rp:
        return rp
    return db.query(models.RiskProfile).filter(models.RiskProfile.user_id == user_id).first()

def calc_rr(direction: str, entry: float, sl: float, tp: float | None):
    if tp is None:
        return None
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    reward = (tp - entry) if direction == "long" else (entry - tp)
    return reward / risk

def calc_position_size(rp: models.RiskProfile, entry: float, sl: float):
    stop_distance = abs(entry - sl)
    if stop_distance <= 0:
        return None, None, None
    risk_amount = rp.account_balance * (rp.risk_per_trade_pct / 100.0)
    units = risk_amount / stop_distance
    return risk_amount, stop_distance, units

def daily_lockout_active(db: Session, user_id: int) -> bool:
    day = utc_day_str()
    dm = db.query(models.DailyMetric).filter(models.DailyMetric.user_id == user_id, models.DailyMetric.day == day).first()
    return bool(dm and dm.locked_out)

def build_plan(payload: schemas.EnginePlanRequest, db: Session, user: models.User) -> schemas.EnginePlanResponse:
    reasons: list[str] = []
    checklist: list[schemas.EngineChecklistItem] = []

    # REAL daily loss gate
    if daily_lockout_active(db, user.id):
        reasons.append("daily loss lockout active")
        checklist.append(schemas.EngineChecklistItem(key="daily_loss_gate", passed=False, detail="locked out for today"))
    else:
        checklist.append(schemas.EngineChecklistItem(key="daily_loss_gate", passed=True, detail="not locked out"))

    # Strategy exists
    if payload.strategy_id is not None:
        st = db.query(models.StrategyTemplate).filter(models.StrategyTemplate.id == payload.strategy_id).first()
        if not st:
            reasons.append("strategy_id not found")
            checklist.append(schemas.EngineChecklistItem(key="strategy_exists", passed=False, detail="strategy_id invalid"))
        else:
            if not is_admin(user) and st.user_id != user.id:
                reasons.append("not authorized to use this strategy")
                checklist.append(schemas.EngineChecklistItem(key="strategy_owner", passed=False, detail="strategy not owned"))
            else:
                checklist.append(schemas.EngineChecklistItem(key="strategy_exists", passed=True, detail="strategy found"))

    # Risk profile selection
    rp = None
    if payload.risk_profile_id is not None:
        rp = db.query(models.RiskProfile).filter(models.RiskProfile.id == payload.risk_profile_id).first()
        if not rp:
            reasons.append("risk_profile_id not found")
            checklist.append(schemas.EngineChecklistItem(key="risk_profile_exists", passed=False, detail="risk_profile_id invalid"))
        elif not is_admin(user) and rp.user_id != user.id:
            reasons.append("not authorized to use this risk profile")
            checklist.append(schemas.EngineChecklistItem(key="risk_profile_owner", passed=False, detail="risk profile not owned"))
        else:
            checklist.append(schemas.EngineChecklistItem(key="risk_profile_exists", passed=True, detail="risk profile found"))
    else:
        rp = get_default_risk_profile(db, user.id)
        checklist.append(schemas.EngineChecklistItem(
            key="risk_profile_default",
            passed=rp is not None,
            detail="default risk profile found" if rp else "no risk profile found (create one)"
        ))

    # Validate entry/stop
    if payload.entry_price is not None:
        if payload.stop_loss is None:
            reasons.append("stop_loss required when entry_price is provided")
            checklist.append(schemas.EngineChecklistItem(key="stop_required", passed=False, detail="stop_loss missing"))
        else:
            checklist.append(schemas.EngineChecklistItem(key="stop_required", passed=True, detail="stop_loss provided"))

        if payload.stop_loss is not None:
            if payload.direction == "long" and payload.stop_loss >= payload.entry_price:
                reasons.append("for long trades, stop_loss must be below entry_price")
                checklist.append(schemas.EngineChecklistItem(key="direction_stop_logic", passed=False, detail="SL not below entry for long"))
            elif payload.direction == "short" and payload.stop_loss <= payload.entry_price:
                reasons.append("for short trades, stop_loss must be above entry_price")
                checklist.append(schemas.EngineChecklistItem(key="direction_stop_logic", passed=False, detail="SL not above entry for short"))
            else:
                checklist.append(schemas.EngineChecklistItem(key="direction_stop_logic", passed=True, detail="direction/SL consistent"))
    else:
        checklist.append(schemas.EngineChecklistItem(key="entry_optional", passed=True, detail="entry_price not provided; plan limited"))

    # Calculations
    risk_amount = stop_distance = position_size_units = rr = None
    chosen_rp_id = rp.id if rp else None

    if rp and payload.entry_price is not None and payload.stop_loss is not None and len(reasons) == 0:
        ra, sd, units = calc_position_size(rp, payload.entry_price, payload.stop_loss)
        risk_amount = round_money(ra, 2) if ra is not None else None
        stop_distance = round_price(sd, 6) if sd is not None else None
        position_size_units = round_price(units, 2) if units is not None else None

    if payload.entry_price is not None and payload.stop_loss is not None and payload.take_profit is not None and len(reasons) == 0:
        rr_val = calc_rr(payload.direction, payload.entry_price, payload.stop_loss, payload.take_profit)
        rr = round_price(rr_val, 4) if rr_val is not None else None
        if rr is None:
            reasons.append("could not compute rr")
            checklist.append(schemas.EngineChecklistItem(key="rr_calc", passed=False, detail="invalid prices for rr"))
        else:
            passed = rr >= payload.rr_min
            checklist.append(schemas.EngineChecklistItem(key="rr_min", passed=passed, detail=f"RR={rr} (min {payload.rr_min})"))
            if not passed:
                reasons.append(f"RR below minimum ({payload.rr_min})")
    else:
        checklist.append(schemas.EngineChecklistItem(key="rr_min", passed=True, detail="TP not provided; rr gate skipped"))

    allowed = len(reasons) == 0
    recommendation = "place_order_or_wait_for_trigger" if allowed else "do_not_trade"

    return schemas.EnginePlanResponse(
        allowed=allowed,
        reasons=reasons,
        risk_profile_id=chosen_rp_id,
        risk_amount=risk_amount,
        stop_distance=stop_distance,
        position_size_units=position_size_units,
        rr=rr,
        checklist=checklist,
        recommendation=recommendation,
    )

@router.post("/plan", response_model=schemas.EnginePlanResponse)
def plan(payload: schemas.EnginePlanRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return build_plan(payload, db, user)

@router.post("/commit", response_model=schemas.EngineCommitResponse)
def commit(payload: schemas.EnginePlanRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    plan_obj = build_plan(payload, db, user)
    if not plan_obj.allowed:
        raise HTTPException(status_code=400, detail={"message": "Plan not allowed", "reasons": plan_obj.reasons})

    sig = models.Signal(
        user_id=user.id,
        strategy_id=payload.strategy_id,
        risk_profile_id=plan_obj.risk_profile_id,
        market=payload.market,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        direction=payload.direction,
        status="new",
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        rationale="Committed via /engine/commit",
        raw_data_json="{}",
        risk_amount=plan_obj.risk_amount,
        stop_distance=plan_obj.stop_distance,
        position_size_units=plan_obj.position_size_units,
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)

    draft = models.TradeJournalEntry(
        user_id=user.id,
        signal_id=sig.id,
        market=sig.market,
        symbol=sig.symbol,
        timeframe=sig.timeframe,
        direction=sig.direction,
        entry_price=sig.entry_price,
        exit_price=None,
        stop_loss=sig.stop_loss,
        take_profit=sig.take_profit,
        pnl=None,
        rr=plan_obj.rr,
        notes="DRAFT: created by /engine/commit. Fill after trade closes.",
        emotion=None,
        grade=None,
        adherence_score=None,
        is_finalized=False,
        closed_at=None,
        pnl_calc_mode=None,
        used_risk_profile_id=None,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    req_json = json.dumps(payload.model_dump(), ensure_ascii=False, default=str)
    resp_json = json.dumps(plan_obj.model_dump(), ensure_ascii=False, default=str)

    audit = models.AuditLog(
        user_id=user.id,
        action="engine.commit",
        entity_type="signal",
        entity_id=sig.id,
        request_json=req_json,
        response_json=resp_json,
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return schemas.EngineCommitResponse(plan=plan_obj, signal=sig, journal_draft=draft, audit_id=audit.id)

@router.get("/audit/me", response_model=list[schemas.AuditLogOut])
def audit_me(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    q = db.query(models.AuditLog).filter(models.AuditLog.user_id == user.id).order_by(models.AuditLog.id.desc())
    return q.offset(offset).limit(limit).all()

@router.get("/audit", response_model=list[schemas.AuditLogOut])
def audit_all(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    q = db.query(models.AuditLog).order_by(models.AuditLog.id.desc())
    return q.offset(offset).limit(limit).all()
