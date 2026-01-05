from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.jwt_helpers import pwd_context, create_jwt_token, verify_password
from app.schemas import UserLogin, UserResponse
from app.database import get_user_by_email  # replace with your actual DB function

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# Example login route
@router.post("/login", response_model=UserResponse)
def login(user: UserLogin):
    # Step 1: Fetch user from database
    db_user = get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Step 2: Verify password
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Step 3: Create JWT token
    token = create_jwt_token({"sub": db_user.email})
    
    return {"access_token": token, "token_type": "bearer"}
