from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from bson import ObjectId
from app.models import (
    User,
    EmployeePosition,
    POSITION_LABELS,
    ResponsibilityTargetType,
)
from app.schemas.performance import (
    PositionInfo,
    PerformanceRankingResponse,
    ResponsibilityTraceResponse,
    PerformanceSummary,
)
from app.services.auth import get_current_active_user
from app.services.performance import (
    get_performance_ranking,
    get_employee_performance,
    get_responsibility_trace,
    get_performance_summary,
)

router = APIRouter()


@router.get("/positions")
async def get_positions(
    current_user: User = Depends(get_current_active_user),
):
    positions = []
    for pos in EmployeePosition:
        positions.append(PositionInfo(code=pos.value, label=POSITION_LABELS.get(pos, pos.value)))
    return positions


@router.get("/summary", response_model=PerformanceSummary)
async def get_perf_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    return await get_performance_summary(start_date, end_date, store_id)


@router.get("/ranking", response_model=PerformanceRankingResponse)
async def get_perf_ranking(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    sort_by: str = Query("score", regex="^(score|total_operations|on_time_rate|loss_rate)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    results = await get_performance_ranking(start_date, end_date, store_id, position, sort_by)
    total = len(results)
    start_idx = (page - 1) * page_size
    paginated = results[start_idx:start_idx + page_size]

    ps = start_date or ""
    pe = end_date or ""

    return PerformanceRankingResponse(
        items=paginated,
        total=total,
        period_start=ps,
        period_end=pe,
    )


@router.get("/employee/{user_id}")
async def get_employee_perf(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    user = await User.get(ObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return await get_employee_performance(user, start_date, end_date)


@router.get("/responsibility-trace", response_model=ResponsibilityTraceResponse)
async def get_trace(
    target_type: str = Query(..., regex="^(bucket|flower|warning)$"),
    target_id: str = Query(...),
    current_user: User = Depends(get_current_active_user),
):
    try:
        tt = ResponsibilityTargetType(target_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的目标类型")
    return await get_responsibility_trace(tt, target_id)
