from sqlalchemy import text
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
