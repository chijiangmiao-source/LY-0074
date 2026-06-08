from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from bson import ObjectId
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
)
from app.services.auth import get_current_active_user

router = APIRouter()

LOW_LIQUID_THRESHOLD = 0.3
IN_BUCKET_WARNING_HOURS = 72
HIGH_LOSS_THRESHOLD = 10


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

    for store in stores:
        loss_records = await LossRecord.find(LossRecord.store.id == store.id).to_list()
        total_loss_qty = sum(r.quantity for r in loss_records)
        total_loss_count = len(loss_records)

        flower_qty = 0
        flowers = await Flower.find(Flower.store.id == store.id).to_list()
        for f in flowers:
            flower_qty += f.current_quantity

        result.append({
            "store_id": str(store.id),
            "store_code": store.store_code,
            "store_name": store.store_name,
            "manager": store.manager,
            "total_loss_quantity": total_loss_qty,
            "total_loss_count": total_loss_count,
            "current_flower_quantity": flower_qty,
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


@router.get("/warnings")
async def get_warnings(
    current_user: User = Depends(get_current_active_user),
    store_id: Optional[str] = Query(None),
    warning_type: Optional[str] = Query(None),
    only_pending: bool = Query(True),
):
    warnings = []
    now = datetime.utcnow()

    buckets = await Bucket.find(fetch_links=True).to_list()
    flowers = await Flower.find(fetch_links=True).to_list()
    stores = await Store.find_all().to_list()
    store_map = {str(s.id): s for s in stores}

    for bucket in buckets:
        if store_id and bucket.store:
            bucket_store_id = str(bucket.store.id) if isinstance(bucket.store, Store) else str(bucket.store)
            if bucket_store_id != store_id:
                continue

        if bucket.capacity > 0:
            liquid_ratio = bucket.current_quantity / bucket.capacity
            if liquid_ratio < LOW_LIQUID_THRESHOLD:
                store_name = ""
                if isinstance(bucket.store, Store):
                    store_name = bucket.store.store_name
                warnings.append({
                    "warning_id": f"liquid_{bucket.id}",
                    "warning_type": "low_liquid",
                    "warning_type_label": "液位过低",
                    "severity": "high" if liquid_ratio < 0.1 else "medium",
                    "store_id": str(bucket.store.id) if isinstance(bucket.store, Store) else str(bucket.store) if bucket.store else None,
                    "store_name": store_name,
                    "bucket_id": str(bucket.id),
                    "bucket_code": bucket.bucket_code,
                    "flower_id": None,
                    "flower_name": None,
                    "flower_code": None,
                    "message": f"花桶 {bucket.bucket_code} 液位仅 {liquid_ratio*100:.1f}%，需要及时补充保鲜液",
                    "current_value": round(bucket.current_quantity, 2),
                    "threshold": round(bucket.capacity * LOW_LIQUID_THRESHOLD, 2),
                    "unit": "L",
                    "created_at": now,
                    "handled": False,
                })

    for flower in flowers:
        if store_id and flower.store:
            flower_store_id = str(flower.store.id) if isinstance(flower.store, Store) else str(flower.store)
            if flower_store_id != store_id:
                continue

        store_name = ""
        if isinstance(flower.store, Store):
            store_name = flower.store.store_name

        bucket_code = ""
        if isinstance(flower.bucket, Bucket):
            bucket_code = flower.bucket.bucket_code

        if flower.preservation_status == PreservationStatus.WILTED:
            warnings.append({
                "warning_id": f"preservation_{flower.id}",
                "warning_type": "wilted",
                "warning_type_label": "花材萎蔫",
                "severity": "high",
                "store_id": str(flower.store.id) if isinstance(flower.store, Store) else str(flower.store) if flower.store else None,
                "store_name": store_name,
                "bucket_id": str(flower.bucket.id) if isinstance(flower.bucket, Bucket) else str(flower.bucket) if flower.bucket else None,
                "bucket_code": bucket_code,
                "flower_id": str(flower.id),
                "flower_name": flower.flower_name,
                "flower_code": flower.flower_code,
                "message": f"花材 {flower.flower_name}({flower.flower_code}) 已萎蔫，需要及时处理",
                "current_value": "wilted",
                "threshold": "fresh/normal",
                "unit": "",
                "created_at": now,
                "handled": False,
            })

        if flower.in_bucket_date:
            hours_in_bucket = (now - flower.in_bucket_date).total_seconds() / 3600
            if hours_in_bucket > IN_BUCKET_WARNING_HOURS:
                warnings.append({
                    "warning_id": f"duration_{flower.id}",
                    "warning_type": "long_in_bucket",
                    "warning_type_label": "入桶时间过长",
                    "severity": "medium" if hours_in_bucket < 120 else "high",
                    "store_id": str(flower.store.id) if isinstance(flower.store, Store) else str(flower.store) if flower.store else None,
                    "store_name": store_name,
                    "bucket_id": str(flower.bucket.id) if isinstance(flower.bucket, Bucket) else str(flower.bucket) if flower.bucket else None,
                    "bucket_code": bucket_code,
                    "flower_id": str(flower.id),
                    "flower_name": flower.flower_name,
                    "flower_code": flower.flower_code,
                    "message": f"花材 {flower.flower_name} 已入桶 {hours_in_bucket:.1f} 小时，超过建议时长",
                    "current_value": round(hours_in_bucket, 1),
                    "threshold": IN_BUCKET_WARNING_HOURS,
                    "unit": "小时",
                    "created_at": now,
                    "handled": False,
                })

    for store in stores:
        if store_id and str(store.id) != store_id:
            continue
        recent_loss = await LossRecord.find(LossRecord.store.id == store.id).to_list()
        recent_7d = [r for r in recent_loss if (now - r.created_at).days <= 7]
        total_loss_qty = sum(r.quantity for r in recent_7d)
        if total_loss_qty >= HIGH_LOSS_THRESHOLD:
            warnings.append({
                "warning_id": f"loss_{store.id}",
                "warning_type": "high_loss",
                "warning_type_label": "损耗过高",
                "severity": "high" if total_loss_qty >= 30 else "medium",
                "store_id": str(store.id),
                "store_name": store.store_name,
                "bucket_id": None,
                "bucket_code": None,
                "flower_id": None,
                "flower_name": None,
                "flower_code": None,
                "message": f"门店 {store.store_name} 近7天损耗 {total_loss_qty} 枝花材，损耗过高",
                "current_value": total_loss_qty,
                "threshold": HIGH_LOSS_THRESHOLD,
                "unit": "枝",
                "created_at": now,
                "handled": False,
            })

    if warning_type:
        warnings = [w for w in warnings if w["warning_type"] == warning_type]

    warnings.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]])

    return warnings


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

    if bucket_id:
        in_query["bucket"] = ObjectId(bucket_id)
        out_query["bucket"] = ObjectId(bucket_id)
        pres_query["bucket"] = ObjectId(bucket_id)
    if flower_id:
        in_query["flower"] = ObjectId(flower_id)
        out_query["flower"] = ObjectId(flower_id)
        loss_query["flower"] = ObjectId(flower_id)
    if store_id:
        pres_query["store"] = ObjectId(store_id)
        loss_query["store"] = ObjectId(store_id)

    in_records = await BucketInRecord.find(in_query, fetch_links=True).sort("-created_at").to_list()
    out_records = await BucketOutRecord.find(out_query, fetch_links=True).sort("-created_at").to_list()
    pres_records = await PreservationRecord.find(pres_query, fetch_links=True).sort("-created_at").to_list()
    loss_records = await LossRecord.find(loss_query, fetch_links=True).sort("-created_at").to_list()

    all_traces = []

    def get_store_name(obj):
        if hasattr(obj, "store") and isinstance(obj.store, Store):
            return obj.store.store_name
        return ""

    def get_store_id(obj):
        if hasattr(obj, "store") and isinstance(obj.store, Store):
            return str(obj.store.id)
        return ""

    for r in in_records:
        store_info = ""
        if isinstance(r.bucket, Bucket) and isinstance(r.bucket.store, Store):
            store_info = r.bucket.store.store_name
        all_traces.append({
            "trace_id": f"in_{r.id}",
            "operation_type": "in_bucket",
            "operation_type_label": "入桶",
            "store_name": store_info,
            "store_id": str(r.bucket.store.id) if isinstance(r.bucket, Bucket) and isinstance(r.bucket.store, Store) else "",
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
        if isinstance(r.bucket, Bucket) and isinstance(r.bucket.store, Store):
            store_info = r.bucket.store.store_name
        all_traces.append({
            "trace_id": f"out_{r.id}",
            "operation_type": "out_bucket",
            "operation_type_label": "回桶",
            "store_name": store_info,
            "store_id": str(r.bucket.store.id) if isinstance(r.bucket, Bucket) and isinstance(r.bucket.store, Store) else "",
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
