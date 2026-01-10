from pathlib import Path
import textwrap
import os

ROOT = Path(__file__).resolve().parent

def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    print(f"✅ wrote {rel_path}")

def main():
    # --- Remove broken DB ---
    db = ROOT / "app.db"
    if db.exists():
        db.unlink()
        print("🧹 removed app.db")

    # --- database.py ---
    write("app/database.py", """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, declarative_base
        from typing import Generator

        DATABASE_URL = "sqlite:///./app.db"

        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
        )

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()

        def get_db() -> Generator:
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
    """)

    # --- models.py ---
    write("app/models.py", """
        from sqlalchemy import Column, Integer, String, Boolean, DateTime
        from sqlalchemy.sql import func
        from app.database import Base

        class User(Base):
            __tablename__ = "users"

            id = Column(Integer, primary_key=True, index=True)
            email = Column(String, unique=True, index=True, nullable=False)
            hashed_password = Column(String, nullable=False)

            is_active = Column(Boolean, default=True)
            is_admin = Column(Boolean, default=False)

            created_at = Column(DateTime(timezone=True), server_default=func.now())
            updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    """)

    # --- schemas.py ---
    write("app/schemas.py", """
        from pydantic import BaseModel, EmailStr, Field

        class UserCreate(BaseModel):
            email: EmailStr
            password: str = Field(min_length=8)

        class UserResponse(BaseModel):
            id: int
            email: EmailStr
            is_active: bool
            is_admin: bool

            class Config:
                from_attributes = True

        class Token(BaseModel):
            access_token: str
            token_type: str = "bearer"
    """)

    # --- config.py ---
    write("app/core/config.py", """
        from pydantic import BaseModel

        class Settings(BaseModel):
            SECRET_KEY: str = "CHANGE_ME_NOW"
            ALGORITHM: str = "HS256"
            ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

        settings = Settings()
    """)

    # --- security.py (ARGON2 ONLY) ---
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
            return user
    """)

    # --- auth.py ---
    write("app/routers/auth.py", """
        from fastapi import APIRouter, Depends, HTTPException, status
        from fastapi.security import OAuth2PasswordRequestForm
        from sqlalchemy.orm import Session

        from app.database import get_db
        from app import models, schemas
        from app.core.security import get_password_hash, verify_password, create_access_token

        router = APIRouter(prefix="/auth", tags=["auth"])

        @router.post("/register", response_model=schemas.UserResponse, status_code=201)
        def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
            if db.query(models.User).filter(models.User.email == payload.email).first():
                raise HTTPException(400, "Email already registered")

            user = models.User(
                email=payload.email,
                hashed_password=get_password_hash(payload.password),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        @router.post("/login", response_model=schemas.Token)
        def login(
            form: OAuth2PasswordRequestForm = Depends(),
            db: Session = Depends(get_db),
        ):
            user = db.query(models.User).filter(models.User.email == form.username).first()
            if not user or not verify_password(form.password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            token = create_access_token(str(user.id))
            return {"access_token": token}
    """)

    # --- users.py ---
    write("app/routers/users.py", """
        from fastapi import APIRouter, Depends
        from app.core.security import get_current_user
        from app import schemas

        router = APIRouter(prefix="/users", tags=["users"])

        @router.get("/me", response_model=schemas.UserResponse)
        def me(user = Depends(get_current_user)):
            return user
    """)

    # --- main.py ---
    write("app/main.py", """
        from fastapi import FastAPI
        from app.database import Base, engine
        from app import models
        from app.routers import auth, users

        app = FastAPI(title="TheButtonApp API")

        Base.metadata.create_all(bind=engine)

        app.include_router(auth.router)
        app.include_router(users.router)

        @app.get("/health")
        def health():
            return {"status": "ok"}
    """)

    write("app/routers/__init__.py", "")

    print("\\n🎉 FIX COMPLETE")
    print("NEXT:")
    print('pip install fastapi uvicorn sqlalchemy "pydantic[email]" "passlib[argon2]" argon2-cffi python-jose')
    print("python3 -m uvicorn app.main:app --port 8003 --reload")

if __name__ == "__main__":
    main()

