from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from bson import ObjectId
from app.models import Store, User
from app.schemas.store import StoreCreate, StoreUpdate, StoreResponse
from app.schemas.common import PaginatedResponse
from app.services.auth import get_current_active_user

router = APIRouter()


@router.post("", response_model=StoreResponse)
async def create_store(
    store_in: StoreCreate,
    current_user: User = Depends(get_current_active_user),
):
    existing = await Store.find_one(Store.store_code == store_in.store_code)
    if existing:
        raise HTTPException(status_code=400, detail="门店编号已存在")
    store = Store(**store_in.model_dump())
    await store.create()
    return store


@router.get("", response_model=PaginatedResponse[StoreResponse])
async def list_stores(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if keyword:
        query["$or"] = [
            {"store_code": {"$regex": keyword, "$options": "i"}},
            {"store_name": {"$regex": keyword, "$options": "i"}},
        ]
    if is_active is not None:
        query["is_active"] = is_active

    total = await Store.find(query).count()
    items = (
        await Store.find(query)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/all", response_model=List[StoreResponse])
async def list_all_stores(
    current_user: User = Depends(get_current_active_user),
):
    items = await Store.find(Store.is_active == True).sort("store_code").to_list()
    return items


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: str,
    current_user: User = Depends(get_current_active_user),
):
    store = await Store.get(ObjectId(store_id))
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    return store


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: str,
    store_in: StoreUpdate,
    current_user: User = Depends(get_current_active_user),
):
    store = await Store.get(ObjectId(store_id))
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")

    update_data = store_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(store, key, value)
    await store.save()
    return store


@router.delete("/{store_id}")
async def delete_store(
    store_id: str,
    current_user: User = Depends(get_current_active_user),
):
    store = await Store.get(ObjectId(store_id))
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    await store.delete()
    return {"message": "删除成功"}
