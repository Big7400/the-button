from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from app import models

router = APIRouter(
    prefix="/markets",
    tags=["markets"]
)

@router.get("/")
def get_markets(db: Session = Depends(get_db)):
    return db.query(models.Market).all()

@router.post("/")
def create_market(
    symbol: str,
    name: str,
    db: Session = Depends(get_db)
):
    market = models.Market(symbol=symbol, name=name)
    db.add(market)
    db.commit()
    db.refresh(market)
    return market
