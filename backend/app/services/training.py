from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId

from app.models import (
    User,
    EmployeePosition,
    POSITION_LABELS,
    Store,
    ResponsibilityTrace,
    ResponsibilityAction,
    StatusChangeTarget,
)
from app.models.training import (
    CompetencyDimension,
    COMPETENCY_LABELS,
    TrainingCourse,
    EmployeeTrainingTask,
    TrainingTaskType,
    TRAINING_TASK_TYPE_LABELS,
    TrainingTaskStatus,
    TRAINING_TASK_STATUS_LABELS,
    EmployeeCompetencyAssessment,
    CompetencyScoreItem,
    HighFrequencyError,
)
from app.services.stats_service import (
    build_date_query,
    resolve_date_range,
    get_user_store,
    get_operator_name,
    BatchRecordLoader,
    WARNING_HANDLE_OVERDUE_HOURS,
)


COMPETENCY_LEVEL_THRESHOLDS = {
    "excellent": 90,
    "good": 75,
    "normal": 60,
    "weak": 40,
    "poor": 0,
}


def get_competency_level(score: float) -> str:
    if score >= COMPETENCY_LEVEL_THRESHOLDS["excellent"]:
        return "excellent"
    elif score >= COMPETENCY_LEVEL_THRESHOLDS["good"]:
        return "good"
    elif score >= COMPETENCY_LEVEL_THRESHOLDS["normal"]:
        return "normal"
    elif score >= COMPETENCY_LEVEL_THRESHOLDS["weak"]:
        return "weak"
    else:
        return "poor"


COMPETENCY_LEVEL_LABELS = {
    "excellent": "优秀",
    "good": "良好",
    "normal": "合格",
    "weak": "薄弱",
    "poor": "很差",
}


async def analyze_inspection_competency(
    user_id: str,
    loader: BatchRecordLoader,
) -> Dict[str, Any]:
    status_records = loader.get_status_records_for_user(user_id)
    inspection_count = len(status_records)

    warnings = loader.get_warnings_for_user(user_id)
    overdue_count = 0
    for w in warnings:
        if w.handled_at and w.created_at:
            hours = (w.handled_at - w.created_at).total_seconds() / 3600
            if hours > WARNING_HANDLE_OVERDUE_HOURS:
                overdue_count += 1

    error_count = overdue_count
    if inspection_count == 0:
        score = 50.0
    else:
        error_rate = error_count / max(inspection_count, 1)
        score = max(0.0, min(100.0, 100.0 - error_rate * 100))

    return {
        "score": round(score, 2),
        "operations_count": inspection_count,
        "error_count": error_count,
        "details": {
            "inspection_count": inspection_count,
            "overdue_warning_count": overdue_count,
        },
    }


async def analyze_loss_competency(
    user_id: str,
    loader: BatchRecordLoader,
) -> Dict[str, Any]:
    operator_name = await get_operator_name(user_id)
    loss_records = loader.get_loss_records_for_user(user_id, operator_name)

    operations_count = len(loss_records)
    total_qty = sum(r.quantity for r in loss_records)

    high_loss_count = 0
    unreasonable_reasons = 0
    for r in loss_records:
        if r.quantity >= 10:
            high_loss_count += 1
        if r.reason and ("未及时" in r.reason or "操作不当" in r.reason or "疏忽" in r.reason):
            unreasonable_reasons += 1

    error_count = high_loss_count + unreasonable_reasons

    if operations_count == 0:
        score = 60.0
    else:
        error_rate = error_count / max(operations_count, 1)
        avg_loss = total_qty / max(operations_count, 1)
        qty_penalty = min(avg_loss * 2, 40)
        score = max(0.0, min(100.0, 100.0 - error_rate * 50 - qty_penalty))

    return {
        "score": round(score, 2),
        "operations_count": operations_count,
        "error_count": error_count,
        "details": {
            "total_loss_quantity": total_qty,
            "high_loss_count": high_loss_count,
            "unreasonable_reason_count": unreasonable_reasons,
        },
    }


