from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent

def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    print(f"✅ wrote {rel_path}")

def append_if_missing(rel_path: str, line: str):
    path = ROOT / rel_path
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in existing:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(existing + ("" if existing.endswith("\n") or existing == "" else "\n") + line + "\n", encoding="utf-8")
        print(f"✅ updated {rel_path}")

def main():
    # .gitignore hygiene
    write(".gitignore", """
        .venv/
        __pycache__/
        *.pyc
        *.db
        .DS_Store
        .env
    """)

    # requirements.txt (minimal, stable)
    write("requirements.txt", """
        fastapi
        uvicorn
        sqlalchemy
        pydantic[email]
        passlib[argon2]
        argon2-cffi
        python-jose
        python-multipart
    """)

    # app/core/config.py (env-driven)
    write("app/core/config.py", """
        import os
        from pydantic import BaseModel

        class Settings(BaseModel):
            SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_NOW")  # set in .env or shell
            ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
            ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

            # Bootstrap admin behavior
            # Option A: if no admins exist, auto-promote the first registered user (safe for local dev)
            AUTO_PROMOTE_FIRST_ADMIN: bool = os.getenv("AUTO_PROMOTE_FIRST_ADMIN", "true").lower() == "true"

            # Option B: only auto-promote if email matches this value
            BOOTSTRAP_ADMIN_EMAIL: str | None = os.getenv("BOOTSTRAP_ADMIN_EMAIL")

        settings = Settings()
    """)

    # app/core/security.py (same as now, but keep require_admin and current_user)
    write("app/core/security.py", """
        from datetime import datetime, timedelta, timezone
        from fastapi import Depends, HTTPException
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
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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

    # app/routers/admin.py (adds role & active toggles)
    write("app/routers/admin.py", """
        from fastapi import APIRouter, Depends, HTTPException
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
                {"id": u.id, "email": u.email, "is_active": u.is_active, "role": u.role.name}
                for u in users
            ]

        @router.patch("/users/{user_id}/role")
        def update_role(
            user_id: int,
            payload: schemas.RoleUpdate,
            db: Session = Depends(get_db),
            _: models.User = Depends(require_admin),
        ):
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise HTTPException(404, "User not found")

            role = db.query(models.Role).filter(models.Role.name == payload.role_name).first()
            if not role:
                raise HTTPException(400, "Role not found")

            user.role_id = role.id
            db.commit()
            return {"status": "role updated", "user_id": user.id, "role": role.name}

        @router.patch("/users/{user_id}/active")
        def set_active(
            user_id: int,
            payload: schemas.ActiveUpdate,
            db: Session = Depends(get_db),
            _: models.User = Depends(require_admin),
        ):
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise HTTPException(404, "User not found")

            user.is_active = payload.is_active
            db.commit()
            return {"status": "active updated", "user_id": user.id, "is_active": user.is_active}
    """)

    # app/schemas.py (add ActiveUpdate)
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

        class ActiveUpdate(BaseModel):
            is_active: bool
    """)

    # app/routers/auth.py (bootstrap admin logic)
    write("app/routers/auth.py", """
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
    """)

    # app/main.py (move seeding to startup event)
    write("app/main.py", """
        from fastapi import FastAPI
        from app.database import Base, engine, SessionLocal
        from app import models
        from app.routers import auth, users, admin

        app = FastAPI(title="TheButtonApp API")

        @app.on_event("startup")
        def startup():
            Base.metadata.create_all(bind=engine)
            # Ensure roles exist
            db = SessionLocal()
            for name in ["user", "admin"]:
                if not db.query(models.Role).filter_by(name=name).first():
                    db.add(models.Role(name=name))
            db.commit()
            db.close()

        app.include_router(auth.router)
        app.include_router(users.router)
        app.include_router(admin.router)

        @app.get("/health")
        def health():
            return {"status": "ok"}
    """)

    # Ensure routers init exists
    write("app/routers/__init__.py", "")

    print("\n✅ Phase 3.5 complete: bootstrap admin + startup seeding + env config + admin utilities")
    print("Next: restart uvicorn and test a fresh register to see auto-admin behavior.")

if __name__ == "__main__":
    main()

