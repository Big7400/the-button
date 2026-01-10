# fix_all_phase4_2_one_button_engine.py
# Adds POST /engine/plan (One-Button Trade Plan Engine)
# Keeps admin schemas (RoleUpdate/ActiveUpdate) + trading schemas.
# Does NOT delete app.db (no DB schema change in 4.2).

from pathlib import Path

ROOT = Path(__file__).resolve().parent

def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✅ wrote {rel_path}")

def main():
    # --- app/schemas.py ---
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
'''
    write("app/schemas.py", SCHEMAS)

    # --- app/routers/engine.py ---
    ENGINE = r'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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

@router.post("/plan", response_model=schemas.EnginePlanResponse)
def plan(payload: schemas.EnginePlanRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    reasons: list[str] = []
    checklist: list[schemas.EngineChecklistItem] = []

    # --- Strategy exists (if provided) ---
    if payload.strategy_id is not None:
        st = db.query(models.StrategyTemplate).filter(models.StrategyTemplate.id == payload.strategy_id).first()
        if not st:
            reasons.append("strategy_id not found")
            checklist.append(schemas.EngineChecklistItem(key="strategy_exists", passed=False, detail="strategy_id invalid"))
        else:
            if user.role.name != "admin" and st.user_id != user.id:
                reasons.append("not authorized to use this strategy")
                checklist.append(schemas.EngineChecklistItem(key="strategy_owner", passed=False, detail="strategy not owned"))
            else:
                checklist.append(schemas.EngineChecklistItem(key="strategy_exists", passed=True, detail="strategy found"))

    # --- Risk profile selection ---
    rp = None
    if payload.risk_profile_id is not None:
        rp = db.query(models.RiskProfile).filter(models.RiskProfile.id == payload.risk_profile_id).first()
        if not rp:
            reasons.append("risk_profile_id not found")
            checklist.append(schemas.EngineChecklistItem(key="risk_profile_exists", passed=False, detail="risk_profile_id invalid"))
        elif user.role.name != "admin" and rp.user_id != user.id:
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

    # --- Validate entry/stop ---
    if payload.entry_price is not None:
        if payload.stop_loss is None:
            reasons.append("stop_loss required when entry_price is provided")
            checklist.append(schemas.EngineChecklistItem(key="stop_required", passed=False, detail="stop_loss missing"))
        else:
            checklist.append(schemas.EngineChecklistItem(key="stop_required", passed=True, detail="stop_loss provided"))

        # direction sanity
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

    # --- Daily loss gate scaffold (placeholder until you track PnL per day) ---
    checklist.append(schemas.EngineChecklistItem(key="daily_loss_gate", passed=True, detail="no daily-loss lockout set"))

    # --- Calculations ---
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
'''
    write("app/routers/engine.py", ENGINE)

    # --- app/main.py (include engine router) ---
    # Keep your existing imports/routers; we add engine.
    MAIN = r'''from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app import models
from app.routers import auth, users, admin, trading, engine as engine_router

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
app.include_router(engine_router.router)

@app.get("/health")
def health():
    return {"status": "ok"}
'''
    write("app/main.py", MAIN)

    # --- app/routers/__init__.py ---
    write("app/routers/__init__.py", "")

    print("\n🎉 Phase 4.2 installed: POST /engine/plan is live.")
    print("Next:")
    print("python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload")
    print("Then test /engine/plan with curl.")

if __name__ == "__main__":
    main()

