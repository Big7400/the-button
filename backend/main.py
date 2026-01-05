from fastapi import FastAPI
from backend.api import users, auth  # import your routers

app = FastAPI(title="TheButtonApp API")

# Include routers
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])  # auth routes

@app.get("/")
def root():
    return {"status": "ok", "message": "API is alive"}
