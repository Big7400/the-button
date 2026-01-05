from fastapi import FastAPI
from app.routers import auth  # Make sure auth.py is in app/routers

app = FastAPI(
    title="TheButtonApp API",
    description="API for user authentication and other routes",
    version="1.0.0"
)

# Register routers
app.include_router(auth.router)

# Simple health check
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is alive"}
