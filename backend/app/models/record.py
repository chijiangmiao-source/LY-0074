from datetime import datetime
from enum import Enum
from beanie import Document, Link
from pydantic import Field
from typing import Optional
from app.models.bucket import Bucket
from app.models.flower import Flower
from app.models.store import Store


class RecordType(str, Enum):
    IN_BUCKET = "in_bucket"
    OUT_BUCKET = "out_bucket"
    PRESERVATION = "preservation"
    LOSS = "loss"


class BucketInRecord(Document):
    record_type: RecordType = RecordType.IN_BUCKET
    bucket: Link[Bucket]
    flower: Link[Flower]
    quantity: int
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "bucket_in_records"


class BucketOutRecord(Document):
    record_type: RecordType = RecordType.OUT_BUCKET
    bucket: Link[Bucket]
    flower: Link[Flower]
    quantity: int
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "bucket_out_records"


class PreservationRecord(Document):
    record_type: RecordType = RecordType.PRESERVATION
    bucket: Link[Bucket]
    store: Optional[Link[Store]] = None
    supplement_quantity: float
    previous_quantity: float
    after_quantity: float
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "preservation_records"


class LossRecord(Document):
    record_type: RecordType = RecordType.LOSS
    flower: Link[Flower]
    store: Optional[Link[Store]] = None
    quantity: int
    reason: Optional[str] = None
    operator: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "loss_records"
