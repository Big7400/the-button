# fix_all_phase4_3_commit_audit.py
# Phase 4.3: /engine/commit + AuditLog + auto Journal Draft
# - Adds AuditLog table (no DB wipe)
# - Adds /engine/commit, /engine/audit/me, /engine/audit (admin-only)
# - commit creates Signal + Journal Draft + Audit record

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✅ wrote {rel_path}")


def main():
    # ---------------------------
    # app/models.py (ADD AuditLog)
    # ---------------------------
    MODELS = r'''from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

# ---------------------------
# Roles / Users
# ---------------------------
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    role = relationship("Role", back_populates="users")


# ---------------------------
# Trading Core
# ---------------------------
class StrategyTemplate(Base):
    __tablename__ = "strategy_templates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    name = Column(String, index=True, nullable=False)
    market = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    rules_json = Column(Text, default="{}", nullable=False)
    is_active = Column(Boolean, default=True)

class RiskProfile(Base):
    __tablename__ = "risk_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    name = Column(String, index=True, nullable=False)

    account_balance = Column(Float, default=10000.0, nullable=False)
    account_currency = Column(String, default="USD", nullable=False)

    risk_per_trade_pct = Column(Float, default=1.0, nullable=False)
    max_daily_loss_pct = Column(Float, default=3.0, nullable=False)
    max_weekly_loss_pct = Column(Float, default=8.0, nullable=False)

    position_sizing_mode = Column(String, default="fixed_percent", nullable=False)
    notes = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    strategy_id = Column(Integer, ForeignKey("strategy_templates.id"), nullable=True)
    risk_profile_id = Column(Integer, ForeignKey("risk_profiles.id"), nullable=True)

    market = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=True)
    direction = Column(String, nullable=False)

    status = Column(String, default="new", nullable=False)

    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    rationale = Column(Text, nullable=True)
    raw_data_json = Column(Text, default="{}", nullable=False)

    # auto sizing fields
    risk_amount = Column(Float, nullable=True)
    stop_distance = Column(Float, nullable=True)
    position_size_units = Column(Float, nullable=True)

class TradeJournalEntry(Base):
    __tablename__ = "trade_journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)

    market = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=True)
    direction = Column(String, nullable=False)

    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)

    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    pnl = Column(Float, nullable=True)
    rr = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)
    emotion = Column(String, nullable=True)

    grade = Column(String, nullable=True)
    adherence_score = Column(Integer, nullable=True)

# ---------------------------
# Phase 4.3: Audit Log
# ---------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    action = Column(String, index=True, nullable=False)          # e.g. engine.commit
    entity_type = Column(String, index=True, nullable=False)     # e.g. signal
    entity_id = Column(Integer, index=True, nullable=True)       # e.g. signal.id

    request_json = Column(Text, nullable=False)
    response_json = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
'''
    write("app/models.py", MODELS)

    # ---------------------------
    # app/schemas.py (ADD audit + commit response)
    # Keep everything Phase 4.2 had.
    # ---------------------------
    SCHEMAS = r'''from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal

# -------- Auth/User --------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# -------- Admin (required by admin.py) --------
class RoleUpdate(BaseModel):
    role_name: str

class ActiveUpdate(BaseModel):
    is_active: bool

# -------- Trading Core --------
class StrategyTemplateCreate(BaseModel):
    name: str
    market: str
    timeframe: Optional[str] = None
    description: Optional[str] = None
    rules_json: str = "{}"
    is_active: bool = True

class StrategyTemplateUpdate(BaseModel):
    name: Optional[str] = None
    market: Optional[str] = None
    timeframe: Optional[str] = None
    description: Optional[str] = None
    rules_json: Optional[str] = None
    is_active: Optional[bool] = None

class StrategyTemplateOut(BaseModel):
    id: int
    user_id: int
    name: str
    market: str
    timeframe: Optional[str] = None
    description: Optional[str] = None
    rules_json: str
    is_active: bool
    class Config:
        from_attributes = True

class RiskProfileCreate(BaseModel):
    name: str
    account_balance: float = 10000.0
    account_currency: str = "USD"
    risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_weekly_loss_pct: float = 8.0
    position_sizing_mode: str = "fixed_percent"
    notes: Optional[str] = None
    is_default: bool = False

class RiskProfileUpdate(BaseModel):
    name: Optional[str] = None
    account_balance: Optional[float] = None
    account_currency: Optional[str] = None
    risk_per_trade_pct: Optional[float] = None
    max_daily_loss_pct: Optional[float] = None
    max_weekly_loss_pct: Optional[float] = None
    position_sizing_mode: Optional[str] = None
    notes: Optional[str] = None
    is_default: Optional[bool] = None

class RiskProfileOut(BaseModel):
    id: int
    user_id: int
    name: str
    account_balance: float
    account_currency: str
    risk_per_trade_pct: float
    max_daily_loss_pct: float
    max_weekly_loss_pct: float
    position_sizing_mode: str
    notes: Optional[str] = None
    is_default: bool
    class Config:
        from_attributes = True

class SignalCreate(BaseModel):
    strategy_id: Optional[int] = None
    risk_profile_id: Optional[int] = None
    market: str
    symbol: str
    timeframe: Optional[str] = None
    direction: str
    status: str = "new"
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rationale: Optional[str] = None
    raw_data_json: str = "{}"

class SignalUpdate(BaseModel):
    strategy_id: Optional[int] = None
    risk_profile_id: Optional[int] = None
    market: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    direction: Optional[str] = None
    status: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rationale: Optional[str] = None
    raw_data_json: Optional[str] = None

class SignalOut(BaseModel):
    id: int
    user_id: int
    strategy_id: Optional[int] = None
    risk_profile_id: Optional[int] = None
    market: str
    symbol: str
    timeframe: Optional[str] = None
    direction: str
    status: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rationale: Optional[str] = None
    raw_data_json: str
    risk_amount: Optional[float] = None
    stop_distance: Optional[float] = None
    position_size_units: Optional[float] = None
    class Config:
        from_attributes = True

class TradeJournalCreate(BaseModel):
    signal_id: Optional[int] = None
    market: str
    symbol: str
    timeframe: Optional[str] = None
    direction: str
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: Optional[float] = None
    rr: Optional[float] = None
    notes: Optional[str] = None
    emotion: Optional[str] = None
    grade: Optional[str] = None
    adherence_score: Optional[int] = None

class TradeJournalOut(BaseModel):
    id: int
    user_id: int
    signal_id: Optional[int] = None
    market: str
    symbol: str
    timeframe: Optional[str] = None
    direction: str
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: Optional[float] = None
    rr: Optional[float] = None
    notes: Optional[str] = None
    emotion: Optional[str] = None
    grade: Optional[str] = None
    adherence_score: Optional[int] = None
    class Config:
        from_attributes = True

# -------- Phase 4.2 Engine --------
class EnginePlanRequest(BaseModel):
    market: str
    symbol: str
    timeframe: Optional[str] = None
    direction: Literal["long", "short"]
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_id: Optional[int] = None
    risk_profile_id: Optional[int] = None
    rr_min: float = 1.5

class EngineChecklistItem(BaseModel):
    key: str
    passed: bool
    detail: str

class EnginePlanResponse(BaseModel):
    allowed: bool
    reasons: List[str]
    risk_profile_id: Optional[int] = None
    risk_amount: Optional[float] = None
    stop_distance: Optional[float] = None
    position_size_units: Optional[float] = None
    rr: Optional[float] = None
    checklist: List[EngineChecklistItem]
    recommendation: str

# -------- Phase 4.3 Commit + Audit --------
class AuditLogOut(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    request_json: str
    response_json: str
    created_at: str
    class Config:
        from_attributes = True

class EngineCommitResponse(BaseModel):
    plan: EnginePlanResponse
    signal: SignalOut
    journal_draft: TradeJournalOut
    audit_id: int
'''
    write("app/schemas.py", SCHEMAS)

    # ---------------------------
    # app/routers/engine.py (ADD commit + audit endpoints)
    # ---------------------------
    ENGINE = r'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime

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

