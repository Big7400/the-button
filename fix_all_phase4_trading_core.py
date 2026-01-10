from pathlib import Path

ROOT = Path(__file__).resolve().parent

def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✅ wrote {rel_path}")

def main():
    # Reset DB (schema additions)
    db = ROOT / "app.db"
    if db.exists():
        db.unlink()
        print("🧹 removed app.db (fresh schema for Phase 4)")

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
    market = Column(String, nullable=False)      # forex/indices/metals/crypto/futures
    timeframe = Column(String, nullable=True)    # 5m/15m/1h/4h etc.
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
    status = Column(String, nullable=False, default="new")  # new/triggered/invalidated/executed

    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    rationale = Column(Text, nullable=True)
    raw_data_json = Column(Text, nullable=False, default="{}")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="signals")
    strategy = relationship("StrategyTemplate")

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
    grade = Column(String, nullable=True)
    adherence_score = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="journal_entries")
    signal = relationship("Signal")
'''

    SCHEMAS = r'''from pydantic import BaseModel, EmailStr, Field
from typing import Optional

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

class RoleUpdate(BaseModel):
    role_name: str

class ActiveUpdate(BaseModel):
    is_active: bool

# ---------- Trading Core ----------
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
    risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_weekly_loss_pct: float = 8.0
    position_sizing_mode: str = "fixed_percent"
    notes: Optional[str] = None
    is_default: bool = False

class RiskProfileUpdate(BaseModel):
    name: Optional[str] = None
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

    TRADING = r'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user

router = APIRouter(prefix="/trading", tags=["trading"])

def owned_or_404(db: Session, model, obj_id: int, user: models.User):
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(404, "Not found")
    if user.role.name != "admin" and getattr(obj, "user_id", None) != user.id:
        raise HTTPException(403, "Not authorized")
    return obj

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
    if user.role.name == "admin":
        return db.query(models.StrategyTemplate).all()
    return db.query(models.StrategyTemplate).filter(models.StrategyTemplate.user_id == user.id).all()

@router.get("/strategies/{strategy_id}", response_model=schemas.StrategyTemplateOut)
def get_strategy(strategy_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return owned_or_404(db, models.StrategyTemplate, strategy_id, user)

@router.patch("/strategies/{strategy_id}", response_model=schemas.StrategyTemplateOut)
def update_strategy(strategy_id: int, payload: schemas.StrategyTemplateUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    s = owned_or_404(db, models.StrategyTemplate, strategy_id, user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s

@router.delete("/strategies/{strategy_id}")
def delete_strategy(strategy_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    s = owned_or_404(db, models.StrategyTemplate, strategy_id, user)
    db.delete(s)
    db.commit()
    return {"status": "deleted"}

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
    if user.role.name == "admin":
        return db.query(models.RiskProfile).all()
    return db.query(models.RiskProfile).filter(models.RiskProfile.user_id == user.id).all()

@router.get("/risk-profiles/{rp_id}", response_model=schemas.RiskProfileOut)
def get_risk_profile(rp_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return owned_or_404(db, models.RiskProfile, rp_id, user)

@router.patch("/risk-profiles/{rp_id}", response_model=schemas.RiskProfileOut)
def update_risk_profile(rp_id: int, payload: schemas.RiskProfileUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rp = owned_or_404(db, models.RiskProfile, rp_id, user)
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default") is True:
        db.query(models.RiskProfile).filter(models.RiskProfile.user_id == rp.user_id).update({"is_default": False})
    for k, v in data.items():
        setattr(rp, k, v)
    db.commit()
    db.refresh(rp)
    return rp

@router.delete("/risk-profiles/{rp_id}")
def delete_risk_profile(rp_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rp = owned_or_404(db, models.RiskProfile, rp_id, user)
    db.delete(rp)
    db.commit()
    return {"status": "deleted"}

# -------- Signals --------
@router.post("/signals", response_model=schemas.SignalOut)
def create_signal(payload: schemas.SignalCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sig = models.Signal(user_id=user.id, **payload.model_dump())
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig

@router.get("/signals", response_model=list[schemas.SignalOut])
def list_signals(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role.name == "admin":
        return db.query(models.Signal).all()
    return db.query(models.Signal).filter(models.Signal.user_id == user.id).all()

@router.get("/signals/{signal_id}", response_model=schemas.SignalOut)
def get_signal(signal_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return owned_or_404(db, models.Signal, signal_id, user)

@router.patch("/signals/{signal_id}", response_model=schemas.SignalOut)
def update_signal(signal_id: int, payload: schemas.SignalUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sig = owned_or_404(db, models.Signal, signal_id, user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(sig, k, v)
    db.commit()
    db.refresh(sig)
    return sig

@router.delete("/signals/{signal_id}")
def delete_signal(signal_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sig = owned_or_404(db, models.Signal, signal_id, user)
    db.delete(sig)
    db.commit()
    return {"status": "deleted"}

# -------- Journal --------
@router.post("/journal", response_model=schemas.TradeJournalOut)
def create_journal(payload: schemas.TradeJournalCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    j = models.TradeJournalEntry(user_id=user.id, **payload.model_dump())
    db.add(j)
    db.commit()
    db.refresh(j)
    return j

@router.get("/journal", response_model=list[schemas.TradeJournalOut])
def list_journal(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role.name == "admin":
        return db.query(models.TradeJournalEntry).all()
    return db.query(models.TradeJournalEntry).filter(models.TradeJournalEntry.user_id == user.id).all()

@router.get("/journal/{entry_id}", response_model=schemas.TradeJournalOut)
def get_journal(entry_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return owned_or_404(db, models.TradeJournalEntry, entry_id, user)

@router.patch("/journal/{entry_id}", response_model=schemas.TradeJournalOut)
def update_journal(entry_id: int, payload: schemas.TradeJournalUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    j = owned_or_404(db, models.TradeJournalEntry, entry_id, user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(j, k, v)
    db.commit()
    db.refresh(j)
    return j

@router.delete("/journal/{entry_id}")
def delete_journal(entry_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    j = owned_or_404(db, models.TradeJournalEntry, entry_id, user)
    db.delete(j)
    db.commit()
    return {"status": "deleted"}
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

    write("app/models.py", MODELS)
    write("app/schemas.py", SCHEMAS)
    write("app/routers/trading.py", TRADING)
    write("app/main.py", MAIN)
    write("app/routers/__init__.py", "")

    print("\n🎉 Phase 4 Trading Core installed (quote-safe).")
    print("Next:")
    print("python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")

if __name__ == "__main__":
    main()

