#!/bin/bash
# ============================================
# 开发环境一键启动脚本
# ============================================

set -e

echo "========================================"
echo "  实训评价系统 - 开发环境启动"
echo "========================================"

# 启动后端
echo "[1/2] 启动后端服务..."
cd "$(dirname "$0")/../backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
    pip install -r requirements.txt

echo "  后端启动: http://localhost:8000"
python main.py &
BACKEND_PID=$!

# 启动前端
echo "[2/2] 启动前端服务..."
cd "$(dirname "$0")/../frontend"
npm install --registry=https://registry.npmmirror.com 2>/dev/null || npm install
echo "  前端启动: http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  系统已启动！"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait