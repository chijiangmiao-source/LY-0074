#!/bin/bash
cd "$(dirname "$0")"
pip install -r requirements.txt
echo "========================================"
echo "后端启动成功！"
echo "请访问: http://localhost:8001"
echo "API文档: http://localhost:8001/docs"
echo "========================================"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
