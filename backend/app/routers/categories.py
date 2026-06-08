from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from bson import ObjectId
from app.models import FlowerCategory, User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import PaginatedResponse
from app.services.auth import get_current_active_user

router = APIRouter()


@router.post("", response_model=CategoryResponse)
async def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
):
    existing = await FlowerCategory.find_one(
        FlowerCategory.category_code == category_in.category_code
    )
    if existing:
        raise HTTPException(status_code=400, detail="分类编号已存在")
    category = FlowerCategory(**category_in.model_dump())
    await category.create()
    return category


@router.get("", response_model=PaginatedResponse[CategoryResponse])
async def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    query = {}
    if keyword:
        query["$or"] = [
            {"category_code": {"$regex": keyword, "$options": "i"}},
            {"category_name": {"$regex": keyword, "$options": "i"}},
        ]

    total = await FlowerCategory.find(query).count()
    items = (
        await FlowerCategory.find(query)
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


@router.get("/all", response_model=List[CategoryResponse])
async def list_all_categories(
    current_user: User = Depends(get_current_active_user),
):
    items = await FlowerCategory.find_all().sort("category_code").to_list()
    return items


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user: User = Depends(get_current_active_user),
):
    category = await FlowerCategory.get(ObjectId(category_id))
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
):
    category = await FlowerCategory.get(ObjectId(category_id))
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    await category.save()
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_active_user),
):
    category = await FlowerCategory.get(ObjectId(category_id))
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    await category.delete()
    return {"message": "删除成功"}
