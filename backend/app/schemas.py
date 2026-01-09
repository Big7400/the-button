from pydantic import BaseModel, EmailStr
from datetime import datetime

# Signup
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# Response after signup/login
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True