async def analyze_warning_competency(
    user_id: str,
    loader: BatchRecordLoader,
) -> Dict[str, Any]:
    warnings = loader.get_warnings_for_user(user_id)

    operations_count = len(warnings)
    overdue_count = 0
    avg_hours_list = []
    for w in warnings:
        if w.handled_at and w.created_at:
            hours = (w.handled_at - w.created_at).total_seconds() / 3600
            avg_hours_list.append(hours)
            if hours > WARNING_HANDLE_OVERDUE_HOURS:
                overdue_count += 1

    avg_handle_hours = round(sum(avg_hours_list) / len(avg_hours_list), 2) if avg_hours_list else 0.0

    if operations_count == 0:
        score = 60.0
    else:
        on_time_rate = (operations_count - overdue_count) / operations_count * 100
        hours_penalty = min(avg_handle_hours * 2, 30)
        score = max(0.0, min(100.0, on_time_rate - hours_penalty))

    return {
        "score": round(score, 2),
        "operations_count": operations_count,
        "error_count": overdue_count,
        "details": {
            "overdue_count": overdue_count,
            "avg_handle_hours": avg_handle_hours,
        },
    }


async def analyze_operation_competency(
    dimension: CompetencyDimension,
    user_id: str,
    loader: BatchRecordLoader,
) -> Dict[str, Any]:
    operator_name = await get_operator_name(user_id)

    operations_count = 0
    error_count = 0

    if dimension == CompetencyDimension.IN_BUCKET:
        records = loader.get_in_records_for_user(user_id, operator_name)
        operations_count = len(records)
        for r in records:
            if r.quantity > 50:
                error_count += 1
            if r.remark and ("错误" in r.remark or "纠正" in r.remark):
                error_count += 1

    elif dimension == CompetencyDimension.OUT_BUCKET:
        records = loader.get_out_records_for_user(user_id, operator_name)
        operations_count = len(records)
        for r in records:
            if r.remark and ("错误" in r.remark or "纠正" in r.remark or "遗漏" in r.remark):
                error_count += 1

    elif dimension == CompetencyDimension.PRESERVATION:
        records = loader.get_pres_records_for_user(user_id, operator_name)
        operations_count = len(records)
        for r in records:
            diff = abs(r.after_quantity - r.previous_quantity - r.supplement_quantity)
            if diff > 5:
                error_count += 1
            if r.supplement_quantity <= 0:
                error_count += 1

    if operations_count == 0:
        score = 55.0
    else:
        error_rate = error_count / max(operations_count, 1)
        score = max(0.0, min(100.0, 100.0 - error_rate * 80))

    return {
        "score": round(score, 2),
        "operations_count": operations_count,
        "error_count": error_count,
        "details": {
            "error_rate": round(error_count / max(operations_count, 1) * 100, 2),
        },
    }


