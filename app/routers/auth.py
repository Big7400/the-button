
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

def _ensure_roles(db: Session):
    for name in ["user", "admin"]:
        if not db.query(models.Role).filter_by(name=name).first():
            db.add(models.Role(name=name))
    db.commit()

def _maybe_bootstrap_admin(db: Session, email: str) -> bool:
    # If BOOTSTRAP_ADMIN_EMAIL is set, only that email can be bootstrapped.
    if settings.BOOTSTRAP_ADMIN_EMAIL:
        if email != settings.BOOTSTRAP_ADMIN_EMAIL:
            return False

    if not settings.AUTO_PROMOTE_FIRST_ADMIN and not settings.BOOTSTRAP_ADMIN_EMAIL:
        return False

    # If there are no admins yet, promote this user.
    admin_role = db.query(models.Role).filter_by(name="admin").first()
    has_admin = (
        db.query(models.User)
          .join(models.Role, models.User.role_id == models.Role.id)
          .filter(models.Role.name == "admin")
          .first()
        is not None
    )
    return (admin_role is not None) and (not has_admin)

@router.post("/register", response_model=schemas.UserResponse)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    _ensure_roles(db)

    user_role = db.query(models.Role).filter(models.Role.name == "user").first()
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()

    role_id = user_role.id

    # Bootstrap rule: if no admin exists, first user (or configured email) becomes admin
    if _maybe_bootstrap_admin(db, payload.email):
        role_id = admin_role.id

    user = models.User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role_id=role_id,
        is_active=True,
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
