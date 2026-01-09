# fix_app_phase3.py
import os

# -----------------------------
# Folder structure
# -----------------------------
folders = [
    "app",
    "app/routers",
    "app/core",
    "app/utils"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"Created folder: {folder}")

# -----------------------------
# File templates
# -----------------------------
files = {
    "app/main.py": '''from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth, users

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TheButtonApp - Phase 3")

# Routers
app.include_router(auth.router)
app.include_router(users.router)

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}
''',

    "app/database.py": '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',

    "app/models.py": '''from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")
''',

    "app/schemas.py": '''from pydantic import BaseModel, EmailStr
from typing import Optional

# Role schemas
class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int
    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role_id: Optional[int]

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: Optional[RoleResponse]
    class Config:
        from_attributes = True
''',

    "app/core/security.py": '''from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app import models, database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"

# Dummy password hashing
def fake_hash_password(password: str):
    return "hashed_" + password

# Dependency to get current user from token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    # For demo purposes, decode token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid auth")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid auth")
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
''',

    "app/utils/roles.py": '''from fastapi import HTTPException, status

def require_role(user, role_name: str):
    if user.role is None or user.role.name != role_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User must have role: {role_name}"
        )
    return True
''',

    "app/routers/auth.py": '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database
from app.core.security import fake_hash_password, SECRET_KEY, ALGORITHM
from jose import jwt

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = fake_hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password, role_id=user.role_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or db_user.hashed_password != fake_hash_password(user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token_data = {"sub": db_user.username}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
''',

    "app/routers/users.py": '''from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, database
from app.core.security import get_current_user
from app.utils.roles import require_role

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    require_role(current_user, "admin")
    return db.query(models.User).all()

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
'''
}

# -----------------------------
# Write all files
# -----------------------------
for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)
    print(f"Created file: {path}")

print("\n✅ Phase 3 runner complete! You can now run:\n\nuvicorn app.main:app --reload\n")
