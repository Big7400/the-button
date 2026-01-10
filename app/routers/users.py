from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app import schemas, models

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserResponse)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user
