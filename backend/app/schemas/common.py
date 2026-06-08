from datetime import datetime
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field, EmailStr

T = TypeVar("T")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    position: Optional[str] = "other"
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    position_label: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
