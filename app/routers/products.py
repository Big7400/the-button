from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas, database
from app.core.security import get_current_user, require_admin

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductBase, db: Session = Depends(get_db), admin=Depends(require_admin)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=list[schemas.ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()
