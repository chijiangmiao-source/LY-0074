@echo off
cd /d %~dp0
pip install -r requirements.txt
echo.
echo ========================================
echo 后端启动成功！
echo 请访问: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo ========================================
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
