from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PositionInfo(BaseModel):
    code: str
    label: str


class StoreSimpleInfo(BaseModel):
    id: str
    store_name: str
    store_code: Optional[str] = None


class UserSimpleInfo(BaseModel):
    id: str
    username: str
    full_name: Optional[str] = None
    position: Optional[str] = None
    position_label: Optional[str] = None


class WorkloadStats(BaseModel):
    in_bucket_count: int = 0
    out_bucket_count: int = 0
    preservation_count: int = 0
    loss_count: int = 0
    warning_handled_count: int = 0
    inspection_count: int = 0
    total_operations: int = 0


class TimelinessStats(BaseModel):
    on_time_count: int = 0
    overdue_count: int = 0
    on_time_rate: float = 0.0
    avg_warning_handle_hours: float = 0.0


class LossStats(BaseModel):
    total_loss_quantity: int = 0
    responsible_loss_quantity: int = 0
    loss_rate: float = 0.0


class EmployeePerformance(BaseModel):
    user: UserSimpleInfo
    store: Optional[StoreSimpleInfo] = None
    workload: WorkloadStats
    timeliness: TimelinessStats
    loss: LossStats
    score: float = 0.0
    rank: Optional[int] = None


class PerformanceRankingResponse(BaseModel):
    items: List[EmployeePerformance]
    total: int
    period_start: str
    period_end: str


class ResponsibilityTraceItem(BaseModel):
    id: str = Field(alias="_id")
    target_type: str
    target_type_label: str
    target_id: str
    action: str
    action_label: str
    operator: Optional[UserSimpleInfo] = None
    operator_name: Optional[str] = None
    operator_position: Optional[str] = None
    operator_position_label: Optional[str] = None
    store: Optional[StoreSimpleInfo] = None
    bucket: Optional[dict] = None
    flower: Optional[dict] = None
    warning: Optional[dict] = None
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class ResponsibilityTraceResponse(BaseModel):
    target_type: str
    target_type_label: str
    target_id: str
    target_info: dict
    traces: List[ResponsibilityTraceItem]
    total: int


class PerformanceSummary(BaseModel):
    period_start: str
    period_end: str
    total_employees: int
    total_operations: int
    avg_on_time_rate: float
    total_loss_quantity: int
