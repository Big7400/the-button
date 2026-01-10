import os
import subprocess
import sys
import signal

SECURITY_CODE = """
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# ---------- Password Hashing ----------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ---------- JWT Helpers ----------
SECRET_KEY = "SUPERSECRETKEYCHANGEINPRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------- FastAPI Dependency ----------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": user_id}
"""

# Step 1 — Overwrite security.py
security_path = os.path.join("app", "core", "security.py")
os.makedirs(os.path.dirname(security_path), exist_ok=True)
with open(security_path, "w") as f:
    f.write(SECURITY_CODE)
print("[✓] security.py overwritten successfully.")

# Step 2 — Install dependencies
deps = ["fastapi", "uvicorn", "pyjwt", "sqlalchemy", "pydantic", "passlib[bcrypt]"]
subprocess.run([sys.executable, "-m", "pip", "install", *deps])

# Step 3 — Kill processes using ports 8003 and 8004
for port in [8003, 8004]:
    try:
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
        pids = result.stdout.split()
        for pid in pids:
            os.kill(int(pid), signal.SIGKILL)
            print(f"[✓] Killed process {pid} on port {port}")
    except Exception:
        pass

# Step 4 — Run uvicorn on port 8004
print("[✓] Starting server on http://127.0.0.1:8004")
subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app",
                "--host", "127.0.0.1", "--port", "8004", "--reload", "--log-level", "debug"])
