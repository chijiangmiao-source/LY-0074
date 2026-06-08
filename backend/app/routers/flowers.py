from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from bson import ObjectId
from app.models import (
    Flower,
    PreservationStatus,
    FlowerCategory,
    Bucket,
    Store,
    User,
    StatusChangeRecord,
    StatusChangeTarget,
)
from app.schemas.flower import (
    FlowerCreate,
    FlowerUpdate,
    FlowerResponse,
    CategoryInfo,
    BucketInfo,
    StoreInfo,
)
from app.schemas.common import PaginatedResponse
from app.services.auth import get_current_active_user

router = APIRouter()

PRESERVATION_STATUS_LABEL = {
    PreservationStatus.FRESH: "新鲜",
    PreservationStatus.NORMAL: "一般",
    PreservationStatus.WILTED: "萎蔫",
}


async def create_flower_status_change_record(
    target_type: StatusChangeTarget,
    target_id: str,
    old_status: Optional[str],
    new_status: str,
    old_label: Optional[str],
    new_label: str,
    current_user: User,
    store: Optional[Store] = None,
    bucket: Optional[Bucket] = None,
    flower: Optional[Flower] = None,
    remark: Optional[str] = None,
):
    record = StatusChangeRecord(
        target_type=target_type,
        target_id=target_id,
        store=store,
        bucket=bucket,
        flower=flower,
        old_status=old_status,
        new_status=new_status,
        old_label=old_label,
        new_label=new_label,
        operator=current_user,
        operator_name=current_user.full_name or current_user.username,
        remark=remark,
    )
    await record.create()


def flower_to_response(flower: Flower) -> dict:
    data = flower.model_dump(by_alias=True)
    data["_id"] = str(flower.id)
    if isinstance(flower.category, FlowerCategory):
        data["category"] = {
            "id": str(flower.category.id),
            "category_name": flower.category.category_name,
            "category_code": flower.category.category_code,
        }
    else:
        data["category"] = {"id": str(flower.category), "category_name": "", "category_code": ""}

    if isinstance(flower.bucket, Bucket):
        data["bucket"] = {"id": str(flower.bucket.id), "bucket_code": flower.bucket.bucket_code}
    elif flower.bucket:
        data["bucket"] = {"id": str(flower.bucket), "bucket_code": ""}
    else:
        data["bucket"] = None

    if isinstance(flower.store, Store):
        data["store"] = {"id": str(flower.store.id), "store_name": flower.store.store_name}
    elif flower.store:
        data["store"] = {"id": str(flower.store), "store_name": ""}
    else:
        data["store"] = None

    return data


@router.post("", response_model=FlowerResponse)
async def create_flower(
    flower_in: FlowerCreate,
    current_user: User = Depends(get_current_active_user),
):
    existing = await Flower.find_one(Flower.flower_code == flower_in.flower_code)
    if existing:
        raise HTTPException(status_code=400, detail="花材编号已存在")

    category = await FlowerCategory.get(ObjectId(flower_in.category_id))
    if not category:
        raise HTTPException(status_code=404, detail="花材分类不存在")

    bucket = None
    if flower_in.bucket_id:
        bucket = await Bucket.get(ObjectId(flower_in.bucket_id))
        if not bucket:
            raise HTTPException(status_code=404, detail="花桶不存在")

    store = None
    if flower_in.store_id:
        store = await Store.get(ObjectId(flower_in.store_id))
        if not store:
            raise HTTPException(status_code=404, detail="门店不存在")

    flower = Flower(
        flower_code=flower_in.flower_code,
        flower_name=flower_in.flower_name,
        category=category,
        batch_no=flower_in.batch_no,
        bucket=bucket,
        store=store,
        current_quantity=flower_in.current_quantity,
        preservation_status=flower_in.preservation_status,
        in_bucket_date=flower_in.in_bucket_date,
        remark=flower_in.remark,
    )
    await flower.create()
    return flower_to_response(flower)