async def assess_employee_competency(
    user: User,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
) -> EmployeeCompetencyAssessment:
    ps, pe = resolve_date_range(start_date, end_date)
    date_query = build_date_query(start_date, end_date)

    loader = BatchRecordLoader(date_query, store_id)
    await loader.load_all()

    competency_scores: List[CompetencyScoreItem] = []

    dimensions = [
        (CompetencyDimension.IN_BUCKET, lambda: analyze_operation_competency(CompetencyDimension.IN_BUCKET, str(user.id), loader)),
        (CompetencyDimension.OUT_BUCKET, lambda: analyze_operation_competency(CompetencyDimension.OUT_BUCKET, str(user.id), loader)),
        (CompetencyDimension.PRESERVATION, lambda: analyze_operation_competency(CompetencyDimension.PRESERVATION, str(user.id), loader)),
        (CompetencyDimension.LOSS_HANDLING, lambda: analyze_loss_competency(str(user.id), loader)),
        (CompetencyDimension.WARNING_HANDLING, lambda: analyze_warning_competency(str(user.id), loader)),
        (CompetencyDimension.INSPECTION, lambda: analyze_inspection_competency(str(user.id), loader)),
    ]

    for dim, analyzer in dimensions:
        result = await analyzer()
        level = get_competency_level(result["score"])
        competency_scores.append(CompetencyScoreItem(
            dimension=dim,
            dimension_label=COMPETENCY_LABELS.get(dim, dim.value),
            score=result["score"],
            level=level,
            operations_count=result["operations_count"],
            error_count=result["error_count"],
            details=result["details"],
        ))

    valid_scores = [s.score for s in competency_scores if s.operations_count > 0]
    if not valid_scores:
        valid_scores = [s.score for s in competency_scores]
    overall_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0
    overall_level = get_competency_level(overall_score)

    weak_dimensions = [s.dimension for s in competency_scores if s.level in ("weak", "poor")]
    strong_dimensions = [s.dimension for s in competency_scores if s.level in ("excellent", "good")]

    training_suggestions: List[str] = []
    for s in competency_scores:
        if s.level in ("weak", "poor"):
            label = COMPETENCY_LABELS.get(s.dimension, s.dimension.value)
            if s.score < 40:
                training_suggestions.append(f"【紧急】{label}能力严重不足（{s.score}分），建议立即安排专项强化培训并进行考核")
            else:
                training_suggestions.append(f"【注意】{label}能力偏弱（{s.score}分），建议安排复训和实操练习")
        elif s.level == "normal":
            label = COMPETENCY_LABELS.get(s.dimension, s.dimension.value)
            if s.error_count > 0:
                training_suggestions.append(f"【建议】{label}存在{s.error_count}次操作问题，建议针对性培训巩固")

    if not training_suggestions:
        training_suggestions.append("员工各项能力表现良好，建议保持现有培训节奏，可安排进阶技能提升")

    user_store = store_id
    store_obj = None
    if not user_store:
        store_obj = await get_user_store(user)
        if store_obj:
            user_store = str(store_obj.id)

    if user_store and not store_obj:
        store_obj = await Store.get(ObjectId(user_store))

    assessment = EmployeeCompetencyAssessment(
        user=user,
        user_name=user.full_name or user.username,
        position=user.position,
        position_label=POSITION_LABELS.get(user.position, "其他") if user.position else "其他",
        store=store_obj,
        store_name=store_obj.store_name if store_obj else None,
        period_start=datetime.fromisoformat(ps),
        period_end=datetime.fromisoformat(pe),
        overall_score=overall_score,
        overall_level=overall_level,
        competency_scores=competency_scores,
        weak_dimensions=weak_dimensions,
        strong_dimensions=strong_dimensions,
        training_suggestions=training_suggestions,
    )

    existing = await EmployeeCompetencyAssessment.find_one(
        EmployeeCompetencyAssessment.user.id == user.id,
        EmployeeCompetencyAssessment.period_start == assessment.period_start,
        EmployeeCompetencyAssessment.period_end == assessment.period_end,
    )
    if existing:
        await existing.delete()
    await assessment.create()

    return assessment


