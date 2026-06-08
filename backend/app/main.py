from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth, stores, buckets, flowers, categories, records, dashboard, performance, training


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="连锁花店花桶周转与保鲜液补充管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": settings.APP_NAME, "version": "1.0.0"}


app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(stores.router, prefix="/api/stores", tags=["门店管理"])
app.include_router(categories.router, prefix="/api/categories", tags=["花材分类"])
app.include_router(buckets.router, prefix="/api/buckets", tags=["花桶档案"])
app.include_router(flowers.router, prefix="/api/flowers", tags=["花材管理"])
app.include_router(records.router, prefix="/api/records", tags=["业务记录"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["数据看板"])
app.include_router(performance.router, prefix="/api/performance", tags=["员工绩效与责任追踪"])
app.include_router(training.router, prefix="/api/training", tags=["培训与能力改进"])
