#!/bin/bash
cd "$(dirname "$0")"
echo "正在安装依赖..."
npm install
echo "========================================"
echo "前端启动成功！"
echo "请访问: http://localhost:5175"
echo "========================================"
npm run dev