def assessment_to_response(a: EmployeeCompetencyAssessment) -> Dict[str, Any]:
    return {
        "_id": str(a.id),
        "user_id": str(a.user.id) if a.user else "",
        "user_name": a.user_name,
        "position": a.position.value if isinstance(a.position, EmployeePosition) else a.position,
        "position_label": a.position_label,
        "store_id": str(a.store.id) if a.store and hasattr(a.store, 'id') else (str(a.store) if a.store else None),
        "store_name": a.store_name,
        "period_start": a.period_start.isoformat()[:10],
        "period_end": a.period_end.isoformat()[:10],
        "overall_score": a.overall_score,
        "overall_level": a.overall_level,
        "overall_level_label": COMPETENCY_LEVEL_LABELS.get(a.overall_level, a.overall_level),
        "competency_scores": [
            {
                "dimension": s.dimension.value if isinstance(s.dimension, CompetencyDimension) else s.dimension,
                "dimension_label": s.dimension_label,
                "score": s.score,
                "max_score": s.max_score,
                "level": s.level,
                "level_label": COMPETENCY_LEVEL_LABELS.get(s.level, s.level),
                "operations_count": s.operations_count,
                "error_count": s.error_count,
                "details": s.details,
            }
            for s in a.competency_scores
        ],
        "weak_dimensions": [d.value if isinstance(d, CompetencyDimension) else d for d in a.weak_dimensions],
        "strong_dimensions": [d.value if isinstance(d, CompetencyDimension) else d for d in a.strong_dimensions],
        "training_suggestions": a.training_suggestions,
        "created_at": a.created_at.isoformat(),
    }


def task_to_response(t: EmployeeTrainingTask) -> Dict[str, Any]:
    position_val = t.position.value if isinstance(t.position, EmployeePosition) else t.position
    store_id = None
    if t.store:
        if hasattr(t.store, 'id'):
            store_id = str(t.store.id)
        else:
            store_id = str(t.store)
    course_id = None
    if t.course:
        if hasattr(t.course, 'id'):
            course_id = str(t.course.id)
        else:
            course_id = str(t.course)
    dim_val = t.competency_dimension.value if isinstance(t.competency_dimension, CompetencyDimension) else t.competency_dimension
    task_type_val = t.task_type.value if isinstance(t.task_type, TrainingTaskType) else t.task_type
    status_val = t.status.value if isinstance(t.status, TrainingTaskStatus) else t.status

    return {
        "_id": str(t.id),
        "user_id": str(t.user.id) if t.user and hasattr(t.user, 'id') else (str(t.user) if t.user else ""),
        "user_name": t.user_name,
        "position": position_val,
        "position_label": POSITION_LABELS.get(t.position, "") if t.position else "",
        "store_id": store_id,
        "store_name": t.store_name,
        "course_id": course_id,
        "course_name": t.course_name,
        "competency_dimension": dim_val,
        "competency_dimension_label": COMPETENCY_LABELS.get(t.competency_dimension, dim_val),
        "task_type": task_type_val,
        "task_type_label": TRAINING_TASK_TYPE_LABELS.get(t.task_type, task_type_val),
        "status": status_val,
        "status_label": TRAINING_TASK_STATUS_LABELS.get(t.status, status_val),
        "assigned_at": t.assigned_at.isoformat(),
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "score": t.score,
        "passed": t.passed,
        "attempts": t.attempts,
        "remark": t.remark,
        "related_error_ids": t.related_error_ids,
        "related_trace_ids": t.related_trace_ids,
    }


async def create_training_task(
    req_data: Dict[str, Any],
) -> Dict[str, Any]:
    user = await User.get(ObjectId(req_data["user_id"]))
    if not user:
        raise ValueError("用户不存在")

    store_obj = None
    store_name = None
    store_obj = await get_user_store(user)
    if store_obj:
        store_name = store_obj.store_name

    course = None
    if req_data.get("course_id"):
        course = await TrainingCourse.get(ObjectId(req_data["course_id"]))

    deadline = None
    if req_data.get("deadline"):
        deadline = datetime.fromisoformat(req_data["deadline"])

    task = EmployeeTrainingTask(
        user=user,
        user_name=user.full_name or user.username,
        position=user.position,
        store=store_obj,
        store_name=store_name,
        course=course,
        course_name=req_data["course_name"],
        competency_dimension=CompetencyDimension(req_data["competency_dimension"]),
        task_type=TrainingTaskType(req_data.get("task_type", "refresher")),
        deadline=deadline,
        remark=req_data.get("remark"),
        related_error_ids=req_data.get("related_error_ids", []),
        related_trace_ids=req_data.get("related_trace_ids", []),
    )
    await task.create()
    return task_to_response(task)


