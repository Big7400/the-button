from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
import models

router = APIRouter(prefix="/markets", tags=["markets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_markets(db: Session = Depends(get_db)):
    return db.query(models.Market).all()

@router.post("/")
def create_market(name: str, symbol: str, db: Session = Depends(get_db)):
    market = models.Market(name=name, symbol=symbol)
    db.add(market)
    db.commit()
    db.refresh(market)
    return market
