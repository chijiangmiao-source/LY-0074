from datetime import datetime
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field, EmailStr
from typing import Optional


class EmployeePosition(str, Enum):
    MANAGER = "manager"
    FLORIST = "florist"
    WAREHOUSE = "warehouse"
    DELIVERY = "delivery"
    OTHER = "other"


POSITION_LABELS = {
    EmployeePosition.MANAGER: "店长",
    EmployeePosition.FLORIST: "花艺师",
    EmployeePosition.WAREHOUSE: "仓管员",
    EmployeePosition.DELIVERY: "配送员",
    EmployeePosition.OTHER: "其他",
}


class User(Document):
    username: Indexed(str, unique=True)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    position: EmployeePosition = EmployeePosition.OTHER
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
                "position": "manager",
                "is_active": True,
                "is_admin": True,
            }
        }
