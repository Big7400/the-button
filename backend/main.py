from fastapi import FastAPI
from app.routers import auth  # this is the correct router path now

app = FastAPI(title="TheButtonApp API", version="0.1.0")

# Include the auth router
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "API is alive"}
