from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StoreBase(BaseModel):
    store_code: str
    store_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    manager: Optional[str] = None
    is_active: bool = True


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    store_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager: Optional[str] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    id: str = Field(alias="_id")
    created_at: datetime

    class Config:
        populate_by_name = True
