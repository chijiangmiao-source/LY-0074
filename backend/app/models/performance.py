from datetime import datetime
from enum import Enum
from beanie import Document, Indexed, Link
from pydantic import Field
from typing import Optional
from app.models.user import User, EmployeePosition
from app.models.store import Store
from app.models.bucket import Bucket
from app.models.flower import Flower
from app.models.warning import Warning


class TaskType(str, Enum):
    IN_BUCKET = "in_bucket"
    OUT_BUCKET = "out_bucket"
    PRESERVATION = "preservation"
    LOSS = "loss"
    WARNING_HANDLE = "warning_handle"
    INSPECTION = "inspection"


class ResponsibilityTargetType(str, Enum):
    BUCKET = "bucket"
    FLOWER = "flower"
    WARNING = "warning"
    STORE = "store"


class ResponsibilityAction(str, Enum):
    ASSIGN = "assign"
    IN_BUCKET = "in_bucket"
    OUT_BUCKET = "out_bucket"
    PRESERVATION = "preservation"
    LOSS = "loss"
    WARNING_HANDLE = "warning_handle"
    INSPECTION = "inspection"
    TRANSFER = "transfer"
    COMPLETE = "complete"


class ResponsibilityTrace(Document):
    target_type: ResponsibilityTargetType
    target_id: str
    batch_no: Optional[str] = None
    store: Optional[Link[Store]] = None
    bucket: Optional[Link[Bucket]] = None
    flower: Optional[Link[Flower]] = None
    warning: Optional[Link[Warning]] = None
    action: ResponsibilityAction
    action_label: str
    operator: Optional[Link[User]] = None
    operator_name: Optional[str] = None
    operator_position: Optional[EmployeePosition] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "responsibility_traces"
        indexes = [
            [("target_type", 1), ("target_id", 1)],
            [("operator", 1)],
            [("created_at", -1)],
        ]


class EmployeePerformanceSnapshot(Document):
    user: Link[User]
    user_name: str
    position: EmployeePosition
    position_label: str
    store: Optional[Link[Store]] = None
    store_name: Optional[str] = None
    period_start: datetime
    period_end: datetime
    total_operations: int = 0
    in_bucket_count: int = 0
    out_bucket_count: int = 0
    preservation_count: int = 0
    loss_count: int = 0
    warning_handled_count: int = 0
    inspection_count: int = 0
    on_time_count: int = 0
    overdue_count: int = 0
    on_time_rate: float = 0.0
    total_loss_quantity: int = 0
    responsible_loss_quantity: int = 0
    avg_warning_handle_hours: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "employee_performance_snapshots"
        indexes = [
            [("user", 1), ("period_start", 1), ("period_end", 1)],
            [("position", 1)],
        ]
