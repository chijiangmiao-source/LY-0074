from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from bson import ObjectId
from beanie.odm.fields import PydanticObjectId
from app.models import Bucket, BucketStatus, Store, User
from app.schemas.bucket import BucketCreate, BucketUpdate, BucketResponse, BucketStoreInfo
from app.schemas.common import PaginatedResponse
from app.services.auth import get_current_active_user

router = APIRouter()


def bucket_to_response(bucket: Bucket) -> dict:
    data = bucket.model_dump(by_alias=True)
    data["_id"] = str(bucket.id)
    if isinstance(bucket.store, Store):
        data["store"] = {
            "id": str(bucket.store.id),
            "store_name": bucket.store.store_name,
            "store_code": bucket.store.store_code,
        }
    elif isinstance(bucket.store, (ObjectId, PydanticObjectId)):
        data["store"] = {"id": str(bucket.store), "store_name": "", "store_code": ""}
    return data


@router.post("", response_model=BucketResponse)
async def create_bucket(
    bucket_in: BucketCreate,
    current_user: User = Depends(get_current_active_user),
):
    existing = await Bucket.find_one(Bucket.bucket_code == bucket_in.bucket_code)
    if existing:
        raise HTTPException(status_code=400, detail="桶编号已存在")

    store = await Store.get(ObjectId(bucket_in.store_id))
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")

    if bucket_in.current_quantity > bucket_in.capacity:
        raise HTTPException(status_code=400, detail="桶体当前数量不能超过容量")

    bucket = Bucket(
        bucket_code=bucket_in.bucket_code,
        store=store,
        capacity=bucket_in.capacity,
        current_quantity=bucket_in.current_quantity,
        status=bucket_in.status,
        responsible_person=bucket_in.responsible_person,
        remark=bucket_in.remark,
    )
    await bucket.create()
    await bucket.fetch_link(Bucket.store)
    return bucket_to_response(bucket)


@router.get("", response_model=PaginatedResponse)
async def list_buckets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    store_id: Optional[str] = None,
    status: Optional[BucketStatus] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if keyword:
        query["$or"] = [
            {"bucket_code": {"$regex": keyword, "$options": "i"}},
            {"responsible_person": {"$regex": keyword, "$options": "i"}},
        ]
    if store_id:
        query["store"] = ObjectId(store_id)
    if status:
        query["status"] = status

    total = await Bucket.find(query).count()
    buckets = (
        await Bucket.find(query, fetch_links=True)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    items = [bucket_to_response(b) for b in buckets]
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/all", response_model=List[BucketResponse])
async def list_all_buckets(
    store_id: Optional[str] = None,
    status: Optional[BucketStatus] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if store_id:
        query["store"] = ObjectId(store_id)
    if status:
        query["status"] = status
    else:
        query["status"] = BucketStatus.ACTIVE

    buckets = (
        await Bucket.find(query, fetch_links=True).sort("bucket_code").to_list()
    )
    return [bucket_to_response(b) for b in buckets]


@router.get("/{bucket_id}", response_model=BucketResponse)
async def get_bucket(
    bucket_id: str,
    current_user: User = Depends(get_current_active_user),
):
    bucket = await Bucket.get(ObjectId(bucket_id), fetch_links=True)
    if not bucket:
        raise HTTPException(status_code=404, detail="花桶不存在")
    return bucket_to_response(bucket)


@router.put("/{bucket_id}", response_model=BucketResponse)
async def update_bucket(
    bucket_id: str,
    bucket_in: BucketUpdate,
    current_user: User = Depends(get_current_active_user),
):
    bucket = await Bucket.get(ObjectId(bucket_id))
    if not bucket:
        raise HTTPException(status_code=404, detail="花桶不存在")

    update_data = bucket_in.model_dump(exclude_unset=True)

    if "store_id" in update_data:
        store = await Store.get(ObjectId(update_data.pop("store_id")))
        if not store:
            raise HTTPException(status_code=404, detail="门店不存在")
        bucket.store = store

    new_capacity = update_data.get("capacity", bucket.capacity)
    new_quantity = update_data.get("current_quantity", bucket.current_quantity)
    if new_quantity > new_capacity:
        raise HTTPException(status_code=400, detail="桶体当前数量不能超过容量")

    for key, value in update_data.items():
        setattr(bucket, key, value)
    bucket.updated_at = datetime.utcnow()
    await bucket.save()
    await bucket.fetch_link(Bucket.store)
    return bucket_to_response(bucket)


@router.delete("/{bucket_id}")
async def delete_bucket(
    bucket_id: str,
    current_user: User = Depends(get_current_active_user),
):
    bucket = await Bucket.get(ObjectId(bucket_id))
    if not bucket:
        raise HTTPException(status_code=404, detail="花桶不存在")
    await bucket.delete()
    return {"message": "删除成功"}
