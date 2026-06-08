from datetime import datetime
from enum import Enum
from beanie import Document, Link
from pydantic import Field
from typing import Optional
from app.models.bucket import Bucket
from app.models.flower import Flower
from app.models.store import Store
from app.models.user import User


class WarningType(str, Enum):
    LOW_LIQUID = "low_liquid"
    WILTED = "wilted"
    LONG_IN_BUCKET = "long_in_bucket"
    HIGH_LOSS = "high_loss"


class WarningSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WarningStatus(str, Enum):
    PENDING = "pending"
    HANDLING = "handling"
    RESOLVED = "resolved"


class Warning(Document):
    warning_type: WarningType
    warning_type_label: str
    severity: WarningSeverity
    store: Optional[Link[Store]] = None
    bucket: Optional[Link[Bucket]] = None
    flower: Optional[Link[Flower]] = None
    message: str
    current_value: Optional[str] = None
    threshold_value: Optional[str] = None
    unit: str = ""
    status: WarningStatus = WarningStatus.PENDING
    handler: Optional[Link[User]] = None
    handled_at: Optional[datetime] = None
    handle_note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "warnings"
