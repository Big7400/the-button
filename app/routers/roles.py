from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role
from app.schemas import Role, RoleCreate
from app.core.auth import require_admin
