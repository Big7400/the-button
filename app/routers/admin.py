from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Role
from ..schemas import UserRead

from ..core.security import get_current_active_admin

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_active_admin)]
)

@router.get("/users", response_model=list[UserRead])
def list_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
