from fastapi import FastAPI
from .database import engine
from . import models

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="The Button App API",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"status": "API is running"}
