from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

def _maybe_bootstrap_admin(db: Session, email: str) -> bool:
    """Returns True if this should be admin (first user)"""
    existing_admin = db.query(models.User).filter(models.User.is_admin == True).first()
    return existing_admin is None

@router.post("/register")
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    # Get or create default role
    user_role = db.query(models.Role).filter(models.Role.name == "user").first()
    if not user_role:
        user_role = models.Role(name="user", description="Standard user")
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
    
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    if not admin_role:
        admin_role = models.Role(name="admin", description="Administrator")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
    
    role_id = user_role.id
    is_admin = False
    
    # Bootstrap admin
    if _maybe_bootstrap_admin(db, payload.email):
        role_id = admin_role.id
        is_admin = True
    
    user = models.User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role_id=role_id,
        is_active=True,
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "role": user.role.name,
    }

@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}