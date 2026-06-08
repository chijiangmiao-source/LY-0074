from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CompetencyDimensionInfo(BaseModel):
    code: str
    label: str


class TrainingCourseSimple(BaseModel):
    id: str = Field(alias="_id")
    course_code: str
    course_name: str
    competency_dimension: str
    competency_dimension_label: str
    duration_minutes: int = 60

    class Config:
        populate_by_name = True


class TrainingCourseDetail(TrainingCourseSimple):
    description: Optional[str] = None
    target_positions: List[str] = []
    content: Optional[str] = None
    passing_score: float = 80.0
    status: str
    created_at: datetime
    updated_at: datetime


class CompetencyScoreItemResponse(BaseModel):
    dimension: str
    dimension_label: str
    score: float
    max_score: float = 100.0
    level: str
    operations_count: int = 0
    error_count: int = 0
    details: Dict[str, Any] = {}


class EmployeeCompetencyAssessmentResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    user_name: str
    position: Optional[str] = None
    position_label: Optional[str] = None
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    period_start: str
    period_end: str
    overall_score: float = 0.0
    overall_level: str = "normal"
    competency_scores: List[CompetencyScoreItemResponse] = []
    weak_dimensions: List[str] = []
    strong_dimensions: List[str] = []
    training_suggestions: List[str] = []
    created_at: str

    class Config:
        populate_by_name = True


class TrainingTaskResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    user_name: str
    position: Optional[str] = None
    position_label: Optional[str] = None
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    course_id: Optional[str] = None
    course_name: str
    competency_dimension: str
    competency_dimension_label: str
    task_type: str
    task_type_label: str
    status: str
    status_label: str
    assigned_at: str
    deadline: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    score: Optional[float] = None
    passed: Optional[bool] = None
    attempts: int = 0
    remark: Optional[str] = None
    related_error_ids: List[str] = []
    related_trace_ids: List[str] = []

    class Config:
        populate_by_name = True


class CreateTrainingTaskRequest(BaseModel):
    user_id: str
    course_id: Optional[str] = None
    course_name: str
    competency_dimension: str
    task_type: str = "refresher"
    deadline: Optional[str] = None
    remark: Optional[str] = None
    related_error_ids: List[str] = []
    related_trace_ids: List[str] = []


class UpdateTrainingTaskRequest(BaseModel):
    status: Optional[str] = None
    score: Optional[float] = None
    passed: Optional[bool] = None
    remark: Optional[str] = None


class HighFrequencyErrorResponse(BaseModel):
    id: str = Field(alias="_id")
    error_type: str
    error_type_label: str
    competency_dimension: str
    competency_dimension_label: str
    description: str
    occurrence_count: int = 0
    affected_employee_count: int = 0
    affected_store_count: int = 0
    period_start: str
    period_end: str
    related_trace_ids: List[str] = []
    sample_traces: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str

    class Config:
        populate_by_name = True


class TrainingStatsResponse(BaseModel):
    period_start: str
    period_end: str
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    total_employees: int = 0
    total_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    training_completion_rate: float = 0.0
    refresher_tasks: int = 0
    refresher_passed: int = 0
    refresher_pass_rate: float = 0.0
    exam_tasks: int = 0
    exam_passed: int = 0
    exam_pass_rate: float = 0.0
    problem_recurrence_rate: float = 0.0
    avg_overall_score: float = 0.0
    dimension_scores: List[Dict[str, Any]] = []
    trend_data: List[Dict[str, Any]] = []


class EmployeeTrainingListResponse(BaseModel):
    items: List[TrainingTaskResponse]
    total: int


class ErrorTraceLinkRequest(BaseModel):
    error_type: str
    error_type_label: str
    competency_dimension: str
    description: str
    trace_ids: List[str]