async def update_training_task(
    task_id: str,
    req_data: Dict[str, Any],
) -> Dict[str, Any]:
    task = await EmployeeTrainingTask.get(ObjectId(task_id))
    if not task:
        raise ValueError("培训任务不存在")

    if req_data.get("status"):
        task.status = TrainingTaskStatus(req_data["status"])
        if task.status == TrainingTaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.utcnow()
        if task.status in (TrainingTaskStatus.COMPLETED, TrainingTaskStatus.FAILED):
            task.completed_at = datetime.utcnow()
            task.attempts += 1
    if req_data.get("score") is not None:
        task.score = req_data["score"]
        if task.course:
            course_obj = task.course
            if hasattr(course_obj, 'passing_score'):
                task.passed = task.score >= course_obj.passing_score
            else:
                task.passed = task.score >= 80.0
        else:
            task.passed = task.score >= 80.0
    if req_data.get("passed") is not None:
        task.passed = req_data["passed"]
    if req_data.get("remark"):
        task.remark = req_data["remark"]

    await task.save()
    return task_to_response(task)


async def list_training_tasks(
    user_id: Optional[str] = None,
    store_id: Optional[str] = None,
    position: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    competency_dimension: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    query = {}
    if user_id:
        query["user"] = ObjectId(user_id)
    if store_id:
        query["store"] = ObjectId(store_id)
    if position:
        query["position"] = EmployeePosition(position)
    if status:
        query["status"] = TrainingTaskStatus(status)
    if task_type:
        query["task_type"] = TrainingTaskType(task_type)
    if competency_dimension:
        query["competency_dimension"] = CompetencyDimension(competency_dimension)

    date_query = build_date_query(start_date, end_date)
    if date_query:
        query["assigned_at"] = date_query

    tasks_cursor = EmployeeTrainingTask.find(query, fetch_links=True).sort("-assigned_at")
    total = await tasks_cursor.count()
    tasks = await tasks_cursor.skip((page - 1) * page_size).limit(page_size).to_list()

    return {
        "items": [task_to_response(t) for t in tasks],
        "total": total,
    }


async def get_training_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
    position: Optional[str] = None,
) -> Dict[str, Any]:
    ps, pe = resolve_date_range(start_date, end_date)

    task_query = {}
    assessment_query = {}
    if store_id:
        task_query["store"] = ObjectId(store_id)
        assessment_query["store"] = ObjectId(store_id)
    if position:
        task_query["position"] = EmployeePosition(position)
        assessment_query["position"] = EmployeePosition(position)

    date_q = build_date_query(start_date, end_date)
    if date_q:
        task_query["assigned_at"] = date_q
        assessment_query["period_start"] = {"$gte": date_q.get("$gte", datetime.utcnow() - timedelta(days=30))}

    tasks = await EmployeeTrainingTask.find(task_query).to_list()
    assessments = await EmployeeCompetencyAssessment.find(assessment_query).to_list()

    total_tasks = len(tasks)
    pending = sum(1 for t in tasks if t.status == TrainingTaskStatus.PENDING)
    in_progress = sum(1 for t in tasks if t.status == TrainingTaskStatus.IN_PROGRESS)
    completed = sum(1 for t in tasks if t.status == TrainingTaskStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == TrainingTaskStatus.FAILED)

    refresher_tasks = [t for t in tasks if t.task_type == TrainingTaskType.REFRESHER]
    refresher_passed = sum(1 for t in refresher_tasks if t.status == TrainingTaskStatus.COMPLETED and t.passed)
    refresher_pass_rate = round(refresher_passed / len(refresher_tasks) * 100, 2) if refresher_tasks else 0.0

    exam_tasks = [t for t in tasks if t.task_type == TrainingTaskType.EXAM]
    exam_passed = sum(1 for t in exam_tasks if t.status == TrainingTaskStatus.COMPLETED and t.passed)
    exam_pass_rate = round(exam_passed / len(exam_tasks) * 100, 2) if exam_tasks else 0.0

    completion_rate = round((completed) / max(total_tasks - pending - in_progress, 1) * 100, 2) if total_tasks > 0 else 0.0

    user_task_map: Dict[str, List[EmployeeTrainingTask]] = {}
    for t in tasks:
        uid = str(t.user.id) if hasattr(t.user, 'id') else str(t.user)
        if uid not in user_task_map:
            user_task_map[uid] = []
        user_task_map[uid].append(t)

    recurrence_count = 0
    total_employees_with_tasks = len(user_task_map)
    for uid, user_tasks in user_task_map.items():
        failed_tasks = [t for t in user_tasks if t.status == TrainingTaskStatus.FAILED]
        dims = set()
        for ft in failed_tasks:
            dim_val = ft.competency_dimension.value if isinstance(ft.competency_dimension, CompetencyDimension) else ft.competency_dimension
            if dim_val in dims:
                recurrence_count += 1
            dims.add(dim_val)
    recurrence_rate = round(recurrence_count / max(total_employees_with_tasks, 1) * 100, 2)

    avg_overall = 0.0
    if assessments:
        avg_overall = round(sum(a.overall_score for a in assessments) / len(assessments), 2)

    dimension_scores: Dict[str, List[float]] = {}
    for a in assessments:
        for s in a.competency_scores:
            dim_val = s.dimension.value if isinstance(s.dimension, CompetencyDimension) else s.dimension
            if dim_val not in dimension_scores:
                dimension_scores[dim_val] = []
            dimension_scores[dim_val].append(s.score)

    dimension_score_list = []
    for dim, scores in dimension_scores.items():
        dimension_score_list.append({
            "dimension": dim,
            "dimension_label": COMPETENCY_LABELS.get(CompetencyDimension(dim), dim),
            "avg_score": round(sum(scores) / len(scores), 2),
            "employee_count": len(scores),
        })

    trend_data = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        week_start = (now - timedelta(days=i * 7)).isoformat()[:10]
        week_end = (now - timedelta(days=(i - 1) * 7 - 1)).isoformat()[:10]
        week_date_q = build_date_query(week_start, week_end)
        week_query = dict(task_query)
        if week_date_q:
            week_query["assigned_at"] = week_date_q
        week_tasks = await EmployeeTrainingTask.find(week_query).to_list()
        week_completed = sum(1 for t in week_tasks if t.status == TrainingTaskStatus.COMPLETED)
        week_total = len(week_tasks)
        week_rate = round(week_completed / max(week_total, 1) * 100, 2)
        trend_data.append({
            "period": f"{week_start} ~ {week_end}",
            "total_tasks": week_total,
            "completed_tasks": week_completed,
            "completion_rate": week_rate,
        })

    store_name = None
    if store_id:
        s = await Store.get(ObjectId(store_id))
        if s:
            store_name = s.store_name

    return {
        "period_start": ps,
        "period_end": pe,
        "store_id": store_id,
        "store_name": store_name,
        "total_employees": total_employees_with_tasks,
        "total_tasks": total_tasks,
        "pending_tasks": pending,
        "in_progress_tasks": in_progress,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "training_completion_rate": completion_rate,
        "refresher_tasks": len(refresher_tasks),
        "refresher_passed": refresher_passed,
        "refresher_pass_rate": refresher_pass_rate,
        "exam_tasks": len(exam_tasks),
        "exam_passed": exam_passed,
        "exam_pass_rate": exam_pass_rate,
        "problem_recurrence_rate": recurrence_rate,
        "avg_overall_score": avg_overall,
        "dimension_scores": dimension_score_list,
        "trend_data": trend_data,
    }