@router.get("", response_model=PaginatedResponse)
async def list_flowers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    category_id: Optional[str] = None,
    bucket_id: Optional[str] = None,
    store_id: Optional[str] = None,
    preservation_status: Optional[PreservationStatus] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if keyword:
        query["$or"] = [
            {"flower_code": {"$regex": keyword, "$options": "i"}},
            {"flower_name": {"$regex": keyword, "$options": "i"}},
        ]
    if category_id:
        query["category"] = ObjectId(category_id)
    if bucket_id:
        query["bucket"] = ObjectId(bucket_id)
    if store_id:
        query["store"] = ObjectId(store_id)
    if preservation_status:
        query["preservation_status"] = preservation_status

    total = await Flower.find(query).count()
    flowers = (
        await Flower.find(query, fetch_links=True)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    items = [flower_to_response(f) for f in flowers]
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/all", response_model=List[FlowerResponse])
async def list_all_flowers(
    store_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if store_id:
        query["store"] = ObjectId(store_id)

    flowers = await Flower.find(query, fetch_links=True).sort("flower_code").to_list()
    return [flower_to_response(f) for f in flowers]


@router.get("/{flower_id}", response_model=FlowerResponse)
async def get_flower(
    flower_id: str,
    current_user: User = Depends(get_current_active_user),
):
    flower = await Flower.get(ObjectId(flower_id), fetch_links=True)
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    return flower_to_response(flower)


@router.put("/{flower_id}", response_model=FlowerResponse)
async def update_flower(
    flower_id: str,
    flower_in: FlowerUpdate,
    current_user: User = Depends(get_current_active_user),
):
    flower = await Flower.get(ObjectId(flower_id))
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")

    update_data = flower_in.model_dump(exclude_unset=True)

    old_preservation_status = flower.preservation_status
    old_preservation_label = PRESERVATION_STATUS_LABEL.get(old_preservation_status)
    old_bucket_id = str(flower.bucket.id) if flower.bucket else None

    if "category_id" in update_data:
        category = await FlowerCategory.get(ObjectId(update_data.pop("category_id")))
        if not category:
            raise HTTPException(status_code=404, detail="花材分类不存在")
        flower.category = category

    if "bucket_id" in update_data:
        bucket_id_val = update_data.pop("bucket_id")
        if bucket_id_val:
            bucket = await Bucket.get(ObjectId(bucket_id_val))
            if not bucket:
                raise HTTPException(status_code=404, detail="花桶不存在")
            flower.bucket = bucket
        else:
            flower.bucket = None

    if "store_id" in update_data:
        store_id_val = update_data.pop("store_id")
        if store_id_val:
            store = await Store.get(ObjectId(store_id_val))
            if not store:
                raise HTTPException(status_code=404, detail="门店不存在")
            flower.store = store
        else:
            flower.store = None

    for key, value in update_data.items():
        setattr(flower, key, value)
    flower.updated_at = datetime.utcnow()
    await flower.save()
    await flower.fetch_all_links()

    if "preservation_status" in update_data and old_preservation_status != flower.preservation_status:
        store_ref = flower.store if isinstance(flower.store, Store) else None
        bucket_ref = flower.bucket if isinstance(flower.bucket, Bucket) else None
        await create_flower_status_change_record(
            target_type=StatusChangeTarget.FLOWER_PRESERVATION,
            target_id=str(flower.id),
            old_status=old_preservation_status.value,
            new_status=flower.preservation_status.value,
            old_label=old_preservation_label,
            new_label=PRESERVATION_STATUS_LABEL.get(flower.preservation_status),
            current_user=current_user,
            store=store_ref,
            bucket=bucket_ref,
            flower=flower,
        )

    new_bucket_id = str(flower.bucket.id) if flower.bucket else None
    if old_bucket_id != new_bucket_id:
        store_ref = flower.store if isinstance(flower.store, Store) else None
        bucket_ref = flower.bucket if isinstance(flower.bucket, Bucket) else None
        old_bucket_code = ""
        new_bucket_code = bucket_ref.bucket_code if bucket_ref else "无"
        if old_bucket_id:
            old_bucket = await Bucket.get(ObjectId(old_bucket_id))
            if old_bucket:
                old_bucket_code = old_bucket.bucket_code
        await create_flower_status_change_record(
            target_type=StatusChangeTarget.FLOWER_BUCKET,
            target_id=str(flower.id),
            old_status=old_bucket_id or "none",
            new_status=new_bucket_id or "none",
            old_label=old_bucket_code or "无",
            new_label=new_bucket_code,
            current_user=current_user,
            store=store_ref,
            bucket=bucket_ref,
            flower=flower,
        )

    return flower_to_response(flower)


@router.delete("/{flower_id}")
async def delete_flower(
    flower_id: str,
    current_user: User = Depends(get_current_active_user),
):
    flower = await Flower.get(ObjectId(flower_id))
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    await flower.delete()
    return {"message": "删除成功"}
