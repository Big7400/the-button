from pydantic import BaseModel, EmailStr
from datetime import datetime

# Input schema for creating a user
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# Output schema for returning user info
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # for Pydantic V2 compatibility
