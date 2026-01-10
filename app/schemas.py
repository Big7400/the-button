from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RoleUpdate(BaseModel):
    role_name: str

class ActiveUpdate(BaseModel):
    is_active: bool

# Strategy schemas
class StrategyTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rules_json: Optional[str] = None

class StrategyTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules_json: Optional[str] = None

class StrategyTemplateOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    rules_json: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Risk Profile schemas
class RiskProfileCreate(BaseModel):
    name: str
    account_balance: float
    risk_per_trade_pct: float
    max_daily_loss_pct: float
    is_default: bool = False
    max_trades_per_day: Optional[int] = None
    max_consecutive_losses: Optional[int] = None

class RiskProfileUpdate(BaseModel):
    name: Optional[str] = None
    account_balance: Optional[float] = None
    risk_per_trade_pct: Optional[float] = None
    max_daily_loss_pct: Optional[float] = None
    is_default: Optional[bool] = None
    max_trades_per_day: Optional[int] = None
    max_consecutive_losses: Optional[int] = None

class RiskProfileOut(BaseModel):
    id: int
    user_id: int
    name: str
    account_balance: float
    risk_per_trade_pct: float
    max_daily_loss_pct: float
    is_default: bool
    max_trades_per_day: Optional[int]
    max_consecutive_losses: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

# Signal schemas
class SignalCreate(BaseModel):
    strategy_id: Optional[int] = None
    risk_profile_id: Optional[int] = None
    market: str
    symbol: str
    timeframe: str
    direction: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rationale: Optional[str] = None

class SignalUpdate(BaseModel):
    status: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rationale: Optional[str] = None

class SignalOut(BaseModel):
    id: int
    user_id: int
    strategy_id: Optional[int]
    risk_profile_id: Optional[int]
    market: str
    symbol: str
    timeframe: str
    direction: str
    status: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_amount: Optional[float]
    stop_distance: Optional[float]
    position_size_units: Optional[float]
    rationale: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Journal schemas
class TradeJournalCreate(BaseModel):
    signal_id: Optional[int] = None
    market: str
    symbol: str
    timeframe: str
    direction: str
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None
    emotion: Optional[str] = None

class JournalFinalizeRequest(BaseModel):
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    notes: Optional[str] = None
    emotion: Optional[str] = None

class TradeJournalOut(BaseModel):
    id: int
    user_id: int
    signal_id: Optional[int]
    market: str
    symbol: str
    timeframe: str
    direction: str
    entry_price: Optional[float]
    exit_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    pnl: Optional[float]
    rr: Optional[float]
    notes: Optional[str]
    emotion: Optional[str]
    grade: Optional[str]
    adherence_score: Optional[int]
    is_finalized: bool
    closed_at: Optional[datetime]
    pnl_calc_mode: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
        # Engine schemas
class EnginePlanRequest(BaseModel):
    strategy_id: Optional[int] = None
    risk_profile_id: Optional[int] = None
    market: str
    symbol: str
    timeframe: str
    direction: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rr_min: float = 1.5

class EngineChecklistItem(BaseModel):
    key: str
    passed: bool
    detail: str

class EnginePlanResponse(BaseModel):
    allowed: bool
    reasons: list[str]
    risk_profile_id: Optional[int]
    risk_amount: Optional[float]
    stop_distance: Optional[float]
    position_size_units: Optional[float]
    rr: Optional[float]
    checklist: list[EngineChecklistItem]
    recommendation: str

class EngineCommitResponse(BaseModel):
    plan: EnginePlanResponse
    signal: SignalOut
    journal_draft: TradeJournalOut
    audit_id: int

# Daily Metric schemas
class DailyMetricOut(BaseModel):
    id: int
    user_id: int
    day: str
    realized_pnl: float
    locked_out: bool
    trades_today: int
    consecutive_losses: int
    created_at: datetime
    class Config:
        from_attributes = True

# Audit Log schemas
class AuditLogOut(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

# Symbol Spec schemas
class SymbolSpecCreate(BaseModel):
    market: str
    symbol: str
    pip_size: Optional[float] = None
    pip_value: Optional[float] = None
    contract_size: Optional[float] = None
    tick_size: Optional[float] = None
    tick_value: Optional[float] = None
    point_value: Optional[float] = None

class SymbolSpecOut(BaseModel):
    id: int
    market: str
    symbol: str
    pip_size: Optional[float]
    pip_value: Optional[float]
    contract_size: Optional[float]
    tick_size: Optional[float]
    tick_value: Optional[float]
    point_value: Optional[float]
    created_at: datetime
    class Config:
        from_attributes = True