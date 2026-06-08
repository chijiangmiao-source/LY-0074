from datetime import datetime
from enum import Enum
from beanie import Document, Indexed, Link
from pydantic import Field, BaseModel
from typing import Optional, List
from app.models.user import User, EmployeePosition
from app.models.store import Store


class CompetencyDimension(str, Enum):
    IN_BUCKET = "in_bucket"
    OUT_BUCKET = "out_bucket"
    PRESERVATION = "preservation"
    LOSS_HANDLING = "loss_handling"
    WARNING_HANDLING = "warning_handling"
    INSPECTION = "inspection"


COMPETENCY_LABELS = {
    CompetencyDimension.IN_BUCKET: "入桶操作",
    CompetencyDimension.OUT_BUCKET: "回桶操作",
    CompetencyDimension.PRESERVATION: "补液操作",
    CompetencyDimension.LOSS_HANDLING: "损耗处理",
    CompetencyDimension.WARNING_HANDLING: "预警处置",
    CompetencyDimension.INSPECTION: "巡检工作",
}


class TrainingCourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TrainingTaskType(str, Enum):
    INITIAL = "initial"
    REFRESHER = "refresher"
    EXAM = "exam"


TRAINING_TASK_TYPE_LABELS = {
    TrainingTaskType.INITIAL: "初次培训",
    TrainingTaskType.REFRESHER: "复训任务",
    TrainingTaskType.EXAM: "考核任务",
}


class TrainingTaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


TRAINING_TASK_STATUS_LABELS = {
    TrainingTaskStatus.PENDING: "待开始",
    TrainingTaskStatus.IN_PROGRESS: "进行中",
    TrainingTaskStatus.COMPLETED: "已完成",
    TrainingTaskStatus.FAILED: "未通过",
    TrainingTaskStatus.EXPIRED: "已过期",
}


class TrainingCourse(Document):
    course_code: str
    course_name: str
    description: Optional[str] = None
    competency_dimension: CompetencyDimension
    target_positions: List[EmployeePosition] = []
    content: Optional[str] = None
    duration_minutes: int = 60
    passing_score: float = 80.0
    status: TrainingCourseStatus = TrainingCourseStatus.DRAFT
    created_by: Optional[Link[User]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "training_courses"
        indexes = [
            [("course_code", 1)],
            [("competency_dimension", 1)],
            [("status", 1)],
        ]


class EmployeeTrainingTask(Document):
    user: Link[User]
    user_name: str
    position: Optional[EmployeePosition] = None
    store: Optional[Link[Store]] = None
    store_name: Optional[str] = None
    course: Optional[Link[TrainingCourse]] = None
    course_name: str
    competency_dimension: CompetencyDimension
    task_type: TrainingTaskType
    status: TrainingTaskStatus = TrainingTaskStatus.PENDING
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    passed: Optional[bool] = None
    attempts: int = 0
    remark: Optional[str] = None
    related_error_ids: List[str] = []
    related_trace_ids: List[str] = []

    class Settings:
        name = "employee_training_tasks"
        indexes = [
            [("user", 1)],
            [("status", 1)],
            [("competency_dimension", 1)],
            [("task_type", 1)],
            [("assigned_at", -1)],
            [("store", 1)],
        ]


class CompetencyScoreItem(BaseModel):
    dimension: CompetencyDimension
    dimension_label: str
    score: float
    max_score: float = 100.0
    level: str
    operations_count: int = 0
    error_count: int = 0
    details: dict = {}


class EmployeeCompetencyAssessment(Document):
    user: Link[User]
    user_name: str
    position: Optional[EmployeePosition] = None
    position_label: Optional[str] = None
    store: Optional[Link[Store]] = None
    store_name: Optional[str] = None
    period_start: datetime
    period_end: datetime
    overall_score: float = 0.0
    overall_level: str = "normal"
    competency_scores: List[CompetencyScoreItem] = []
    weak_dimensions: List[CompetencyDimension] = []
    strong_dimensions: List[CompetencyDimension] = []
    training_suggestions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "employee_competency_assessments"
        indexes = [
            [("user", 1), ("period_start", 1), ("period_end", 1)],
            [("store", 1)],
            [("position", 1)],
        ]


class HighFrequencyError(Document):
    error_type: str
    error_type_label: str
    competency_dimension: CompetencyDimension
    description: str
    occurrence_count: int = 0
    affected_employees: List[str] = []
    affected_stores: List[str] = []
    related_trace_ids: List[str] = []
    sample_traces: List[dict] = []
    period_start: datetime
    period_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "high_frequency_errors"
        indexes = [
            [("error_type", 1), ("period_start", 1), ("period_end", 1)],
            [("competency_dimension", 1)],
            [("occurrence_count", -1)],
        ]
