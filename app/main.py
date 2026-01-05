# app/main.py
from fastapi import FastAPI
from app.routers import auth  # import your auth router

app = FastAPI()

# Register the router
app.include_router(auth.router, prefix="/auth")
