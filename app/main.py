from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="JWT Auth App")

# Include the auth router
app.include_router(auth.router, prefix="/auth")
