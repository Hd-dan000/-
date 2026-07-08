#!/bin/bash
# ============================================
# 大模型智能软件实训评价系统 - 部署脚本
# 适配: LoongArch + 银河麒麟高级服务器V10/V11
# 环境: 四核8G内存256G硬盘
# ============================================

set -e

APP_DIR="/opt/training-evaluation"
PYTHON_BIN="python3"
LOG_FILE="$APP_DIR/deploy.log"
PROJECT_ROOT="$APP_DIR"

echo "========================================" | tee -a $LOG_FILE
echo "  实训评价系统部署脚本" | tee -a $LOG_FILE
echo "  时间: $(date)" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

# 1. 检查系统架构
echo "[1/7] 检查系统架构..." | tee -a $LOG_FILE
ARCH=$(uname -m)
echo "  当前架构: $ARCH" | tee -a $LOG_FILE
if [[ "$ARCH" != "loongarch64" ]]; then
    echo "  警告: 非LoongArch架构，但可继续部署" | tee -a $LOG_FILE
fi

if [ -f /etc/kylin-release ]; then
    echo "  操作系统: $(cat /etc/kylin-release)" | tee -a $LOG_FILE
else
    echo "  操作系统: $(cat /etc/os-release | grep PRETTY_NAME)" | tee -a $LOG_FILE
fi

# 2. 安装系统依赖
echo "[2/7] 安装系统依赖..." | tee -a $LOG_FILE
if command -v dnf &> /dev/null; then
    sudo dnf install -y python3 python3-pip python3-devel python3-venv python3-pymysql gcc nodejs npm 2>&1 | tee -a $LOG_FILE
elif command -v apt &> /dev/null; then
    sudo apt update && sudo apt install -y python3 python3-pip python3-dev python3-venv python3-pymysql gcc nodejs npm 2>&1 | tee -a $LOG_FILE
else
    echo "  请手动安装: python3, python3-pip, python3-venv, python3-pymysql, nodejs, npm, gcc" | tee -a $LOG_FILE
fi

# 3. 创建应用目录
echo "[3/7] 创建应用目录..." | tee -a $LOG_FILE
sudo mkdir -p $APP_DIR
sudo mkdir -p $APP_DIR/backend/uploads
sudo mkdir -p $APP_DIR/backend/reports
sudo mkdir -p $APP_DIR/frontend/dist
sudo mkdir -p $APP_DIR/logs

# 4. 部署前后端依赖
echo "[4/7] 部署后端服务..." | tee -a $LOG_FILE
cd $APP_DIR

if [ ! -d "venv" ]; then
    $PYTHON_BIN -m venv venv
fi
source venv/bin/activate

echo "  安装Python依赖..." | tee -a $LOG_FILE
if ! $PYTHON_BIN -c "import pymysql" >/dev/null 2>&1; then
    pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>&1 | tee -a $LOG_FILE
else
    echo "  已检测到系统包版 PyMySQL，跳过 pip 安装第三方 Python 依赖" | tee -a $LOG_FILE
fi

echo "  安装前端依赖..." | tee -a $LOG_FILE
cd $APP_DIR/frontend
npm install --registry=https://registry.npmmirror.com 2>&1 | tee -a $LOG_FILE

echo "  构建前端静态资源..." | tee -a $LOG_FILE
npm run build 2>&1 | tee -a $LOG_FILE
cd $APP_DIR

# 5. 创建systemd服务
echo "[5/7] 配置systemd服务..." | tee -a $LOG_FILE
sudo tee /etc/systemd/system/training-eval.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=大模型智能软件实训评价系统
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/training-evaluation/backend
Environment="PATH=/opt/training-evaluation/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="LLM_PROVIDER=ollama"
Environment="OLLAMA_HOST=http://localhost:11434"
Environment="OLLAMA_MODEL=qwen2.5:7b"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/training-evaluation/venv/bin/python /opt/training-evaluation/backend/main.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/training-evaluation/logs/app.log
StandardError=append:/opt/training-evaluation/logs/error.log

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# 6. 配置防火墙
echo "[6/7] 配置防火墙..." | tee -a $LOG_FILE
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=8000/tcp 2>&1 | tee -a $LOG_FILE || true
    sudo firewall-cmd --reload 2>&1 | tee -a $LOG_FILE || true
elif command -v ufw &> /dev/null; then
    sudo ufw allow 8000/tcp 2>&1 | tee -a $LOG_FILE || true
fi

# 7. 启动服务
echo "[7/7] 启动服务..." | tee -a $LOG_FILE
sudo systemctl daemon-reload
sudo systemctl enable training-eval.service
sudo systemctl restart training-eval.service

echo "" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE
echo "  部署完成！" | tee -a $LOG_FILE
echo "  访问地址: http://$(hostname -I | awk '{print $1}'):8000" | tee -a $LOG_FILE
echo "  前端页面: http://$(hostname -I | awk '{print $1}')/" | tee -a $LOG_FILE
echo "  API健康检查: http://$(hostname -I | awk '{print $1}'):8000/api/health" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "常用命令:" | tee -a $LOG_FILE
echo "  查看状态: sudo systemctl status training-eval" | tee -a $LOG_FILE
echo "  查看日志: sudo journalctl -u training-eval -f" | tee -a $LOG_FILE
echo "  重启服务: sudo systemctl restart training-eval" | tee -a $LOG_FILE
echo "  停止服务: sudo systemctl stop training-eval" | tee -a $LOG_FILE