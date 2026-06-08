from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from bson import ObjectId
from app.models import (
    User,
)
from app.schemas.training import (
    CreateTrainingTaskRequest,
    UpdateTrainingTaskRequest,
    ErrorTraceLinkRequest,
)
from app.services.auth import get_current_active_user
from app.services.training import (
    assess_employee_competency,
    assessment_to_response,
    create_training_task,
    update_training_task,
    list_training_tasks,
    get_training_stats,
    analyze_high_frequency_errors,
    link_error_to_traces,
    list_competency_dimensions,
)

router = APIRouter()


@router.get("/dimensions")
async def get_competency_dimensions(
    current_user: User = Depends(get_current_active_user),
):
    return await list_competency_dimensions()


@router.get("/assessment/employee/{user_id}")
async def get_employee_assessment(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    user = await User.get(ObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    assessment = await assess_employee_competency(user, start_date, end_date, store_id)
    return assessment_to_response(assessment)


@router.get("/assessment/refresh/{user_id}")
async def refresh_employee_assessment(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    user = await User.get(ObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    assessment = await assess_employee_competency(user, start_date, end_date, store_id)
    return assessment_to_response(assessment)


@router.post("/tasks")
async def create_task(
    req: CreateTrainingTaskRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await create_training_task(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    req: UpdateTrainingTaskRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await update_training_task(task_id, req.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tasks")
async def get_tasks(
    user_id: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    competency_dimension: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    return await list_training_tasks(
        user_id=user_id,
        store_id=store_id,
        position=position,
        status=status,
        task_type=task_type,
        competency_dimension=competency_dimension,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def get_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    return await get_training_stats(start_date, end_date, store_id, position)


@router.get("/high-frequency-errors")
async def get_high_frequency_errors(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    min_occurrences: int = Query(3, ge=1),
    current_user: User = Depends(get_current_active_user),
):
    return await analyze_high_frequency_errors(start_date, end_date, store_id, min_occurrences)


@router.post("/link-error-traces")
async def link_error_trace(
    req: ErrorTraceLinkRequest,
    current_user: User = Depends(get_current_active_user),
):
    return await link_error_to_traces(req.model_dump())
