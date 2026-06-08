from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from bson import ObjectId
from app.models import (
    Bucket,
    BucketStatus,
    Flower,
    Store,
    User,
    BucketInRecord,
    BucketOutRecord,
    PreservationRecord,
    LossRecord,
    ResponsibilityTargetType,
    ResponsibilityAction,
)
from app.schemas.record import (
    BucketInCreate,
    BucketInResponse,
    BucketOutCreate,
    BucketOutResponse,
    PreservationCreate,
    PreservationResponse,
    LossCreate,
    LossResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.auth import get_current_active_user
from app.services.performance import add_responsibility_trace

router = APIRouter()


def in_record_to_response(rec: BucketInRecord) -> dict:
    data = rec.model_dump(by_alias=True)
    data["_id"] = str(rec.id)
    if isinstance(rec.bucket, Bucket):
        data["bucket"] = {"id": str(rec.bucket.id), "bucket_code": rec.bucket.bucket_code}
    else:
        data["bucket"] = {"id": str(rec.bucket), "bucket_code": ""}
    if isinstance(rec.flower, Flower):
        data["flower"] = {
            "id": str(rec.flower.id),
            "flower_name": rec.flower.flower_name,
            "flower_code": rec.flower.flower_code,
        }
    else:
        data["flower"] = {"id": str(rec.flower), "flower_name": "", "flower_code": ""}
    return data


def out_record_to_response(rec: BucketOutRecord) -> dict:
    return in_record_to_response(rec)


def preservation_to_response(rec: PreservationRecord) -> dict:
    data = rec.model_dump(by_alias=True)
    data["_id"] = str(rec.id)
    if isinstance(rec.bucket, Bucket):
        data["bucket"] = {"id": str(rec.bucket.id), "bucket_code": rec.bucket.bucket_code}
    else:
        data["bucket"] = {"id": str(rec.bucket), "bucket_code": ""}
    if isinstance(rec.store, Store):
        data["store"] = {"id": str(rec.store.id), "store_name": rec.store.store_name}
    elif rec.store:
        data["store"] = {"id": str(rec.store), "store_name": ""}
    else:
        data["store"] = None
    return data


def loss_to_response(rec: LossRecord) -> dict:
    data = rec.model_dump(by_alias=True)
    data["_id"] = str(rec.id)
    if isinstance(rec.flower, Flower):
        data["flower"] = {
            "id": str(rec.flower.id),
            "flower_name": rec.flower.flower_name,
            "flower_code": rec.flower.flower_code,
        }
    else:
        data["flower"] = {"id": str(rec.flower), "flower_name": "", "flower_code": ""}
    if isinstance(rec.store, Store):
        data["store"] = {"id": str(rec.store.id), "store_name": rec.store.store_name}
    elif rec.store:
        data["store"] = {"id": str(rec.store), "store_name": ""}
    else:
        data["store"] = None
    return data


@router.post("/in-bucket", response_model=BucketInResponse)
async def create_bucket_in(
    record_in: BucketInCreate,
    current_user: User = Depends(get_current_active_user),
):
    bucket = await Bucket.get(ObjectId(record_in.bucket_id), fetch_links=True)
    if not bucket:
        raise HTTPException(status_code=404, detail="花桶不存在")
    if bucket.status != BucketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="停用花桶不能办理入桶")

    flower = await Flower.get(ObjectId(record_in.flower_id))
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")

    new_quantity = bucket.current_quantity + record_in.quantity
    if new_quantity > bucket.capacity:
        raise HTTPException(status_code=400, detail="桶体当前数量不能超过容量")

    bucket.current_quantity = new_quantity
    bucket.updated_at = datetime.utcnow()
    await bucket.save()

    flower.bucket = bucket
    flower.store = bucket.store if isinstance(bucket.store, Store) else flower.store
    flower.current_quantity += record_in.quantity
    flower.in_bucket_date = datetime.utcnow()
    flower.updated_at = datetime.utcnow()
    await flower.save()

    operator_name = record_in.operator or current_user.full_name or current_user.username
    record = BucketInRecord(
        bucket=bucket,
        flower=flower,
        quantity=record_in.quantity,
        operator=operator_name,
        remark=record_in.remark,
    )
    await record.create()

    store = bucket.store if isinstance(bucket.store, Store) else None
    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.BUCKET,
        target_id=str(bucket.id),
        action=ResponsibilityAction.IN_BUCKET,
        user=current_user,
        operator_name=operator_name,
        remark=f"入桶 {record_in.quantity} 枝花材",
        store=store,
        bucket=bucket,
        flower=flower,
    )
    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.FLOWER,
        target_id=str(flower.id),
        action=ResponsibilityAction.IN_BUCKET,
        user=current_user,
        operator_name=operator_name,
        remark=f"入桶 {record_in.quantity} 枝到花桶 {bucket.bucket_code}",
        store=store,
        bucket=bucket,
        flower=flower,
    )
    return in_record_to_response(record)


@router.post("/out-bucket", response_model=BucketOutResponse)
async def create_bucket_out(
    record_in: BucketOutCreate,
    current_user: User = Depends(get_current_active_user),
):
    bucket = await Bucket.get(ObjectId(record_in.bucket_id))
    if not bucket:
        raise HTTPException(status_code=404, detail="花桶不存在")

    flower = await Flower.get(ObjectId(record_in.flower_id))
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")

    if record_in.quantity > bucket.current_quantity:
        raise HTTPException(status_code=400, detail="回桶数量不能超过桶内数量")
    if record_in.quantity > flower.current_quantity:
        raise HTTPException(status_code=400, detail="回桶数量不能超过花材当前数量")

    bucket.current_quantity -= record_in.quantity
    bucket.updated_at = datetime.utcnow()
    await bucket.save()

    flower.current_quantity -= record_in.quantity
    if flower.current_quantity <= 0:
        flower.bucket = None
        flower.current_quantity = 0
    flower.updated_at = datetime.utcnow()
    await flower.save()

    operator_name = record_in.operator or current_user.full_name or current_user.username
    record = BucketOutRecord(
        bucket=bucket,
        flower=flower,
        quantity=record_in.quantity,
        operator=operator_name,
        remark=record_in.remark,
    )
    await record.create()

    store = None
    if isinstance(bucket, Bucket) and isinstance(bucket.store, Store):
        store = bucket.store
    elif isinstance(bucket.store, Store):
        store = bucket.store
    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.BUCKET,
        target_id=str(bucket.id),
        action=ResponsibilityAction.OUT_BUCKET,
        user=current_user,
        operator_name=operator_name,
        remark=f"回桶 {record_in.quantity} 枝花材",
        store=store,
        bucket=bucket,
        flower=flower,
    )
    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.FLOWER,
        target_id=str(flower.id),
        action=ResponsibilityAction.OUT_BUCKET,
        user=current_user,
        operator_name=operator_name,
        remark=f"从花桶 {bucket.bucket_code} 回桶 {record_in.quantity} 枝",
        store=store,
        bucket=bucket,
        flower=flower,
    )
    return out_record_to_response(record)


@router.post("/preservation", response_model=PreservationResponse)
async def create_preservation(
    record_in: PreservationCreate,
    current_user: User = Depends(get_current_active_user),
):
    bucket = await Bucket.get(ObjectId(record_in.bucket_id), fetch_links=True)
    if not bucket:
        raise HTTPException(status_code=404, detail="花桶不存在")

    previous_quantity = bucket.current_quantity
    after_quantity = previous_quantity + record_in.supplement_quantity
    if after_quantity > bucket.capacity:
        raise HTTPException(status_code=400, detail="补充后液位不能超过桶体容量")

    bucket.current_quantity = after_quantity
    bucket.updated_at = datetime.utcnow()
    await bucket.save()

    store = bucket.store if isinstance(bucket.store, Store) else None

    operator_name = record_in.operator or current_user.full_name or current_user.username
    record = PreservationRecord(
        bucket=bucket,
        store=store,
        supplement_quantity=record_in.supplement_quantity,
        previous_quantity=previous_quantity,
        after_quantity=after_quantity,
        operator=operator_name,
        remark=record_in.remark,
    )
    await record.create()

    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.BUCKET,
        target_id=str(bucket.id),
        action=ResponsibilityAction.PRESERVATION,
        user=current_user,
        operator_name=operator_name,
        remark=f"补液 {record_in.supplement_quantity}L（{previous_quantity}L → {after_quantity}L）",
        store=store,
        bucket=bucket,
    )
    return preservation_to_response(record)


@router.post("/loss", response_model=LossResponse)
async def create_loss(
    record_in: LossCreate,
    current_user: User = Depends(get_current_active_user),
):
    flower = await Flower.get(ObjectId(record_in.flower_id), fetch_links=True)
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")

    if record_in.quantity > flower.current_quantity:
        raise HTTPException(status_code=400, detail="损耗数量不能超过花材当前数量")

    flower.current_quantity -= record_in.quantity
    if flower.current_quantity <= 0:
        flower.current_quantity = 0
    flower.updated_at = datetime.utcnow()
    await flower.save()

    store = flower.store if isinstance(flower.store, Store) else None

    operator_name = record_in.operator or current_user.full_name or current_user.username
    record = LossRecord(
        flower=flower,
        store=store,
        quantity=record_in.quantity,
        reason=record_in.reason,
        operator=operator_name,
        remark=record_in.remark,
    )
    await record.create()

    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.FLOWER,
        target_id=str(flower.id),
        action=ResponsibilityAction.LOSS,
        user=current_user,
        operator_name=operator_name,
        remark=f"损耗 {record_in.quantity} 枝，原因：{record_in.reason or '未说明'}",
        store=store,
        flower=flower,
    )
    return loss_to_response(record)


@router.get("/in-bucket", response_model=PaginatedResponse)
async def list_bucket_in(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bucket_id: Optional[str] = None,
    flower_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if bucket_id:
        query["bucket"] = ObjectId(bucket_id)
    if flower_id:
        query["flower"] = ObjectId(flower_id)
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date) + timedelta(days=1)
        query["created_at"] = date_query

    total = await BucketInRecord.find(query).count()
    records = (
        await BucketInRecord.find(query, fetch_links=True)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    items = [in_record_to_response(r) for r in records]
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/out-bucket", response_model=PaginatedResponse)
async def list_bucket_out(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bucket_id: Optional[str] = None,
    flower_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if bucket_id:
        query["bucket"] = ObjectId(bucket_id)
    if flower_id:
        query["flower"] = ObjectId(flower_id)
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date) + timedelta(days=1)
        query["created_at"] = date_query

    total = await BucketOutRecord.find(query).count()
    records = (
        await BucketOutRecord.find(query, fetch_links=True)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    items = [out_record_to_response(r) for r in records]
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/preservation", response_model=PaginatedResponse)
async def list_preservation(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bucket_id: Optional[str] = None,
    store_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if bucket_id:
        query["bucket"] = ObjectId(bucket_id)
    if store_id:
        query["store"] = ObjectId(store_id)
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date) + timedelta(days=1)
        query["created_at"] = date_query

    total = await PreservationRecord.find(query).count()
    records = (
        await PreservationRecord.find(query, fetch_links=True)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    items = [preservation_to_response(r) for r in records]
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/loss", response_model=PaginatedResponse)
async def list_loss(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    flower_id: Optional[str] = None,
    store_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if flower_id:
        query["flower"] = ObjectId(flower_id)
    if store_id:
        query["store"] = ObjectId(store_id)
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date) + timedelta(days=1)
        query["created_at"] = date_query

    total = await LossRecord.find(query).count()
    records = (
        await LossRecord.find(query, fetch_links=True)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    items = [loss_to_response(r) for r in records]
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )
