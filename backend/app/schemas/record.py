from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BucketInfo(BaseModel):
    id: str
    bucket_code: str


class FlowerInfo(BaseModel):
    id: str
    flower_name: str
    flower_code: str


class StoreInfo(BaseModel):
    id: str
    store_name: str


class BucketInCreate(BaseModel):
    bucket_id: str
    flower_id: str
    quantity: int
    operator: Optional[str] = None
    remark: Optional[str] = None


class BucketInResponse(BaseModel):
    id: str = Field(alias="_id")
    bucket: BucketInfo
    flower: FlowerInfo
    quantity: int
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class BucketOutCreate(BaseModel):
    bucket_id: str
    flower_id: str
    quantity: int
    operator: Optional[str] = None
    remark: Optional[str] = None


class BucketOutResponse(BaseModel):
    id: str = Field(alias="_id")
    bucket: BucketInfo
    flower: FlowerInfo
    quantity: int
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class PreservationCreate(BaseModel):
    bucket_id: str
    supplement_quantity: float
    operator: Optional[str] = None
    remark: Optional[str] = None


class PreservationResponse(BaseModel):
    id: str = Field(alias="_id")
    bucket: BucketInfo
    store: Optional[StoreInfo] = None
    supplement_quantity: float
    previous_quantity: float
    after_quantity: float
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class LossCreate(BaseModel):
    flower_id: str
    quantity: int
    reason: Optional[str] = None
    operator: Optional[str] = None
    remark: Optional[str] = None


class LossResponse(BaseModel):
    id: str = Field(alias="_id")
    flower: FlowerInfo
    store: Optional[StoreInfo] = None
    quantity: int
    reason: Optional[str] = None
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True
