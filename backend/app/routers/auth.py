from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.config import settings
from app.models import User, EmployeePosition, POSITION_LABELS
from app.schemas.common import Token, UserCreate, UserResponse
from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
)

router = APIRouter()


def user_to_response(user: User) -> dict:
    data = user.model_dump(by_alias=True)
    data["_id"] = str(user.id)
    pos_val = user.position.value if isinstance(user.position, EmployeePosition) else user.position
    data["position"] = pos_val
    data["position_label"] = POSITION_LABELS.get(user.position, "") if user.position else ""
    return data


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.username == form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被停用",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return user_to_response(current_user)


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate):
    existing_user = await User.find_one(User.username == user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    try:
        position = EmployeePosition(user_in.position) if user_in.position else EmployeePosition.OTHER
    except ValueError:
        position = EmployeePosition.OTHER
    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        position=position,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        is_admin=user_in.is_admin,
    )
    await user.create()
    return user_to_response(user)


@router.post("/init-admin")
async def init_admin():
    admin = await User.find_one(User.username == "admin")
    if admin:
        raise HTTPException(status_code=400, detail="管理员已存在")
    user = User(
        username="admin",
        full_name="系统管理员",
        position=EmployeePosition.MANAGER,
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_admin=True,
    )
    await user.create()
    return {"message": "管理员初始化成功，默认账号: admin / admin123"}