def is_admin(user: models.User) -> bool:
    try:
        return user.role is not None and user.role.name == "admin"
    except Exception:
        return False

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

def build_plan(payload: schemas.EnginePlanRequest, db: Session, user: models.User) -> schemas.EnginePlanResponse:
    reasons: list[str] = []
    checklist: list[schemas.EngineChecklistItem] = []

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

    # Daily loss gate scaffold
    checklist.append(schemas.EngineChecklistItem(key="daily_loss_gate", passed=True, detail="no daily-loss lockout set"))

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

    # Create Signal (status=new)
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

    # Create Journal Draft (blank exit/pnl, etc.)
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
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    # Audit Log
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

    return schemas.EngineCommitResponse(
        plan=plan_obj,
        signal=sig,
        journal_draft=draft,
        audit_id=audit.id,
    )

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
'''
    write("app/routers/engine.py", ENGINE)

    # ---------------------------
    # app/main.py (ensure create_all still runs + include engine router)
    # ---------------------------
    MAIN = r'''from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app import models
from app.routers import auth, users, admin, trading, engine as engine_router

app = FastAPI(title="TheButtonApp API")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    # Ensure roles exist
    db = SessionLocal()
    for name in ["user", "admin"]:
        if not db.query(models.Role).filter_by(name=name).first():
            db.add(models.Role(name=name))
    db.commit()
    db.close()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(trading.router)
app.include_router(engine_router.router)

@app.get("/health")
def health():
    return {"status": "ok"}
'''
    write("app/main.py", MAIN)

    print("\n🎉 Phase 4.3 installed: POST /engine/commit + audit logs + journal drafts.")
    print("Next:")
    print("python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")
    print("Then test with curl: /engine/commit, /engine/audit/me")


if __name__ == "__main__":
    main()

