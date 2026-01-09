import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"Created {path}")

# -----------------------------
# main.py
# -----------------------------
main_py = """from fastapi import FastAPI
from app.routers import auth, users
from app.database import Base, engine, get_db
from sqlalchemy.orm import Session
from app.models import User
from app.routers.auth import get_password_hash

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TheButtonApp API")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# Seed a dummy user automatically
# -----------------------------
def seed_dummy_user():
    db = Session(bind=engine)
    user = db.query(User).filter(User.email == "admin@example.com").first()
    if not user:
        hashed_password = get_password_hash("password")
        user = User(email="admin@example.com", hashed_password=hashed_password, is_superuser=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        print("✅ Dummy user created: admin@example.com / password")
    else:
        print("✅ Dummy user already exists: admin@example.com / password")
    db.close()

seed_dummy_user()
"""

write_file(os.path.join(PROJECT_ROOT, "app/main.py"), main_py)

# -----------------------------
# database.py
# -----------------------------
database_py = """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

write_file(os.path.join(PROJECT_ROOT, "app/database.py"), database_py)

# -----------------------------
# models.py
# -----------------------------
models_py = """from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
"""

write_file(os.path.join(PROJECT_ROOT, "app/models.py"), models_py)

# -----------------------------
# schemas.py
# -----------------------------
schemas_py = """from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
"""

write_file(os.path.join(PROJECT_ROOT, "app/schemas.py"), schemas_py)

# -----------------------------
# routers/__init__.py
# -----------------------------
write_file(os.path.join(PROJECT_ROOT, "app/routers/__init__.py"), "")

# -----------------------------
# routers/auth.py
# -----------------------------
auth_py = """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

from app import schemas, models
from app.database import get_db

SECRET_KEY = "SUPERSECRET123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
"""

write_file(os.path.join(PROJECT_ROOT, "app/routers/auth.py"), auth_py)

# -----------------------------
# routers/users.py
# -----------------------------
users_py = """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app import schemas, models
from app.database import get_db
import jwt

SECRET_KEY = "SUPERSECRET123"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise Exception()
    except:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/me", response_model=schemas.UserResponse)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user
"""

write_file(os.path.join(PROJECT_ROOT, "app/routers/users.py"), users_py)

print("\n✅ Project structure, Phase 2 auth/db setup, and dummy user seeding completed!")
print("Run: uvicorn app.main:app --reload --port 8001")
