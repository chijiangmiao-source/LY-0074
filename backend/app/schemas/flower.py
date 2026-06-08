from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.flower import PreservationStatus


class FlowerBase(BaseModel):
    flower_code: str
    flower_name: str
    category_id: str
    batch_no: Optional[str] = None
    bucket_id: Optional[str] = None
    store_id: Optional[str] = None
    current_quantity: int = 0
    preservation_status: PreservationStatus = PreservationStatus.FRESH
    in_bucket_date: Optional[datetime] = None
    remark: Optional[str] = None


class FlowerCreate(FlowerBase):
    pass


class FlowerUpdate(BaseModel):
    flower_name: Optional[str] = None
    category_id: Optional[str] = None
    batch_no: Optional[str] = None
    bucket_id: Optional[str] = None
    store_id: Optional[str] = None
    current_quantity: Optional[int] = None
    preservation_status: Optional[PreservationStatus] = None
    in_bucket_date: Optional[datetime] = None
    remark: Optional[str] = None


class CategoryInfo(BaseModel):
    id: str
    category_name: str
    category_code: str


class BucketInfo(BaseModel):
    id: str
    bucket_code: str


class StoreInfo(BaseModel):
    id: str
    store_name: str


class FlowerResponse(BaseModel):
    id: str = Field(alias="_id")
    flower_code: str
    flower_name: str
    category: CategoryInfo
    batch_no: Optional[str] = None
    bucket: Optional[BucketInfo] = None
    store: Optional[StoreInfo] = None
    current_quantity: int
    preservation_status: PreservationStatus
    in_bucket_date: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
