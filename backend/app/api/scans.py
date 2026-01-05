from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
import models

router = APIRouter(prefix="/scans", tags=["scans"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_scans(db: Session = Depends(get_db)):
    return db.query(models.ScanResult).all()

@router.post("/")
def create_scan(user_id: int, market_id: int, timeframe: str, status: str = "PENDING", db: Session = Depends(get_db)):
    scan = models.ScanResult(user_id=user_id, market_id=market_id, timeframe=timeframe, status=status)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan
