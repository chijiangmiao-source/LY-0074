# 连锁花店花桶周转与保鲜液补充管理系统

## 项目概述

连锁花店花桶周转与保鲜液补充管理系统，基于前后端分离架构开发。

## 技术栈

**后端**: Python + FastAPI + Beanie + MongoDB
**前端**: Vue3 + TypeScript + Vuetify

## 目录结构

```
cj74/
├── backend/          # 后端项目
│   ├── app/
│   │   ├── models/   # 数据模型
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── routers/  # API 路由
│   │   ├── services/ # 业务服务
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── start.bat     # Windows启动
│   └── start.sh      # Linux/Mac启动
└── frontend/         # 前端项目
    ├── src/
    │   ├── api/      # API 接口封装
    │   ├── layouts/  # 布局组件
    │   ├── router/   # 路由配置
    │   ├── stores/   # Pinia 状态管理
    │   ├── types/    # TypeScript 类型
    │   ├── views/    # 页面视图
    │   └── main.ts
    ├── package.json
    ├── start.bat
    └── start.sh
```

## 核心功能

1. **登录认证** - 基于 JWT 的用户登录认证
2. **门店管理** - 连锁门店信息 CRUD
3. **花桶档案** - 花桶编号、容量、状态、责任人等管理
4. **花材分类** - 花材分类管理
5. **花材管理** - 花材档案管理
6. **入桶登记** - 花材入桶操作记录
7. **回桶登记** - 花材回桶操作记录
8. **保鲜液补充** - 花桶保鲜液补充记录
9. **损耗记录** - 花材损耗登记
10. **筛选查询** - 各模块的多维筛选查询
11. **数据看板** - 花桶周转率、花材分类分布、门店损耗排行

## 约束规则

- 桶编号不能重复
- 花材编号不能重复
- 桶体当前数量不能超过容量
- 停用花桶不能办理入桶
- 补充后液位不能超过桶体容量

## 启动说明

### 环境要求

- Python 3.10+
- Node.js 18+
- MongoDB 5.0+

### 启动后端

```bash
cd backend
# Windows
start.bat
# 或手动
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

后端地址: http://localhost:8000  
API 文档: http://localhost:8000/docs

### 启动前端

```bash
cd frontend
# Windows
start.bat
# 或手动
npm install
npm run dev
```

前端地址: http://localhost:5173

### 初始化管理员

首次使用请先在登录页面点击「初始化管理员账号」，或访问 API:
```
POST http://localhost:8000/api/auth/init-admin
```

默认账号: `admin` / `admin123`
