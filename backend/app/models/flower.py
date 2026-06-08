from datetime import datetime
from enum import Enum
from beanie import Document, Indexed, Link
from pydantic import Field
from typing import Optional
from app.models.bucket import Bucket
from app.models.category import FlowerCategory
from app.models.store import Store


class PreservationStatus(str, Enum):
    FRESH = "fresh"
    NORMAL = "normal"
    WILTED = "wilted"


class Flower(Document):
    flower_code: Indexed(str, unique=True)
    flower_name: str
    category: Link[FlowerCategory]
    bucket: Optional[Link[Bucket]] = None
    store: Optional[Link[Store]] = None
    current_quantity: int = 0
    preservation_status: PreservationStatus = PreservationStatus.FRESH
    in_bucket_date: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "flowers"
