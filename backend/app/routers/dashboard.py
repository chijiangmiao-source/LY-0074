from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any, Optional
from bson import ObjectId
from pydantic import BaseModel
from app.models import (
    User,
    Bucket,
    BucketStatus,
    Flower,
    PreservationStatus,
    Store,
    FlowerCategory,
    BucketInRecord,
    BucketOutRecord,
    PreservationRecord,
    LossRecord,
    Warning,
    WarningType,
    WarningSeverity,
    WarningStatus,
    StatusChangeRecord,
    StatusChangeTarget,
    ResponsibilityTargetType,
    ResponsibilityAction,
)
from app.services.auth import get_current_active_user
from app.services.performance import add_responsibility_trace

router = APIRouter()

LOW_LIQUID_THRESHOLD = 0.3
IN_BUCKET_WARNING_HOURS = 72
HIGH_LOSS_RATE_THRESHOLD = 0.15
MEDIUM_LOSS_RATE_THRESHOLD = 0.08


class WarningHandleRequest(BaseModel):
    warning_id: str
    status: WarningStatus
    note: Optional[str] = None


def warning_to_response(w: Warning) -> dict:
    store_id = ""
    store_name = ""
    if isinstance(w.store, Store):
        store_id = str(w.store.id)
        store_name = w.store.store_name
    elif w.store:
        store_id = str(w.store)

    bucket_id = ""
    bucket_code = ""
    if isinstance(w.bucket, Bucket):
        bucket_id = str(w.bucket.id)
        bucket_code = w.bucket.bucket_code
    elif w.bucket:
        bucket_id = str(w.bucket)

    flower_id = ""
    flower_name = ""
    flower_code = ""
    if isinstance(w.flower, Flower):
        flower_id = str(w.flower.id)
        flower_name = w.flower.flower_name
        flower_code = w.flower.flower_code
    elif w.flower:
        flower_id = str(w.flower)

    handler_name = ""
    if isinstance(w.handler, User):
        handler_name = w.handler.full_name or w.handler.username
    elif w.handler:
        handler_name = str(w.handler)

    return {
        "warning_id": str(w.id),
        "warning_type": w.warning_type.value,
        "warning_type_label": w.warning_type_label,
        "severity": w.severity.value,
        "store_id": store_id,
        "store_name": store_name,
        "bucket_id": bucket_id,
        "bucket_code": bucket_code,
        "flower_id": flower_id,
        "flower_name": flower_name,
        "flower_code": flower_code,
        "message": w.message,
        "current_value": w.current_value,
        "threshold": w.threshold_value,
        "unit": w.unit,
        "status": w.status.value,
        "status_label": {
            WarningStatus.PENDING: "待处理",
            WarningStatus.HANDLING: "处理中",
            WarningStatus.RESOLVED: "已解决",
        }.get(w.status, w.status.value),
        "handler": handler_name,
        "handled_at": w.handled_at.isoformat() if w.handled_at else None,
        "handle_note": w.handle_note,
        "created_at": w.created_at.isoformat(),
        "updated_at": w.updated_at.isoformat(),
    }


@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
):
    total_stores = await Store.find(Store.is_active == True).count()
    total_buckets = await Bucket.find_all().count()
    active_buckets = await Bucket.find(Bucket.status == BucketStatus.ACTIVE).count()
    total_flowers = await Flower.find_all().count()
    in_bucket_flowers = await Flower.find(Flower.bucket != None).count()
    total_preservation = await PreservationRecord.find_all().count()
    total_loss = await LossRecord.find_all().count()

    flower_qty = 0
    flowers = await Flower.find_all().to_list()
    for f in flowers:
        flower_qty += f.current_quantity

    return {
        "total_stores": total_stores,
        "total_buckets": total_buckets,
        "active_buckets": active_buckets,
        "total_flowers": total_flowers,
        "in_bucket_flowers": in_bucket_flowers,
        "total_flower_quantity": flower_qty,
        "total_preservation_records": total_preservation,
        "total_loss_records": total_loss,
    }


@router.get("/bucket-turnover")
async def get_bucket_turnover(
    current_user: User = Depends(get_current_active_user),
):
    buckets = await Bucket.find(fetch_links=True).to_list()
    result = []

    for bucket in buckets:
        in_count = await BucketInRecord.find(BucketInRecord.bucket.id == bucket.id).count()
        out_count = await BucketOutRecord.find(BucketOutRecord.bucket.id == bucket.id).count()
        total_ops = in_count + out_count
        utilization = (bucket.current_quantity / bucket.capacity * 100) if bucket.capacity > 0 else 0

        store_name = ""
        store_code = ""
        if isinstance(bucket.store, Store):
            store_name = bucket.store.store_name
            store_code = bucket.store.store_code

        result.append({
            "bucket_id": str(bucket.id),
            "bucket_code": bucket.bucket_code,
            "store_name": store_name,
            "store_code": store_code,
            "capacity": bucket.capacity,
            "current_quantity": bucket.current_quantity,
            "utilization_rate": round(utilization, 2),
            "status": bucket.status,
            "in_count": in_count,
            "out_count": out_count,
            "turnover_count": total_ops,
        })

    result.sort(key=lambda x: x["turnover_count"], reverse=True)
    return result


@router.get("/flower-category-distribution")
async def get_flower_category_distribution(
    current_user: User = Depends(get_current_active_user),
):
    categories = await FlowerCategory.find_all().to_list()
    result = []

    for cat in categories:
        flowers = await Flower.find(Flower.category.id == cat.id).to_list()
        count = len(flowers)
        qty = sum(f.current_quantity for f in flowers)
        result.append({
            "category_id": str(cat.id),
            "category_code": cat.category_code,
            "category_name": cat.category_name,
            "flower_count": count,
            "total_quantity": qty,
        })

    result.sort(key=lambda x: x["total_quantity"], reverse=True)
    return result


@router.get("/store-loss-ranking")
async def get_store_loss_ranking(
    current_user: User = Depends(get_current_active_user),
):
    stores = await Store.find(Store.is_active == True).to_list()
    result = []
    now = datetime.utcnow()

    for store in stores:
        loss_records = await LossRecord.find(LossRecord.store.id == store.id).to_list()
        total_loss_qty = sum(r.quantity for r in loss_records)
        total_loss_count = len(loss_records)

        recent_7d = [r for r in loss_records if (now - r.created_at).days <= 7]
        recent_loss_qty = sum(r.quantity for r in recent_7d)

        flower_qty = 0
        flowers = await Flower.find(Flower.store.id == store.id).to_list()
        for f in flowers:
            flower_qty += f.current_quantity

        base_total = flower_qty + recent_loss_qty
        loss_rate = recent_loss_qty / base_total if base_total > 0 else 0

        result.append({
            "store_id": str(store.id),
            "store_code": store.store_code,
            "store_name": store.store_name,
            "manager": store.manager,
            "total_loss_quantity": total_loss_qty,
            "total_loss_count": total_loss_count,
            "current_flower_quantity": flower_qty,
            "recent_loss_quantity_7d": recent_loss_qty,
            "loss_rate_7d": round(loss_rate * 100, 2),
        })

    result.sort(key=lambda x: x["total_loss_quantity"], reverse=True)
    for i, r in enumerate(result):
        r["rank"] = i + 1
    return result


@router.get("/recent-records")
async def get_recent_records(
    current_user: User = Depends(get_current_active_user),
    limit: int = 10,
):
    in_records = await BucketInRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()
    out_records = await BucketOutRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()
    preservation_records = await PreservationRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()
    loss_records = await LossRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()

    def fmt_in(r):
        bucket_code = r.bucket.bucket_code if isinstance(r.bucket, Bucket) else ""
        flower_name = r.flower.flower_name if isinstance(r.flower, Flower) else ""
        return {
            "type": "入桶",
            "type_key": "in_bucket",
            "bucket_code": bucket_code,
            "flower_name": flower_name,
            "quantity": r.quantity,
            "operator": r.operator,
            "created_at": r.created_at,
        }

    def fmt_out(r):
        bucket_code = r.bucket.bucket_code if isinstance(r.bucket, Bucket) else ""
        flower_name = r.flower.flower_name if isinstance(r.flower, Flower) else ""
        return {
            "type": "回桶",
            "type_key": "out_bucket",
            "bucket_code": bucket_code,
            "flower_name": flower_name,
            "quantity": r.quantity,
            "operator": r.operator,
            "created_at": r.created_at,
        }

    def fmt_pres(r):
        bucket_code = r.bucket.bucket_code if isinstance(r.bucket, Bucket) else ""
        return {
            "type": "保鲜液补充",
            "type_key": "preservation",
            "bucket_code": bucket_code,
            "flower_name": "-",
            "quantity": r.supplement_quantity,
            "operator": r.operator,
            "created_at": r.created_at,
        }

    def fmt_loss(r):
        flower_name = r.flower.flower_name if isinstance(r.flower, Flower) else ""
        return {
            "type": "损耗",
            "type_key": "loss",
            "bucket_code": "-",
            "flower_name": flower_name,
            "quantity": r.quantity,
            "operator": r.operator,
            "created_at": r.created_at,
        }

    all_records = (
        [fmt_in(r) for r in in_records]
        + [fmt_out(r) for r in out_records]
        + [fmt_pres(r) for r in preservation_records]
        + [fmt_loss(r) for r in loss_records]
    )
    all_records.sort(key=lambda x: x["created_at"], reverse=True)
    return all_records[:limit]


async def sync_generated_warnings(current_user: User):
    """根据当前数据状态生成/更新预警并持久化"""
    now = datetime.utcnow()
    buckets = await Bucket.find(fetch_links=True).to_list()
    flowers = await Flower.find(fetch_links=True).to_list()
    stores = await Store.find(Store.is_active == True).to_list()

    active_keys = set()

    # 液位预警
    for bucket in buckets:
        if bucket.capacity <= 0:
            continue
        liquid_ratio = bucket.current_quantity / bucket.capacity
        if liquid_ratio < LOW_LIQUID_THRESHOLD:
            severity = WarningSeverity.HIGH if liquid_ratio < 0.1 else WarningSeverity.MEDIUM
            key = f"{WarningType.LOW_LIQUID.value}:{bucket.id}"
            active_keys.add(key)
            store_ref = bucket.store if isinstance(bucket.store, Store) else None
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.LOW_LIQUID,
                Warning.bucket.id == bucket.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.LOW_LIQUID,
                    warning_type_label="液位过低",
                    severity=severity,
                    store=store_ref,
                    bucket=bucket,
                    flower=None,
                    message=f"花桶 {bucket.bucket_code} 液位仅 {liquid_ratio*100:.1f}%，需要及时补充保鲜液",
                    current_value=str(round(bucket.current_quantity, 2)),
                    threshold_value=str(round(bucket.capacity * LOW_LIQUID_THRESHOLD, 2)),
                    unit="L",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()
            else:
                existing.severity = severity
                existing.current_value = str(round(bucket.current_quantity, 2))
                existing.message = f"花桶 {bucket.bucket_code} 液位仅 {liquid_ratio*100:.1f}%，需要及时补充保鲜液"
                existing.updated_at = now
                await existing.save()

    # 萎蔫预警
    for flower in flowers:
        if flower.preservation_status == PreservationStatus.WILTED:
            key = f"{WarningType.WILTED.value}:{flower.id}"
            active_keys.add(key)
            store_ref = flower.store if isinstance(flower.store, Store) else None
            bucket_ref = flower.bucket if isinstance(flower.bucket, Bucket) else None
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.WILTED,
                Warning.flower.id == flower.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.WILTED,
                    warning_type_label="花材萎蔫",
                    severity=WarningSeverity.HIGH,
                    store=store_ref,
                    bucket=bucket_ref,
                    flower=flower,
                    message=f"花材 {flower.flower_name}({flower.flower_code}) 已萎蔫，需要及时处理",
                    current_value="wilted",
                    threshold_value="fresh/normal",
                    unit="",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()

    # 入桶超时预警
    for flower in flowers:
        if not flower.in_bucket_date or not flower.bucket:
            continue
        hours_in_bucket = (now - flower.in_bucket_date).total_seconds() / 3600
        if hours_in_bucket > IN_BUCKET_WARNING_HOURS:
            severity = WarningSeverity.MEDIUM if hours_in_bucket < 120 else WarningSeverity.HIGH
            key = f"{WarningType.LONG_IN_BUCKET.value}:{flower.id}"
            active_keys.add(key)
            store_ref = flower.store if isinstance(flower.store, Store) else None
            bucket_ref = flower.bucket if isinstance(flower.bucket, Bucket) else None
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.LONG_IN_BUCKET,
                Warning.flower.id == flower.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.LONG_IN_BUCKET,
                    warning_type_label="入桶时间过长",
                    severity=severity,
                    store=store_ref,
                    bucket=bucket_ref,
                    flower=flower,
                    message=f"花材 {flower.flower_name} 已入桶 {hours_in_bucket:.1f} 小时，超过建议时长",
                    current_value=str(round(hours_in_bucket, 1)),
                    threshold_value=str(IN_BUCKET_WARNING_HOURS),
                    unit="小时",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()
            else:
                existing.severity = severity
                existing.current_value = str(round(hours_in_bucket, 1))
                existing.message = f"花材 {flower.flower_name} 已入桶 {hours_in_bucket:.1f} 小时，超过建议时长"
                existing.updated_at = now
                await existing.save()

    # 高损耗预警（基于损耗率）
    for store in stores:
        loss_records = await LossRecord.find(LossRecord.store.id == store.id).to_list()
        recent_7d = [r for r in loss_records if (now - r.created_at).days <= 7]
        recent_loss_qty = sum(r.quantity for r in recent_7d)

        store_flowers = await Flower.find(Flower.store.id == store.id).to_list()
        current_qty = sum(f.current_quantity for f in store_flowers)

        base_total = current_qty + recent_loss_qty
        if base_total <= 0:
            continue
        loss_rate = recent_loss_qty / base_total

        if loss_rate >= MEDIUM_LOSS_RATE_THRESHOLD:
            severity = WarningSeverity.HIGH if loss_rate >= HIGH_LOSS_RATE_THRESHOLD else WarningSeverity.MEDIUM
            key = f"{WarningType.HIGH_LOSS.value}:{store.id}"
            active_keys.add(key)
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.HIGH_LOSS,
                Warning.store.id == store.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.HIGH_LOSS,
                    warning_type_label="损耗过高",
                    severity=severity,
                    store=store,
                    bucket=None,
                    flower=None,
                    message=f"门店 {store.store_name} 近7天损耗率 {loss_rate*100:.1f}%（损耗{recent_loss_qty}枝 / 总库存{base_total}枝），超过阈值",
                    current_value=str(round(loss_rate * 100, 1)),
                    threshold_value=str(round(MEDIUM_LOSS_RATE_THRESHOLD * 100, 1)),
                    unit="%",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()
            else:
                existing.severity = severity
                existing.current_value = str(round(loss_rate * 100, 1))
                existing.message = f"门店 {store.store_name} 近7天损耗率 {loss_rate*100:.1f}%（损耗{recent_loss_qty}枝 / 总库存{base_total}枝），超过阈值"
                existing.updated_at = now
                await existing.save()


@router.get("/warnings")
async def get_warnings(
    current_user: User = Depends(get_current_active_user),
    store_id: Optional[str] = Query(None),
    warning_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    await sync_generated_warnings(current_user)

    query = {}
    if status:
        query["status"] = WarningStatus(status)
    else:
        query["status"] = {"$in": [WarningStatus.PENDING, WarningStatus.HANDLING]}

    warnings = await Warning.find(query, fetch_links=True).sort("-severity", "-created_at").to_list()

    result = []
    for w in warnings:
        w_data = warning_to_response(w)
        if store_id and w_data["store_id"] != store_id:
            continue
        if warning_type and w_data["warning_type"] != warning_type:
            continue
        result.append(w_data)

    return result


@router.post("/warnings/handle")
async def handle_warning(
    req: WarningHandleRequest,
    current_user: User = Depends(get_current_active_user),
):
    w = await Warning.get(ObjectId(req.warning_id), fetch_links=True)
    if not w:
        raise HTTPException(status_code=404, detail="预警不存在")

    w.status = req.status
    w.handler = current_user
    w.handle_note = req.note
    w.handled_at = datetime.utcnow()
    w.updated_at = datetime.utcnow()
    await w.save()
    await w.fetch_all_links()

    store = w.store if isinstance(w.store, Store) else None
    bucket = w.bucket if isinstance(w.bucket, Bucket) else None
    flower = w.flower if isinstance(w.flower, Flower) else None
    status_label = {
        WarningStatus.PENDING: "待处理",
        WarningStatus.HANDLING: "处理中",
        WarningStatus.RESOLVED: "已解决",
    }.get(req.status, req.status.value)

    flower_batch = flower.batch_no if flower and hasattr(flower, 'batch_no') else None
    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.WARNING,
        target_id=str(w.id),
        batch_no=flower_batch,
        action=ResponsibilityAction.WARNING_HANDLE,
        user=current_user,
        remark=f"更新预警状态为{status_label}，备注：{req.note or '无'}",
        store=store,
        bucket=bucket,
        flower=flower,
        warning=w,
    )
    if bucket:
        await add_responsibility_trace(
            target_type=ResponsibilityTargetType.BUCKET,
            target_id=str(bucket.id),
            batch_no=flower_batch,
            action=ResponsibilityAction.WARNING_HANDLE,
            user=current_user,
            remark=f"处理预警[{w.warning_type_label}]，状态：{status_label}",
            store=store,
            bucket=bucket,
            flower=flower,
            warning=w,
        )
    if flower:
        await add_responsibility_trace(
            target_type=ResponsibilityTargetType.FLOWER,
            target_id=str(flower.id),
            batch_no=flower_batch,
            action=ResponsibilityAction.WARNING_HANDLE,
            user=current_user,
            remark=f"处理预警[{w.warning_type_label}]，状态：{status_label}",
            store=store,
            bucket=bucket,
            flower=flower,
            warning=w,
        )

    return warning_to_response(w)


@router.get("/operation-trace")
async def get_operation_trace(
    current_user: User = Depends(get_current_active_user),
    store_id: Optional[str] = Query(None),
    bucket_id: Optional[str] = Query(None),
    flower_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    query_conditions = {}
    date_query = {}
    if start_date:
        date_query["$gte"] = datetime.fromisoformat(start_date)
    if end_date:
        date_query["$lte"] = datetime.fromisoformat(end_date) + timedelta(days=1)

    if date_query:
        query_conditions["created_at"] = date_query

    in_query = dict(query_conditions)
    out_query = dict(query_conditions)
    pres_query = dict(query_conditions)
    loss_query = dict(query_conditions)
    status_query = dict(query_conditions)

    if bucket_id:
        in_query["bucket"] = ObjectId(bucket_id)
        out_query["bucket"] = ObjectId(bucket_id)
        pres_query["bucket"] = ObjectId(bucket_id)
        status_query["bucket"] = ObjectId(bucket_id)
    if flower_id:
        in_query["flower"] = ObjectId(flower_id)
        out_query["flower"] = ObjectId(flower_id)
        loss_query["flower"] = ObjectId(flower_id)
        status_query["flower"] = ObjectId(flower_id)
    if store_id:
        pres_query["store"] = ObjectId(store_id)
        loss_query["store"] = ObjectId(store_id)
        status_query["store"] = ObjectId(store_id)

    in_records = await BucketInRecord.find(in_query, fetch_links=True).sort("-created_at").to_list()
    out_records = await BucketOutRecord.find(out_query, fetch_links=True).sort("-created_at").to_list()
    pres_records = await PreservationRecord.find(pres_query, fetch_links=True).sort("-created_at").to_list()
    loss_records = await LossRecord.find(loss_query, fetch_links=True).sort("-created_at").to_list()
    status_records = await StatusChangeRecord.find(status_query, fetch_links=True).sort("-created_at").to_list()

    all_traces = []

    for r in in_records:
        store_info = ""
        store_id_val = ""
        if isinstance(r.bucket, Bucket) and isinstance(r.bucket.store, Store):
            store_info = r.bucket.store.store_name
            store_id_val = str(r.bucket.store.id)
        all_traces.append({
            "trace_id": f"in_{r.id}",
            "operation_type": "in_bucket",
            "operation_type_label": "入桶",
            "store_name": store_info,
            "store_id": store_id_val,
            "bucket_id": str(r.bucket.id) if isinstance(r.bucket, Bucket) else str(r.bucket),
            "bucket_code": r.bucket.bucket_code if isinstance(r.bucket, Bucket) else "",
            "flower_id": str(r.flower.id) if isinstance(r.flower, Flower) else str(r.flower),
            "flower_name": r.flower.flower_name if isinstance(r.flower, Flower) else "",
            "flower_code": r.flower.flower_code if isinstance(r.flower, Flower) else "",
            "quantity": r.quantity,
            "quantity_unit": "枝",
            "operator": r.operator or "",
            "remark": r.remark or "",
            "detail": f"入桶 {r.quantity} 枝",
            "created_at": r.created_at,
        })

    for r in out_records:
        store_info = ""
        store_id_val = ""
        if isinstance(r.bucket, Bucket) and isinstance(r.bucket.store, Store):
            store_info = r.bucket.store.store_name
            store_id_val = str(r.bucket.store.id)
        all_traces.append({
            "trace_id": f"out_{r.id}",
            "operation_type": "out_bucket",
            "operation_type_label": "回桶",
            "store_name": store_info,
            "store_id": store_id_val,
            "bucket_id": str(r.bucket.id) if isinstance(r.bucket, Bucket) else str(r.bucket),
            "bucket_code": r.bucket.bucket_code if isinstance(r.bucket, Bucket) else "",
            "flower_id": str(r.flower.id) if isinstance(r.flower, Flower) else str(r.flower),
            "flower_name": r.flower.flower_name if isinstance(r.flower, Flower) else "",
            "flower_code": r.flower.flower_code if isinstance(r.flower, Flower) else "",
            "quantity": r.quantity,
            "quantity_unit": "枝",
            "operator": r.operator or "",
            "remark": r.remark or "",
            "detail": f"回桶 {r.quantity} 枝",
            "created_at": r.created_at,
        })

    for r in pres_records:
        all_traces.append({
            "trace_id": f"pres_{r.id}",
            "operation_type": "preservation",
            "operation_type_label": "补液",
            "store_name": r.store.store_name if isinstance(r.store, Store) else "",
            "store_id": str(r.store.id) if isinstance(r.store, Store) else "",
            "bucket_id": str(r.bucket.id) if isinstance(r.bucket, Bucket) else str(r.bucket),
            "bucket_code": r.bucket.bucket_code if isinstance(r.bucket, Bucket) else "",
            "flower_id": "",
            "flower_name": "",
            "flower_code": "",
            "quantity": r.supplement_quantity,
            "quantity_unit": "L",
            "operator": r.operator or "",
            "remark": r.remark or "",
            "detail": f"补充保鲜液 {r.supplement_quantity}L（{r.previous_quantity}L → {r.after_quantity}L）",
            "created_at": r.created_at,
        })

    for r in loss_records:
        all_traces.append({
            "trace_id": f"loss_{r.id}",
            "operation_type": "loss",
            "operation_type_label": "损耗",
            "store_name": r.store.store_name if isinstance(r.store, Store) else "",
            "store_id": str(r.store.id) if isinstance(r.store, Store) else "",
            "bucket_id": "",
            "bucket_code": "",
            "flower_id": str(r.flower.id) if isinstance(r.flower, Flower) else str(r.flower),
            "flower_name": r.flower.flower_name if isinstance(r.flower, Flower) else "",
            "flower_code": r.flower.flower_code if isinstance(r.flower, Flower) else "",
            "quantity": r.quantity,
            "quantity_unit": "枝",
            "operator": r.operator or "",
            "remark": r.remark or "",
            "detail": f"损耗 {r.quantity} 枝，原因：{r.reason or '未说明'}",
            "created_at": r.created_at,
        })

    STATUS_TYPE_LABEL = {
        StatusChangeTarget.BUCKET_STATUS: "花桶状态变更",
        StatusChangeTarget.FLOWER_PRESERVATION: "花材保鲜状态变更",
        StatusChangeTarget.FLOWER_BUCKET: "花材所在花桶变更",
    }

    for r in status_records:
        store_name = r.store.store_name if isinstance(r.store, Store) else ""
        store_id_val = str(r.store.id) if isinstance(r.store, Store) else ""
        bucket_code = r.bucket.bucket_code if isinstance(r.bucket, Bucket) else ""
        bucket_id_val = str(r.bucket.id) if isinstance(r.bucket, Bucket) else ""
        flower_name = r.flower.flower_name if isinstance(r.flower, Flower) else ""
        flower_code = r.flower.flower_code if isinstance(r.flower, Flower) else ""
        flower_id_val = str(r.flower.id) if isinstance(r.flower, Flower) else ""

        op_label = STATUS_TYPE_LABEL.get(r.target_type, "状态变更")
        detail = f"{op_label}：{r.old_label or '-'} → {r.new_label}"

        all_traces.append({
            "trace_id": f"status_{r.id}",
            "operation_type": "status_change",
            "operation_type_label": "状态变更",
            "store_name": store_name,
            "store_id": store_id_val,
            "bucket_id": bucket_id_val,
            "bucket_code": bucket_code,
            "flower_id": flower_id_val,
            "flower_name": flower_name,
            "flower_code": flower_code,
            "quantity": 0,
            "quantity_unit": "",
            "operator": r.operator_name or "",
            "remark": r.remark or "",
            "detail": detail,
            "created_at": r.created_at,
        })

    all_traces.sort(key=lambda x: x["created_at"], reverse=True)

    if store_id:
        all_traces = [t for t in all_traces if t["store_id"] == store_id]
    if bucket_id:
        all_traces = [t for t in all_traces if t["bucket_id"] == bucket_id]
    if flower_id:
        all_traces = [t for t in all_traces if t["flower_id"] == flower_id]

    total = len(all_traces)
    total_pages = (total + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    paginated_items = all_traces[start_idx:start_idx + page_size]

    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
