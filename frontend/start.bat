@echo off
cd /d %~dp0
echo 正在安装依赖...
call npm install
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查 Node.js 环境
    pause
    exit /b 1
)
echo.
echo ========================================
echo 前端启动成功！
echo 请访问: http://localhost:5175
echo ========================================
echo.
npm run dev
