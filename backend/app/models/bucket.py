from datetime import datetime
from enum import Enum
from beanie import Document, Indexed, Link
from pydantic import Field
from typing import Optional
from app.models.store import Store


class BucketStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class Bucket(Document):
    bucket_code: Indexed(str, unique=True)
    store: Link[Store]
    capacity: float
    current_quantity: float = 0.0
    status: BucketStatus = BucketStatus.ACTIVE
    responsible_person: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "buckets"