async def analyze_high_frequency_errors(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
    min_occurrences: int = 3,
) -> List[Dict[str, Any]]:
    ps, pe = resolve_date_range(start_date, end_date)
    dt_start = datetime.fromisoformat(ps)
    dt_end = datetime.fromisoformat(pe) + timedelta(days=1)

    trace_query = {
        "created_at": {"$gte": dt_start, "$lte": dt_end},
        "action": {"$in": [
            ResponsibilityAction.LOSS,
            ResponsibilityAction.WARNING_HANDLE,
        ]},
    }
    if store_id:
        trace_query["store"] = ObjectId(store_id)

    traces = await ResponsibilityTrace.find(trace_query, fetch_links=True).sort("-created_at").limit(500).to_list()

    error_groups: Dict[str, Dict[str, Any]] = {}

    for t in traces:
        action_val = t.action.value if isinstance(t.action, ResponsibilityAction) else t.action
        if action_val == "loss":
            error_type = "loss_handling"
            dim = CompetencyDimension.LOSS_HANDLING
            label = "损耗处理不当"
            desc = "损耗记录异常或损耗数量偏大"
        elif action_val == "warning_handle":
            error_type = "warning_overdue"
            dim = CompetencyDimension.WARNING_HANDLING
            label = "预警处置超时"
            desc = "预警未在24小时内及时处置"
        else:
            continue

        uid = str(t.operator.id) if t.operator and hasattr(t.operator, 'id') else (str(t.operator) if t.operator else "")
        sid = str(t.store.id) if t.store and hasattr(t.store, 'id') else (str(t.store) if t.store else "")

        if error_type not in error_groups:
            error_groups[error_type] = {
                "error_type": error_type,
                "error_type_label": label,
                "competency_dimension": dim,
                "description": desc,
                "occurrence_count": 0,
                "affected_employees": set(),
                "affected_stores": set(),
                "related_trace_ids": [],
                "sample_traces": [],
            }

        g = error_groups[error_type]
        g["occurrence_count"] += 1
        if uid:
            g["affected_employees"].add(uid)
        if sid:
            g["affected_stores"].add(sid)
        g["related_trace_ids"].append(str(t.id))
        if len(g["sample_traces"]) < 5:
            g["sample_traces"].append({
                "trace_id": str(t.id),
                "operator_name": t.operator_name,
                "created_at": t.created_at.isoformat(),
                "remark": t.remark,
                "batch_no": t.batch_no,
            })

    result = []
    for g in error_groups.values():
        if g["occurrence_count"] >= min_occurrences:
            existing = await HighFrequencyError.find_one(
                HighFrequencyError.error_type == g["error_type"],
                HighFrequencyError.period_start == dt_start,
                HighFrequencyError.period_end == dt_end,
            )
            if existing:
                await existing.delete()

            err = HighFrequencyError(
                error_type=g["error_type"],
                error_type_label=g["error_type_label"],
                competency_dimension=g["competency_dimension"],
                description=g["description"],
                occurrence_count=g["occurrence_count"],
                affected_employees=list(g["affected_employees"]),
                affected_stores=list(g["affected_stores"]),
                related_trace_ids=g["related_trace_ids"],
                sample_traces=g["sample_traces"],
                period_start=dt_start,
                period_end=dt_end,
            )
            await err.create()

            dim_val = g["competency_dimension"].value if isinstance(g["competency_dimension"], CompetencyDimension) else g["competency_dimension"]
            result.append({
                "_id": str(err.id),
                "error_type": g["error_type"],
                "error_type_label": g["error_type_label"],
                "competency_dimension": dim_val,
                "competency_dimension_label": COMPETENCY_LABELS.get(g["competency_dimension"], dim_val),
                "description": g["description"],
                "occurrence_count": g["occurrence_count"],
                "affected_employee_count": len(g["affected_employees"]),
                "affected_store_count": len(g["affected_stores"]),
                "period_start": ps,
                "period_end": pe,
                "related_trace_ids": g["related_trace_ids"],
                "sample_traces": g["sample_traces"],
                "created_at": err.created_at.isoformat(),
                "updated_at": err.updated_at.isoformat(),
            })

    result.sort(key=lambda x: x["occurrence_count"], reverse=True)
    return result


async def link_error_to_traces(
    req_data: Dict[str, Any],
) -> Dict[str, Any]:
    ps = (datetime.utcnow() - timedelta(days=30)).isoformat()[:10]
    pe = datetime.utcnow().isoformat()[:10]
    dt_start = datetime.fromisoformat(ps)
    dt_end = datetime.fromisoformat(pe) + timedelta(days=1)

    existing = await HighFrequencyError.find_one(
        HighFrequencyError.error_type == req_data["error_type"],
        HighFrequencyError.period_start == dt_start,
        HighFrequencyError.period_end == dt_end,
    )

    affected_employees: set = set()
    affected_stores: set = set()
    sample_traces: List[Dict] = []

    for tid in req_data.get("trace_ids", []):
        try:
            trace = await ResponsibilityTrace.get(ObjectId(tid), fetch_links=True)
            if trace:
                uid = str(trace.operator.id) if trace.operator and hasattr(trace.operator, 'id') else ""
                sid = str(trace.store.id) if trace.store and hasattr(trace.store, 'id') else ""
                if uid:
                    affected_employees.add(uid)
                if sid:
                    affected_stores.add(sid)
                if len(sample_traces) < 5:
                    sample_traces.append({
                        "trace_id": str(trace.id),
                        "operator_name": trace.operator_name,
                        "created_at": trace.created_at.isoformat(),
                        "remark": trace.remark,
                        "batch_no": trace.batch_no,
                    })
        except Exception:
            pass

    if existing:
        existing.occurrence_count += len(req_data.get("trace_ids", []))
        existing.affected_employees = list(set(existing.affected_employees) | affected_employees)
        existing.affected_stores = list(set(existing.affected_stores) | affected_stores)
        existing.related_trace_ids = list(set(existing.related_trace_ids + req_data.get("trace_ids", [])))
        if sample_traces and len(existing.sample_traces) < 5:
            existing.sample_traces.extend(sample_traces[:5 - len(existing.sample_traces)])
        existing.updated_at = datetime.utcnow()
        await existing.save()
        err = existing
    else:
        err = HighFrequencyError(
            error_type=req_data["error_type"],
            error_type_label=req_data["error_type_label"],
            competency_dimension=CompetencyDimension(req_data["competency_dimension"]),
            description=req_data["description"],
            occurrence_count=len(req_data.get("trace_ids", [])),
            affected_employees=list(affected_employees),
            affected_stores=list(affected_stores),
            related_trace_ids=req_data.get("trace_ids", []),
            sample_traces=sample_traces,
            period_start=dt_start,
            period_end=dt_end,
        )
        await err.create()

    dim_val = err.competency_dimension.value if isinstance(err.competency_dimension, CompetencyDimension) else err.competency_dimension
    return {
        "_id": str(err.id),
        "error_type": err.error_type,
        "error_type_label": err.error_type_label,
        "competency_dimension": dim_val,
        "competency_dimension_label": COMPETENCY_LABELS.get(err.competency_dimension, dim_val),
        "description": err.description,
        "occurrence_count": err.occurrence_count,
        "affected_employee_count": len(err.affected_employees),
        "affected_store_count": len(err.affected_stores),
        "period_start": ps,
        "period_end": pe,
        "related_trace_ids": err.related_trace_ids,
        "sample_traces": err.sample_traces,
        "created_at": err.created_at.isoformat(),
        "updated_at": err.updated_at.isoformat(),
    }


async def list_competency_dimensions() -> List[Dict[str, Any]]:
    result = []
    for dim in CompetencyDimension:
        result.append({
            "code": dim.value,
            "label": COMPETENCY_LABELS.get(dim, dim.value),
        })
    return result
