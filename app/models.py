from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship  
from sqlalchemy.sql import func
from app.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    role = relationship("Role")

class StrategyTemplate(Base):
    __tablename__ = "strategy_templates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rules_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RiskProfile(Base):
    __tablename__ = "risk_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    account_balance = Column(Float, nullable=False)
    risk_per_trade_pct = Column(Float, nullable=False)
    max_daily_loss_pct = Column(Float, nullable=False)
    is_default = Column(Boolean, default=False)
    max_trades_per_day = Column(Integer, nullable=True)
    max_consecutive_losses = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategy_templates.id"), nullable=True)
    risk_profile_id = Column(Integer, ForeignKey("risk_profiles.id"), nullable=True)
    market = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    status = Column(String, default="new")
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    risk_amount = Column(Float, nullable=True)
    stop_distance = Column(Float, nullable=True)
    position_size_units = Column(Float, nullable=True)
    rationale = Column(Text, nullable=True)
    raw_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TradeJournalEntry(Base):
    __tablename__ = "trade_journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    market = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
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
    is_finalized = Column(Boolean, default=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    pnl_calc_mode = Column(String, nullable=True)
    used_risk_profile_id = Column(Integer, ForeignKey("risk_profiles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day = Column(String, nullable=False)
    realized_pnl = Column(Float, default=0.0)
    locked_out = Column(Boolean, default=False)
    trades_today = Column(Integer, default=0)
    consecutive_losses = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    request_json = Column(Text, nullable=True)
    response_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SymbolSpec(Base):
    __tablename__ = "symbol_specs"
    id = Column(Integer, primary_key=True, index=True)
    market = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    pip_size = Column(Float, nullable=True)
    pip_value = Column(Float, nullable=True)
    contract_size = Column(Float, nullable=True)
    tick_size = Column(Float, nullable=True)
    tick_value = Column(Float, nullable=True)
    point_value = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
