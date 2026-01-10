from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, Product
from app.schemas import OrderCreate, Order
from app.core.auth import get_current_user
