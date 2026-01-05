from fastapi import FastAPI
from backend.api import auth  # import auth router

app = FastAPI(title="TheButtonApp API", version="0.1.0")

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "API is alive"}
