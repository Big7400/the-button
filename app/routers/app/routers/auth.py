from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from app.schemas import UserLogin
from app.models import User
from app.database import SessionLocal
from app.jwt_helpers import pwd_context, create_jwt_token

router = APIRouter()

@router.post("/login")
def login(user: UserLogin):
    db = SessionLocal()
    db_user = db.query(User).filter(User.email == user.email).first()
    db.close()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_jwt_token(db_user)
    return {"status": "ok", "token": token}
