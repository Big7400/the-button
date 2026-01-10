# fix_all_phase4_4_finalize_lockout_hybrid.py
# Phase 4.4:
# - Hybrid journal finalize endpoint: manual pnl OR symbol-spec pnl OR fallback pnl
# - DailyMetrics + real daily lockout gate in engine
# - SymbolSpec admin CRUD (optional; engine uses it automatically if present)
# - Safe SQLite auto-migration (ALTER TABLE only when needed)
#
# NOTE: Does NOT delete app.db

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✅ wrote {rel_path}")


def main():
    # ---------------------------
    # app/models.py (add SymbolSpec + DailyMetric + journal finalize fields)
    # ---------------------------
    MODELS = r'''from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime, UniqueConstraint
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

    # Phase 4.4 finalize lifecycle
    is_finalized = Column(Boolean, default=False, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    pnl_calc_mode = Column(String, nullable=True)          # manual/spec/fallback
    used_risk_profile_id = Column(Integer, nullable=True)  # risk profile used for lockout calc


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


# ---------------------------
# Phase 4.4: Symbol Specs + Daily Metrics
# ---------------------------
class SymbolSpec(Base):
    __tablename__ = "symbol_specs"
    id = Column(Integer, primary_key=True, index=True)

    market = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)

    # what kind of calc to prefer (forex/futures/crypto/index/metals)
    kind = Column(String, default="forex", nullable=False)

    # forex-style
    contract_size = Column(Float, nullable=True)  # e.g. 100000 for 1 lot
    pip_size = Column(Float, nullable=True)       # e.g. 0.0001
    pip_value = Column(Float, nullable=True)      # value per pip per 1 lot (quote currency)

    # futures-style
    tick_size = Column(Float, nullable=True)      # e.g. 0.25
    tick_value = Column(Float, nullable=True)     # $ per tick per 1 contract

    # generic
    point_value = Column(Float, nullable=True)    # $ per 1.0 move per 1 unit/contract

    __table_args__ = (UniqueConstraint("market", "symbol", name="uq_symbolspec_market_symbol"),)


class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # store YYYY-MM-DD UTC
    day = Column(String, index=True, nullable=False)

    realized_pnl = Column(Float, default=0.0, nullable=False)
    locked_out = Column(Boolean, default=False, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_daily_user_day"),)
'''
    write("app/models.py", MODELS)

    # ---------------------------
    # app/core/migrations.py (SQLite auto-migration for added columns)
    # ---------------------------
    MIGRATIONS = r'''from sqlalchemy import text
from app.database import engine

def _has_column(table: str, col: str) -> bool:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    cols = {r[1] for r in rows}  # pragma: cid, name, type, notnull, dflt_value, pk
    return col in cols

def add_column_if_missing(table: str, col: str, ddl_type: str, default_sql: str | None = None):
    if _has_column(table, col):
        return
    ddl = f"ALTER TABLE {table} ADD COLUMN {col} {ddl_type}"
    if default_sql is not None:
        ddl += f" DEFAULT {default_sql}"
    with engine.begin() as conn:
        conn.execute(text(ddl))

def run_sqlite_migrations():
    # trade_journal_entries new columns (Phase 4.4)
    add_column_if_missing("trade_journal_entries", "is_finalized", "BOOLEAN", "0")
    add_column_if_missing("trade_journal_entries", "closed_at", "DATETIME")
    add_column_if_missing("trade_journal_entries", "pnl_calc_mode", "VARCHAR")
    add_column_if_missing("trade_journal_entries", "used_risk_profile_id", "INTEGER")
'''
    write("app/core/migrations.py", MIGRATIONS)

    # ---------------------------
    # app/schemas.py (add finalize + symbolspec + daily metrics)
    # Keep RoleUpdate present (admin router needs it)
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
    is_finalized: Optional[bool] = None
    closed_at: Optional[str] = None
    pnl_calc_mode: Optional[str] = None
    used_risk_profile_id: Optional[int] = None
    class Config:
        from_attributes = True

# ---- Phase 4.4 finalize request ----
class JournalFinalizeRequest(BaseModel):
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    notes: Optional[str] = None
    emotion: Optional[str] = None

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

