
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app import schemas

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.UserResponse)
def me(user = Depends(get_current_user)):
    return user
