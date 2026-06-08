from datetime import datetime
from enum import Enum
from beanie import Document, Link
from pydantic import Field
from typing import Optional
from app.models.bucket import Bucket
from app.models.flower import Flower
from app.models.store import Store
from app.models.user import User


class StatusChangeTarget(str, Enum):
    BUCKET_STATUS = "bucket_status"
    FLOWER_PRESERVATION = "flower_preservation"
    FLOWER_BUCKET = "flower_bucket"


class StatusChangeRecord(Document):
    target_type: StatusChangeTarget
    target_id: str
    store: Optional[Link[Store]] = None
    bucket: Optional[Link[Bucket]] = None
    flower: Optional[Link[Flower]] = None
    old_status: Optional[str] = None
    new_status: str
    old_label: Optional[str] = None
    new_label: str
    operator: Optional[Link[User]] = None
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "status_change_records"
