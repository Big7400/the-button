# fix_all_phase4_4_1_finalize_500_hotfix.py
# Hotfix: response_model serialization for datetime fields (closed_at / created_at)
# No DB wipe. Just fixes schemas that caused 500s after successful commits.

from pathlib import Path

ROOT = Path(__file__).resolve().parent

def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✅ wrote {rel_path}")

def main():
    SCHEMAS = r'''from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime

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
    closed_at: Optional[datetime] = None
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
    created_at: datetime
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

    print("\n🎉 Hotfix applied: schemas now use real datetime fields.")
    print("Next: restart uvicorn.")

if __name__ == "__main__":
    main()

