from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent

def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    print(f"✅ wrote {rel_path}")

def main():
    # ---- reset DB (schema change) ----
    db = ROOT / "app.db"
    if db.exists():
        db.unlink()
        print("🧹 removed app.db")

    # ---- models.py ----
    write("app/models.py", """
        from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
        from sqlalchemy.sql import func
        from sqlalchemy.orm import relationship
        from app.database import Base

        class Role(Base):
            __tablename__ = "roles"

            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True, nullable=False)

        class User(Base):
            __tablename__ = "users"

            id = Column(Integer, primary_key=True, index=True)
            email = Column(String, unique=True, index=True, nullable=False)
            hashed_password = Column(String, nullable=False)

            is_active = Column(Boolean, default=True)

            role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
            role = relationship("Role")

            created_at = Column(DateTime(timezone=True), server_default=func.now())
            updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    """)

    # ---- schemas.py ----
    write("app/schemas.py", """
        from pydantic import BaseModel, EmailStr, Field

        class UserCreate(BaseModel):
            email: EmailStr
            password: str = Field(min_length=8)

        class UserResponse(BaseModel):
            id: int
            email: EmailStr
            is_active: bool
            role: str

            class Config:
                from_attributes = True

        class Token(BaseModel):
            access_token: str
            token_type: str = "bearer"

        class RoleUpdate(BaseModel):
            role_name: str
    """)

    # ---- security.py ----
    write("app/core/security.py", """
        from datetime import datetime, timedelta, timezone
        from fastapi import Depends, HTTPException, status
        from fastapi.security import OAuth2PasswordBearer
        from jose import jwt, JWTError
        from passlib.context import CryptContext
        from sqlalchemy.orm import Session

        from app.database import get_db
        from app.core.config import settings
        from app import models

        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

        def get_password_hash(password: str) -> str:
            return pwd_context.hash(password)

        def verify_password(plain: str, hashed: str) -> bool:
            return pwd_context.verify(plain, hashed)

        def create_access_token(subject: str):
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            payload = {"sub": subject, "exp": expire}
            return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        def get_current_user(
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db),
        ):
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = payload.get("sub")
            except JWTError:
                raise HTTPException(status_code=401, detail="Invalid token")

            user = db.query(models.User).filter(models.User.id == int(user_id)).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            if not user.is_active:
                raise HTTPException(status_code=403, detail="User inactive")
            return user

        def require_admin(user: models.User = Depends(get_current_user)):
            if user.role.name != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            return user
    """)

    # ---- auth.py ----
    write("app/routers/auth.py", """
        from fastapi import APIRouter, Depends, HTTPException
        from fastapi.security import OAuth2PasswordRequestForm
        from sqlalchemy.orm import Session

        from app.database import get_db
        from app import models, schemas
        from app.core.security import get_password_hash, verify_password, create_access_token

        router = APIRouter(prefix="/auth", tags=["auth"])

        @router.post("/register", response_model=schemas.UserResponse)
        def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
            if db.query(models.User).filter(models.User.email == payload.email).first():
                raise HTTPException(400, "Email already registered")

            role = db.query(models.Role).filter(models.Role.name == "user").first()

            user = models.User(
                email=payload.email,
                hashed_password=get_password_hash(payload.password),
                role_id=role.id,
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
            return {"access_token": token}
    """)

    # ---- admin.py ----
    write("app/routers/admin.py", """
        from fastapi import APIRouter, Depends
        from sqlalchemy.orm import Session

        from app.database import get_db
        from app import models, schemas
        from app.core.security import require_admin

        router = APIRouter(prefix="/admin", tags=["admin"])

        @router.get("/users")
        def list_users(
            db: Session = Depends(get_db),
            _: models.User = Depends(require_admin),
        ):
            users = db.query(models.User).all()
            return [
                {
                    "id": u.id,
                    "email": u.email,
                    "is_active": u.is_active,
                    "role": u.role.name,
                }
                for u in users
            ]

        @router.patch("/users/{user_id}/role")
        def update_role(
            user_id: int,
            payload: schemas.RoleUpdate,
            db: Session = Depends(get_db),
            _: models.User = Depends(require_admin),
        ):
            user = db.query(models.User).get(user_id)
            role = db.query(models.Role).filter(models.Role.name == payload.role_name).first()

            user.role_id = role.id
            db.commit()

            return {"status": "role updated"}
    """)

    # ---- main.py ----
    write("app/main.py", """
        from fastapi import FastAPI
        from app.database import Base, engine, SessionLocal
        from app import models
        from app.routers import auth, users, admin

        app = FastAPI(title="TheButtonApp API")

        Base.metadata.create_all(bind=engine)

        def seed_roles():
            db = SessionLocal()
            for name in ["user", "admin"]:
                if not db.query(models.Role).filter_by(name=name).first():
                    db.add(models.Role(name=name))
            db.commit()
            db.close()

        seed_roles()

        app.include_router(auth.router)
        app.include_router(users.router)
        app.include_router(admin.router)

        @app.get("/health")
        def health():
            return {"status": "ok"}
    """)

    write("app/routers/__init__.py", "")

    print("\\n🎉 PHASE 3 SETUP COMPLETE")
    print("Next:")
    print("python3 -m uvicorn app.main:app --port 8003 --reload")

if __name__ == "__main__":
    main()

