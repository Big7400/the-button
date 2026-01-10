# fix_all_phase4_1_smart_engine_v2.py
# Quote-safe, full overwrite for Phase 4.1 including admin schemas (RoleUpdate/ActiveUpdate),
# plus smart engine: sizing, status transition enforcement, filters/pagination.
#
# NOTE: This script deletes app.db for a clean schema reset (no migrations).
# Usage:
#   1) CTRL+C uvicorn
#   2) python3 fix_all_phase4_1_smart_engine_v2.py
#   3) python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload

from pathlib import Path

ROOT = Path(__file__).resolve().parent

def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✅ wrote {rel_path}")

def main():
    # Reset DB (schema additions)
    db_file = ROOT / "app.db"
    if db_file.exists():
        db_file.unlink()
        print("🧹 removed app.db (fresh schema for Phase 4.1 v2)")

    MODELS = r'''from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    role = relationship("Role")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    strategies = relationship("StrategyTemplate", back_populates="owner", cascade="all, delete-orphan")
    risk_profiles = relationship("RiskProfile", back_populates="owner", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="owner", cascade="all, delete-orphan")
    journal_entries = relationship("TradeJournalEntry", back_populates="owner", cascade="all, delete-orphan")

class StrategyTemplate(Base):
    __tablename__ = "strategy_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    market = Column(String, nullable=False)
    timeframe = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    rules_json = Column(Text, nullable=False, default="{}")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="strategies")

class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)

    # Account sizing base
    account_balance = Column(Float, nullable=False, default=10000.0)
    account_currency = Column(String, nullable=False, default="USD")

    risk_per_trade_pct = Column(Float, nullable=False, default=1.0)
    max_daily_loss_pct = Column(Float, nullable=False, default=3.0)
    max_weekly_loss_pct = Column(Float, nullable=False, default=8.0)

    position_sizing_mode = Column(String, nullable=False, default="fixed_percent")
    notes = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="risk_profiles")

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    strategy_id = Column(Integer, ForeignKey("strategy_templates.id"), nullable=True, index=True)

    market = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=True)

    direction = Column(String, nullable=False)  # long/short

    # lifecycle states (enforced)
    status = Column(String, nullable=False, default="new")  # new/triggered/executed/invalidated

    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    rationale = Column(Text, nullable=True)
    raw_data_json = Column(Text, nullable=False, default="{}")

    # sizing outputs
    risk_profile_id = Column(Integer, ForeignKey("risk_profiles.id"), nullable=True, index=True)
    risk_amount = Column(Float, nullable=True)
    stop_distance = Column(Float, nullable=True)
    position_size_units = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="signals")
    strategy = relationship("StrategyTemplate")
    risk_profile = relationship("RiskProfile")

class TradeJournalEntry(Base):
    __tablename__ = "trade_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True, index=True)

    market = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
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

    grade = Column(String, nullable=True)             # A/B/C
    adherence_score = Column(Integer, nullable=True) # 1-10

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="journal_entries")
    signal = relationship("Signal")
'''

    SCHEMAS = r'''from pydantic import BaseModel, EmailStr, Field
from typing import Optional

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

# -------- Admin (needed by admin.py) --------
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

class TradeJournalUpdate(BaseModel):
    signal_id: Optional[int] = None
    market: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    direction: Optional[str] = None
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
'''

    TRADING = r'''from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user

router = APIRouter(prefix="/trading", tags=["trading"])

ALLOWED_TRANSITIONS = {
    "new": {"triggered", "invalidated"},
    "triggered": {"executed", "invalidated"},
    "executed": set(),
    "invalidated": set(),
}

def owned_or_404(db: Session, model, obj_id: int, user: models.User):
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(404, "Not found")
    if user.role.name != "admin" and getattr(obj, "user_id", None) != user.id:
        raise HTTPException(403, "Not authorized")
    return obj

def get_default_risk_profile(db: Session, user_id: int):
    rp = db.query(models.RiskProfile).filter(
        models.RiskProfile.user_id == user_id,
        models.RiskProfile.is_default == True
    ).first()
    if rp:
        return rp
    return db.query(models.RiskProfile).filter(models.RiskProfile.user_id == user_id).first()

def calc_position_size(rp: models.RiskProfile, entry: float, sl: float):
    stop_distance = abs(entry - sl)
    if stop_distance <= 0:
        return None, None, None
    risk_amount = rp.account_balance * (rp.risk_per_trade_pct / 100.0)
    position_units = risk_amount / stop_distance
    return risk_amount, stop_distance, position_units

# -------- Strategies --------
@router.post("/strategies", response_model=schemas.StrategyTemplateOut)
def create_strategy(payload: schemas.StrategyTemplateCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    s = models.StrategyTemplate(user_id=user.id, **payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@router.get("/strategies", response_model=list[schemas.StrategyTemplateOut])
def list_strategies(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    q = db.query(models.StrategyTemplate)
    if user.role.name != "admin":
        q = q.filter(models.StrategyTemplate.user_id == user.id)
    return q.all()

# -------- Risk Profiles --------
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
    q = db.query(models.RiskProfile)
    if user.role.name != "admin":
        q = q.filter(models.RiskProfile.user_id == user.id)
    return q.all()

# -------- Signals (filters + pagination + sizing + transition enforcement) --------
@router.post("/signals", response_model=schemas.SignalOut)
def create_signal(payload: schemas.SignalCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sig = models.Signal(user_id=user.id, **payload.model_dump())

    # risk profile selection
    rp = None
    if sig.risk_profile_id:
        rp = db.query(models.RiskProfile).filter(models.RiskProfile.id == sig.risk_profile_id).first()
        if not rp:
            raise HTTPException(400, "risk_profile_id not found")
        if user.role.name != "admin" and rp.user_id != user.id:
            raise HTTPException(403, "Not authorized to use this risk profile")
    else:
        rp = get_default_risk_profile(db, user.id)
        if rp:
            sig.risk_profile_id = rp.id

    # sizing
    if rp and sig.entry_price is not None and sig.stop_loss is not None:
        ra, sd, units = calc_position_size(rp, sig.entry_price, sig.stop_loss)
        sig.risk_amount = ra
        sig.stop_distance = sd
        sig.position_size_units = units

    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig

@router.get("/signals", response_model=list[schemas.SignalOut])
def list_signals(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    market: str | None = None,
    symbol: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.Signal)
    if user.role.name != "admin":
        q = q.filter(models.Signal.user_id == user.id)
    if market:
        q = q.filter(models.Signal.market == market)
    if symbol:
        q = q.filter(models.Signal.symbol == symbol)
    if status:
        q = q.filter(models.Signal.status == status)
    return q.order_by(models.Signal.id.desc()).offset(offset).limit(limit).all()

@router.patch("/signals/{signal_id}", response_model=schemas.SignalOut)
def update_signal(signal_id: int, payload: schemas.SignalUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sig = owned_or_404(db, models.Signal, signal_id, user)
    data = payload.model_dump(exclude_unset=True)

    # transition enforcement
    if "status" in data:
        new_status = data["status"]
        current = sig.status
        if new_status != current:
            allowed = ALLOWED_TRANSITIONS.get(current, set())
            if new_status not in allowed:
                raise HTTPException(400, f"Invalid status transition: {current} -> {new_status}")

    for k, v in data.items():
        setattr(sig, k, v)

    rp = None
    if sig.risk_profile_id:
        rp = db.query(models.RiskProfile).filter(models.RiskProfile.id == sig.risk_profile_id).first()

    if rp and sig.entry_price is not None and sig.stop_loss is not None:
        ra, sd, units = calc_position_size(rp, sig.entry_price, sig.stop_loss)
        sig.risk_amount = ra
        sig.stop_distance = sd
        sig.position_size_units = units

    db.commit()
    db.refresh(sig)
    return sig

# -------- Journal (filters + basic auto scoring) --------
def auto_score_journal(payload: schemas.TradeJournalCreate):
    score = payload.adherence_score
    grade = payload.grade

    if score is None:
        score = 7
        if payload.rr is not None and payload.rr >= 2:
            score += 1
        if payload.pnl is not None and payload.pnl > 0:
            score += 1
        if payload.emotion in ("FOMO", "revenge", "anxious"):
            score -= 2
        score = max(1, min(10, score))

    if grade is None:
        if score >= 9:
            grade = "A"
        elif score >= 7:
            grade = "B"
        else:
            grade = "C"

    return grade, score

@router.post("/journal", response_model=schemas.TradeJournalOut)
def create_journal(payload: schemas.TradeJournalCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    grade, score = auto_score_journal(payload)
    j = models.TradeJournalEntry(user_id=user.id, **payload.model_dump())
    j.grade = grade
    j.adherence_score = score
    db.add(j)
    db.commit()
    db.refresh(j)
    return j

@router.get("/journal", response_model=list[schemas.TradeJournalOut])
def list_journal(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    market: str | None = None,
    symbol: str | None = None,
    grade: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.TradeJournalEntry)
    if user.role.name != "admin":
        q = q.filter(models.TradeJournalEntry.user_id == user.id)
    if market:
        q = q.filter(models.TradeJournalEntry.market == market)
    if symbol:
        q = q.filter(models.TradeJournalEntry.symbol == symbol)
    if grade:
        q = q.filter(models.TradeJournalEntry.grade == grade)
    return q.order_by(models.TradeJournalEntry.id.desc()).offset(offset).limit(limit).all()
'''

    MAIN = r'''from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app import models
from app.routers import auth, users, admin, trading

app = FastAPI(title="TheButtonApp API")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
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

@app.get("/health")
def health():
    return {"status": "ok"}
'''

    ROUTERS_INIT = r''''''

    write("app/models.py", MODELS)
    write("app/schemas.py", SCHEMAS)
    write("app/routers/trading.py", TRADING)
    write("app/main.py", MAIN)
    write("app/routers/__init__.py", ROUTERS_INIT)

    print("\n🎉 Phase 4.1 Smart Engine v2 installed (admin schemas preserved).")
    print("Next:")
    print("python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")

if __name__ == "__main__":
    main()

