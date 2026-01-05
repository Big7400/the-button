# backend/app/api/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
import models

router = APIRouter(prefix="/users", tags=["users"])

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# List all users
@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

# Create a new user
@router.post("/")
def create_user(username: str, email: str, password_hash: str, db: Session = Depends(get_db)):
    user = models.User(username=username, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
