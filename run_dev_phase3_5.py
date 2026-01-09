#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
from pathlib import Path

import uvicorn

# ===========================
# CONFIG
# ===========================
PORT = 8001
HOST = "0.0.0.0"
APP_MODULE = "app.main:app"

# ===========================
# HELPERS
# ===========================
def kill_port(port):
    """Kill any process listening on the specified port."""
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil

    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            pid = conn.pid
            if pid:
                print(f"Killing process {pid} on port {port}")
                os.kill(pid, signal.SIGKILL)


def ensure_directories():
    """Make sure app structure exists for Phase 3.5"""
    base = Path("app")
    (base / "routers").mkdir(parents=True, exist_ok=True)
    (base / "core").mkdir(parents=True, exist_ok=True)
    # Create __init__.py files if missing
    for folder in [base, base / "routers", base / "core"]:
        init_file = folder / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Auto-generated\n")


def create_protected_routes():
    """Create example routers for Phase 3.5 if missing."""
    import json

    # app/core/security.py
    sec_file = Path("app/core/security.py")
    if not sec_file.exists():
        sec_file.write_text(
            '''from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from app import database, models

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    from app.database import SessionLocal
    from sqlalchemy.orm import Session
    db: Session = SessionLocal()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def require_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
'''
        )

    # app/routers/users.py
    user_file = Path("app/routers/users.py")
    if not user_file.exists():
        user_file.write_text(
            '''from fastapi import APIRouter, Depends
from app.core.security import get_current_user, require_admin
from app import models, database
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

@router.get("/admin/all")
def read_all_users(db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    users = db.query(models.User).all()
    return [{"username": u.username, "role": u.role} for u in users]
'''
        )

# ===========================
# MAIN SCRIPT
# ===========================
def main():
    print(f"=== Running Phase 3.5 Dev Runner ===\nKilling port {PORT} if needed...")
    kill_port(PORT)

    print("Ensuring folder structure...")
    ensure_directories()

    print("Creating protected routes if missing...")
    create_protected_routes()

    print("Starting Uvicorn server...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", APP_MODULE, "--reload", "--host", HOST, "--port", str(PORT)]
    )


if __name__ == "__main__":
    main()
