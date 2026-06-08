from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field, EmailStr
from typing import Optional


class User(Document):
    username: Indexed(str, unique=True)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@flowershop.com",
                "full_name": "系统管理员",
                "is_active": True,
                "is_admin": True,
            }
        }
