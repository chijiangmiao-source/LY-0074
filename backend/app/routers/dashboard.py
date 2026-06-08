from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from bson import ObjectId
from app.models import (
    User,
    Bucket,
    BucketStatus,
    Flower,
    Store,
    FlowerCategory,
    BucketInRecord,
    BucketOutRecord,
    PreservationRecord,
    LossRecord,
)
from app.services.auth import get_current_active_user

router = APIRouter()


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
