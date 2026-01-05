# backend/app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut, Token
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter()

# --------------------
# Health check route
# --------------------
@router.get("/health")
def health_check():
    return {"status": "ok", "message": "API is alive"}

# --------------------
# Register a new user
# --------------------
@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --------------------
# Login user
