from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.models import (
    User,
    WarningStatus,
)
from app.services.auth import get_current_active_user
from app.services.warning_service import (
    get_warnings,
    handle_warning,
    warning_to_response,
)
from app.services.dashboard_service import (
    get_dashboard_summary,
    get_bucket_turnover,
    get_flower_category_distribution,
    get_store_loss_ranking,
    get_recent_records,
    get_operation_trace,
)

router = APIRouter()


class WarningHandleRequest(BaseModel):
    warning_id: str
    status: WarningStatus
    note: Optional[str] = None


@router.get("/summary")
async def get_dashboard_summary_route(
    current_user: User = Depends(get_current_active_user),
):
    return await get_dashboard_summary()


@router.get("/bucket-turnover")
async def get_bucket_turnover_route(
    current_user: User = Depends(get_current_active_user),
):
    return await get_bucket_turnover()


@router.get("/flower-category-distribution")
async def get_flower_category_distribution_route(
    current_user: User = Depends(get_current_active_user),
):
    return await get_flower_category_distribution()


@router.get("/store-loss-ranking")
async def get_store_loss_ranking_route(
    current_user: User = Depends(get_current_active_user),
):
    return await get_store_loss_ranking()


@router.get("/recent-records")
async def get_recent_records_route(
    current_user: User = Depends(get_current_active_user),
    limit: int = 10,
):
    return await get_recent_records(limit)


@router.get("/warnings")
async def get_warnings_route(
    current_user: User = Depends(get_current_active_user),
    store_id: Optional[str] = Query(None),
    warning_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    return await get_warnings(store_id, warning_type, status)


@router.post("/warnings/handle")
async def handle_warning_route(
    req: WarningHandleRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await handle_warning(req.warning_id, req.status, req.note, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/operation-trace")
async def get_operation_trace_route(
    current_user: User = Depends(get_current_active_user),
    store_id: Optional[str] = Query(None),
    bucket_id: Optional[str] = Query(None),
    flower_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    return await get_operation_trace(
        store_id=store_id,
        bucket_id=bucket_id,
        flower_id=flower_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
