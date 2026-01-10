from fastapi import FastAPI
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
