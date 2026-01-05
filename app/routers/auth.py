from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.jwt_helpers import verify_password, create_access_token

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def jwt_login(request: LoginRequest, db: Session = Depends(get_db)):
    # 1️⃣ Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # 2️⃣ Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # 3️⃣ Generate JWT token
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)

    # 4️⃣ Return response
    return {"status": "ok", "token": access_token}
