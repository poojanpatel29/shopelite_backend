from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole

class UserOut(BaseModel):
    id:          int
    name:        str
    email:       EmailStr
    phone:       str | None
    role:        UserRole
    avatar:      str | None
    is_active:   bool
    is_verified: bool
    created_at:  datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name:   str | None = None
    phone:  str | None = None
    avatar: str | None = None