from fastapi import FastAPI
from app.routers import auth, users
from app.database import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TheButtonApp API")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/health")
def health():
    return {"status": "ok"}
