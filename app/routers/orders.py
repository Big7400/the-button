from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas, database
from app.core.security import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderBase, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_order = models.Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/", response_model=list[schemas.OrderResponse])
def list_orders(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(models.Order).all()
