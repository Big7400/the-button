from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, database
from app.core.security import get_current_user
from app.utils.roles import require_role

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# List all users (admin only)
@router.get("/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    require_role(current_user, "admin")
    return db.query(models.User).all()

# Get current user info (protected)
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