# -------- Phase 4.4 Symbol Specs + Daily Metrics --------
class SymbolSpecCreate(BaseModel):
    market: str
    symbol: str
    kind: str = "forex"
    contract_size: Optional[float] = None
    pip_size: Optional[float] = None
    pip_value: Optional[float] = None
    tick_size: Optional[float] = None
    tick_value: Optional[float] = None
    point_value: Optional[float] = None

class SymbolSpecOut(SymbolSpecCreate):
    id: int
    class Config:
        from_attributes = True

class DailyMetricOut(BaseModel):
    id: int
    user_id: int
    day: str
    realized_pnl: float
    locked_out: bool
    class Config:
        from_attributes = True
'''
    write("app/schemas.py", SCHEMAS)

    # ---------------------------
    # app/routers/trading.py (add finalize + symbol spec + daily metrics endpoints)
    # NOTE: This overwrites trading router with all Phase 4 core CRUD + finalize additions.
    # ---------------------------
    TRADING = r'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user

router = APIRouter(prefix="/trading", tags=["trading"])

def is_admin(user: models.User) -> bool:
    return user.role is not None and user.role.name == "admin"

def utc_day_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def calc_rr(direction: str, entry: float, sl: float, tp: float | None):
    if tp is None:
        return None
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    reward = (tp - entry) if direction == "long" else (entry - tp)
    return reward / risk

def get_default_risk_profile(db: Session, user_id: int):
    rp = db.query(models.RiskProfile).filter(
        models.RiskProfile.user_id == user_id,
        models.RiskProfile.is_default == True
    ).first()
    if rp:
        return rp
    return db.query(models.RiskProfile).filter(models.RiskProfile.user_id == user_id).first()

def resolve_risk_profile_for_entry(db: Session, user_id: int, signal: models.Signal | None):
    # prefer signal.risk_profile_id, else default
    if signal and signal.risk_profile_id:
        rp = db.query(models.RiskProfile).filter(models.RiskProfile.id == signal.risk_profile_id).first()
        if rp and rp.user_id == user_id:
            return rp
    return get_default_risk_profile(db, user_id)

def get_or_create_daily_metric(db: Session, user_id: int, day: str):
    dm = db.query(models.DailyMetric).filter(models.DailyMetric.user_id == user_id, models.DailyMetric.day == day).first()
    if dm:
        return dm
    dm = models.DailyMetric(user_id=user_id, day=day, realized_pnl=0.0, locked_out=False)
    db.add(dm)
    db.commit()
    db.refresh(dm)
    return dm

def compute_pnl_hybrid(
    direction: str,
    entry: float,
    exit: float,
    units: float | None,
    spec: models.SymbolSpec | None,
):
    # returns (pnl, mode)
    if units is None:
        units = 0.0

    # Try spec-based
    if spec:
        # Forex: use pips * pip_value_per_lot * lots
        if spec.pip_size and spec.pip_value and spec.contract_size and spec.contract_size > 0:
            lots = units / spec.contract_size
            pips = (exit - entry) / spec.pip_size if direction == "long" else (entry - exit) / spec.pip_size
            pnl = pips * spec.pip_value * lots
            return float(pnl), "spec"

        # Futures-like: ticks * tick_value * contracts
        if spec.tick_size and spec.tick_value and spec.tick_size > 0:
            ticks = (exit - entry) / spec.tick_size if direction == "long" else (entry - exit) / spec.tick_size
            pnl = ticks * spec.tick_value * units
            return float(pnl), "spec"

        # Generic point value: points * point_value * units
        if spec.point_value:
            points = (exit - entry) if direction == "long" else (entry - exit)
            pnl = points * spec.point_value * units
            return float(pnl), "spec"

    # Fallback: points * units
    points = (exit - entry) if direction == "long" else (entry - exit)
    pnl = points * units
    return float(pnl), "fallback"

def auto_grade(adherence_score: int | None, rr: float | None, pnl: float | None):
    # simple, deterministic, upgrade later
    score = adherence_score if adherence_score is not None else 9
    if pnl is not None and pnl < 0:
        # losing trades can still be A if followed plan, but cap a bit
        score = min(score, 8)

    if score >= 9:
        return "A", score
    if score >= 7:
        return "B", score
    if score >= 5:
        return "C", score
    return "D", score

# ---------------------------
# Strategy CRUD
# ---------------------------
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

@router.patch("/strategies/{strategy_id}", response_model=schemas.StrategyTemplateOut)
def update_strategy(strategy_id: int, payload: schemas.StrategyTemplateUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    st = db.query(models.StrategyTemplate).filter(models.StrategyTemplate.id == strategy_id).first()
    if not st or (st.user_id != user.id and not is_admin(user)):
        raise HTTPException(status_code=404, detail="Strategy not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(st, k, v)
    db.commit()
    db.refresh(st)
    return st

# ---------------------------
# Risk Profile CRUD
# ---------------------------
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

@router.patch("/risk-profiles/{risk_id}", response_model=schemas.RiskProfileOut)
def update_risk_profile(risk_id: int, payload: schemas.RiskProfileUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rp = db.query(models.RiskProfile).filter(models.RiskProfile.id == risk_id).first()
    if not rp or (rp.user_id != user.id and not is_admin(user)):
        raise HTTPException(status_code=404, detail="Risk profile not found")
    if payload.is_default is True:
        db.query(models.RiskProfile).filter(models.RiskProfile.user_id == user.id).update({"is_default": False})
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(rp, k, v)
    db.commit()
    db.refresh(rp)
    return rp

# ---------------------------
# Signal CRUD (minimal list/create/update status)
# ---------------------------
@router.post("/signals", response_model=schemas.SignalOut)
def create_signal(payload: schemas.SignalCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sig = models.Signal(user_id=user.id, **payload.model_dump())
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig

@router.get("/signals", response_model=list[schemas.SignalOut])
def list_signals(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Signal).filter(models.Signal.user_id == user.id).order_by(models.Signal.id.desc()).all()

@router.patch("/signals/{signal_id}", response_model=schemas.SignalOut)
def update_signal(signal_id: int, payload: schemas.SignalUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sig = db.query(models.Signal).filter(models.Signal.id == signal_id).first()
    if not sig or (sig.user_id != user.id and not is_admin(user)):
        raise HTTPException(status_code=404, detail="Signal not found")

    # status transitions (same rules you proved)
    allowed_next = {
        "new": {"triggered", "cancelled"},
        "triggered": {"executed", "cancelled"},
        "executed": {"closed", "cancelled"},
        "closed": set(),
        "cancelled": set(),
    }
    updates = payload.model_dump(exclude_unset=True)

    if "status" in updates:
        curr = sig.status
        nxt = updates["status"]
        if nxt != curr and nxt not in allowed_next.get(curr, set()):
            raise HTTPException(status_code=400, detail=f"Invalid status transition: {curr} -> {nxt}")

    for k, v in updates.items():
        setattr(sig, k, v)

    db.commit()
    db.refresh(sig)
    return sig

# ---------------------------
# Journal CRUD + Finalize (Phase 4.4)
# ---------------------------
@router.post("/journal", response_model=schemas.TradeJournalOut)
def create_journal(payload: schemas.TradeJournalCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    j = models.TradeJournalEntry(user_id=user.id, is_finalized=False, **payload.model_dump())
    db.add(j)
    db.commit()
    db.refresh(j)
    return j

@router.get("/journal", response_model=list[schemas.TradeJournalOut])
def list_journal(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.TradeJournalEntry).filter(models.TradeJournalEntry.user_id == user.id).order_by(models.TradeJournalEntry.id.desc()).all()

@router.post("/journal/{journal_id}/finalize", response_model=schemas.TradeJournalOut)
def finalize_journal(journal_id: int, payload: schemas.JournalFinalizeRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    j = db.query(models.TradeJournalEntry).filter(models.TradeJournalEntry.id == journal_id).first()
    if not j or (j.user_id != user.id and not is_admin(user)):
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if j.is_finalized:
        raise HTTPException(status_code=400, detail="Journal already finalized")

    # Apply optional updates
    if payload.notes is not None:
        j.notes = payload.notes
    if payload.emotion is not None:
        j.emotion = payload.emotion

    # Resolve linked signal (for units + rp)
    sig = None
    if j.signal_id:
        sig = db.query(models.Signal).filter(models.Signal.id == j.signal_id).first()

    # Must have entry + exit to compute (unless pnl supplied)
    entry = j.entry_price
    exit_price = payload.exit_price if payload.exit_price is not None else j.exit_price
    if payload.exit_price is not None:
        j.exit_price = payload.exit_price

    # Compute rr if possible
    if j.rr is None and j.entry_price is not None and j.stop_loss is not None and j.take_profit is not None:
        rr_val = calc_rr(j.direction, j.entry_price, j.stop_loss, j.take_profit)
        if rr_val is not None:
            j.rr = float(round(rr_val, 4))

    # PnL: hybrid
    if payload.pnl is not None:
        j.pnl = float(payload.pnl)
        j.pnl_calc_mode = "manual"
    else:
        if entry is None or exit_price is None:
            raise HTTPException(status_code=400, detail="Provide exit_price (or pnl) to finalize")

        units = sig.position_size_units if sig and sig.position_size_units is not None else None
        spec = db.query(models.SymbolSpec).filter(models.SymbolSpec.market == j.market, models.SymbolSpec.symbol == j.symbol).first()
        pnl_val, mode = compute_pnl_hybrid(j.direction, float(entry), float(exit_price), units, spec)
        j.pnl = float(round(pnl_val, 2))
        j.pnl_calc_mode = mode

    # Auto grade/adherence (placeholder deterministic rules)
    grade, score = auto_grade(j.adherence_score, j.rr, j.pnl)
    j.grade = grade
    j.adherence_score = score

    # finalize
    j.is_finalized = True
    j.closed_at = datetime.now(timezone.utc)

    # Daily metrics + lockout
    rp = resolve_risk_profile_for_entry(db, user.id, sig)
    if rp:
        j.used_risk_profile_id = rp.id

    day = utc_day_str()
    dm = get_or_create_daily_metric(db, user.id, day)
    dm.realized_pnl = float(dm.realized_pnl) + float(j.pnl or 0.0)

    # lockout threshold
    if rp:
        threshold = rp.account_balance * (rp.max_daily_loss_pct / 100.0)
        if dm.realized_pnl <= -abs(threshold):
            dm.locked_out = True

    db.commit()
    db.refresh(j)
    return j

# ---------------------------
# Daily metrics endpoints
# ---------------------------
@router.get("/metrics/daily", response_model=list[schemas.DailyMetricOut])
def list_daily_metrics(limit: int = 30, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.DailyMetric).filter(models.DailyMetric.user_id == user.id).order_by(models.DailyMetric.id.desc()).limit(limit).all()

# ---------------------------
# Symbol specs (admin-only)
# ---------------------------
@router.post("/symbol-specs", response_model=schemas.SymbolSpecOut)
def create_symbol_spec(payload: schemas.SymbolSpecCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    existing = db.query(models.SymbolSpec).filter(models.SymbolSpec.market == payload.market, models.SymbolSpec.symbol == payload.symbol).first()
    if existing:
        raise HTTPException(status_code=400, detail="SymbolSpec already exists for this market+symbol")
    spec = models.SymbolSpec(**payload.model_dump())
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec

@router.get("/symbol-specs", response_model=list[schemas.SymbolSpecOut])
def list_symbol_specs(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(models.SymbolSpec).order_by(models.SymbolSpec.id.desc()).all()
'''
    write("app/routers/trading.py", TRADING)

    # ---------------------------
    # app/routers/engine.py (add real daily lockout gate)
    # ---------------------------
    ENGINE = r'''from fastapi import APIRouter, Depends, HTTPException
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
'''
    write("app/routers/engine.py", ENGINE)

    # ---------------------------
    # app/main.py (run migrations + create_all)
    # ---------------------------
    MAIN = r'''from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app import models
from app.core.migrations import run_sqlite_migrations
from app.routers import auth, users, admin, trading, engine as engine_router

app = FastAPI(title="TheButtonApp API")

@app.on_event("startup")
def startup():
    # create tables (new tables)
    Base.metadata.create_all(bind=engine)

    # add missing columns to existing tables safely (SQLite)
    run_sqlite_migrations()

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

    print("\n🎉 Phase 4.4 installed:")
    print("- POST /trading/journal/{id}/finalize (hybrid pnl + grade + metrics)")
    print("- GET  /trading/metrics/daily")
    print("- Admin: POST/GET /trading/symbol-specs")
    print("- Engine /plan now blocks if daily lockout active")
    print("\nNext:")
    print("python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")


if __name__ == "__main__":
    main()

