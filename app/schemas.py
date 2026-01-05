# app/schemas.py
from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True  # for Pydantic v2

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True
