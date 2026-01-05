from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from app import models

router = APIRouter(
    prefix="/scans",
    tags=["scans"]
)

@router.get("/")
def get_scans(db: Session = Depends(get_db)):
    return db.query(models.ScanResults).all()

@router.post("/")
def create_scan(
    user_id: int,
    market_id: int,
    timeframe: str,
    db: Session = Depends(get_db)
):
    scan = models.ScanResults(
        user_id=user_id,
        market_id=market_id,
        timeframe=timeframe
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan
