from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId

from app.models import (
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
    StatusChangeRecord,
    StatusChangeTarget,
)
from app.services.stats_service import build_date_query, calculate_store_loss_rate


async def get_dashboard_summary() -> Dict[str, Any]:
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


async def get_bucket_turnover() -> List[Dict[str, Any]]:
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


async def get_flower_category_distribution() -> List[Dict[str, Any]]:
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


async def get_store_loss_ranking() -> List[Dict[str, Any]]:
    stores = await Store.find(Store.is_active == True).to_list()
    result = []

    for store in stores:
        loss_records = await LossRecord.find(LossRecord.store.id == store.id).to_list()
        total_loss_qty = sum(r.quantity for r in loss_records)
        total_loss_count = len(loss_records)

        store_flowers = await Flower.find(Flower.store.id == store.id).to_list()
        flower_qty = sum(f.current_quantity for f in store_flowers)

        loss_rate, recent_loss_qty, _ = calculate_store_loss_rate(
            loss_records, flower_qty, days=7
        )

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


def _fmt_in_record(r: BucketInRecord) -> Dict[str, Any]:
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


def _fmt_out_record(r: BucketOutRecord) -> Dict[str, Any]:
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


def _fmt_preservation_record(r: PreservationRecord) -> Dict[str, Any]:
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


def _fmt_loss_record(r: LossRecord) -> Dict[str, Any]:
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


async def get_recent_records(limit: int = 10) -> List[Dict[str, Any]]:
    in_records = await BucketInRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()
    out_records = await BucketOutRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()
    preservation_records = await PreservationRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()
    loss_records = await LossRecord.find(fetch_links=True).sort("-created_at").limit(limit).to_list()

    all_records = (
        [_fmt_in_record(r) for r in in_records]
        + [_fmt_out_record(r) for r in out_records]
        + [_fmt_preservation_record(r) for r in preservation_records]
        + [_fmt_loss_record(r) for r in loss_records]
    )
    all_records.sort(key=lambda x: x["created_at"], reverse=True)
    return all_records[:limit]


async def get_operation_trace(
    store_id: Optional[str] = None,
    bucket_id: Optional[str] = None,
    flower_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Dict[str, Any]:
    query_conditions = {}
    date_query = build_date_query(start_date, end_date)
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

    all_traces: List[Dict[str, Any]] = []

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
