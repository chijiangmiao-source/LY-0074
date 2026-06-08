from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.bucket import BucketStatus


class BucketBase(BaseModel):
    bucket_code: str
    store_id: str
    capacity: float
    current_quantity: float = 0.0
    status: BucketStatus = BucketStatus.ACTIVE
    responsible_person: Optional[str] = None
    remark: Optional[str] = None


class BucketCreate(BucketBase):
    pass


class BucketUpdate(BaseModel):
    store_id: Optional[str] = None
    capacity: Optional[float] = None
    current_quantity: Optional[float] = None
    status: Optional[BucketStatus] = None
    responsible_person: Optional[str] = None
    remark: Optional[str] = None


class BucketStoreInfo(BaseModel):
    id: str
    store_name: str
    store_code: str


class BucketResponse(BaseModel):
    id: str = Field(alias="_id")
    bucket_code: str
    store: BucketStoreInfo
    capacity: float
    current_quantity: float
    status: BucketStatus
    responsible_person: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
