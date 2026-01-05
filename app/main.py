# app/main.py
from fastapi import FastAPI
from app.routers import auth  # make sure this matches your folder structure

app = FastAPI()

# Include the auth router
app.include_router(auth.router, prefix="/auth")  # <-- prefix is important
