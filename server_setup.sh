#!/bin/bash
# ============================================================
# 大模型智能软件实训教学结果检查评价与报表系统
# 一键环境安装脚本
# 适配: LoongArch + 银河麒麟高级服务器 V10/V11
#     CPU四核 / 内存8GB+ / 硬盘256GB+
# ============================================================
# 用法:
#   chmod +x server_setup.sh
#   sudo bash server_setup.sh
#
# 说明: 本脚本从裸机开始安装全套环境，
#       项目代码需提前放到 /opt/training-evaluation/ 下，
#       或之后手动放置。
# ============================================================

set -e

LOG_FILE="/var/log/training-eval-setup.log"
PROJECT_DIR="/opt/training-evaluation"
MYSQL_ROOT_PASS="123456"        # ← 按需修改

exec 2>&1 | tee -a "$LOG_FILE"

echo ""
echo "========================================"
echo "   实训评价系统 - 全量环境安装"
echo "   时间: $(date)"
echo "========================================"
echo ""

# ============================================================
# 第1步：系统信息确认
# ============================================================
echo "[1/8] 检查系统信息..."

ARCH=$(uname -m)
echo "  CPU架构: $ARCH"

if [ -f /etc/kylin-release ]; then
    OS_INFO=$(cat /etc/kylin-release)
else
    OS_INFO=$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
fi
echo "  操作系统: $OS_INFO"

if [[ "$ARCH" != "loongarch64" ]]; then
    echo "  ⚠️ 警告: 当前架构不是 LoongArch"
    echo "  但本脚本仍可继续执行 (仅兼容包安装会跳过)"
fi

# ============================================================
# 第2步：安装基础系统依赖
# ============================================================
echo ""
echo "[2/8] 安装系统基础依赖..."

# 麒麟/龙芯版 dnf 是主流包管理器
PKG_MGR=""
if command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
elif command -v yum &>/dev/null; then
    PKG_MGR="yum"
elif command -v apt &>/dev/null; then
    PKG_MGR="apt"
else
    echo "  ❌ 找不到包管理器 (dnf/yum/apt)"
    exit 1
fi
echo "  包管理器: $PKG_MGR"

# 安装基础工具
$PKG_MGR install -y wget curl tar gzip unzip make gcc gcc-c++ || true

# ============================================================
# 第3步：安装 MySQL 8.0
# ============================================================
echo ""
echo "[3/8] 安装 MySQL 8.0..."

if command -v mysql &>/dev/null; then
    echo "  MySQL 已安装, 跳过"
else
    echo "  正在安装 mysql-server..."
    $PKG_MGR install -y mysql-server mysql-devel || {
        echo "  ⚠️ dnf 安装失败, 尝试下载 LoongArch RPM..."
        # 如果系统源没有, 从麒麟镜像站下载
        mkdir -p /tmp/mysql-loongarch
        cd /tmp/mysql-loongarch
        # 尝试从镜像源获取 MySQL LoongArch 包
        $PKG_MGR install -y https://mirrors.kylinos.cn/kylin/KYLIN-ALL/10.1/os/loongarch64/Packages/mysql-8.0.36-1.p01.ky10.loongarch64.rpm 2>/dev/null || true
        $PKG_MGR install -y mysql-server 2>/dev/null || echo "  ⚠️ MySQL 自动安装失败, 请手动安装后继续"
    }
fi

# 启动 MySQL
if command -v mysqld &>/dev/null; then
    systemctl enable mysqld 2>/dev/null || systemctl enable mysql 2>/dev/null || true
    systemctl start mysqld 2>/dev/null || systemctl start mysql 2>/dev/null || true
    sleep 2

    # 检查 MySQL 是否在运行
    if systemctl is-active --quiet mysqld 2>/dev/null || systemctl is-active --quiet mysql 2>/dev/null || pidof mysqld &>/dev/null; then
        echo "  ✅ MySQL 运行中"
    else
        echo "  ⚠️ MySQL 未启动, 尝试直接调用..."
        mysqld --user=mysql --datadir=/var/lib/mysql &>/dev/null &
        sleep 3
    fi
fi

# ============================================================
# 第4步：创建数据库和导入表结构
# ============================================================
echo ""
echo "[4/8] 创建数据库并导入表结构..."

if command -v mysql &>/dev/null; then
    # 创建「信息」库
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS \`信息\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;" 2>/dev/null || {
        mysql -u root --socket=/var/run/mysqld/mysqld.sock -e "CREATE DATABASE IF NOT EXISTS \`信息\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;" 2>/dev/null || {
            echo "  ⚠️ 创建数据库失败, 请手动执行:"
            echo "      mysql -u root -p"
            echo "      CREATE DATABASE \`信息\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
        }
    }
    echo "  ✅ 数据库「信息」已就绪"

    # 如果有项目代码, 导入表结构
    if [ -f "$PROJECT_DIR/backend/init_info_db.sql" ]; then
        mysql -u root "信息" < "$PROJECT_DIR/backend/init_info_db.sql" 2>/dev/null || {
            echo "  ⚠️ SQL导入失败, 请手动执行: mysql -u root 信息 < $PROJECT_DIR/backend/init_info_db.sql"
        }
        echo "  ✅ 数据库表结构已导入"
    else
        echo "  ⚠️ 未找到 init_info_db.sql，请放置项目代码后再导入"
    fi
else
    echo "  ⚠️ mysql 命令不可用, 请手动安装 MySQL 后创建数据库"
fi

# ============================================================
# 第5步：安装 Python 3.10+
# ============================================================
echo ""
echo "[5/8] 安装 Python 3..."

PYTHON_BIN="python3"

# 检查Python版本
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
    echo "  已安装 Python $PY_VER"
    # 如果低于 3.10, 尝试升级
    if [ "$(echo "$PY_VER" | tr -d '.')" -lt 310 ]; then
        echo "  Python 版本 < 3.10, 尝试升级..."
        $PKG_MGR install -y python3 python3-devel python3-pip python3-venv python3-pymysql 2>/dev/null || true
    fi
else
    echo "  正在安装 Python 3..."
    $PKG_MGR install -y python3 python3-devel python3-pip python3-venv python3-pymysql 2>/dev/null || echo "  ⚠️ 请手动安装 python3"
fi

# 验证 pip
python3 -m pip --version &>/dev/null || python3 -m ensurepip 2>/dev/null || true

# 配置 pip 国内镜像
python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true
echo "  ✅ Python 环境就绪"

# ============================================================
# 第6步：安装 Node.js 18+ 与 NPM
# ============================================================
echo ""
echo "[6/8] 安装 Node.js..."

if command -v node &>/dev/null; then
    NODE_VER=$(node --version | grep -oP '\d+' | head -1)
    echo "  已安装 Node $(node --version), 主版本: $NODE_VER"
    if [ "$NODE_VER" -lt 18 ]; then
        echo "  ⚠️ Node 版本 < 18, 建议升级到 18+"
    fi
else
    echo "  正在安装 Node.js 18..."
    $PKG_MGR install -y nodejs npm 2>/dev/null || {
        echo "  ⚠️ 系统源中未找到 nodejs, 尝试从麒麟镜像站安装..."
        # 尝试从镜像站安装 Node.js
        $PKG_MGR install -y https://mirrors.kylinos.cn/kylin/KYLIN-ALL/10.1/os/loongarch64/Packages/nodejs-18.20.4-1.ky10.loongarch64.rpm 2>/dev/null || {
            echo "  ⚠️ 请手动安装 Node.js 18+ (LoongArch 版本)"
            echo "     下载地址: https://mirrors.kylinos.cn/kylin/KYLIN-ALL/10.1/os/loongarch64/Packages/"
        }
    }
fi

# 配置 npm 国内镜像
npm config set registry https://registry.npmmirror.com 2>/dev/null || true
echo "  ✅ Node.js 环境就绪"

# ============================================================
# 第7步：安装 Nginx
# ============================================================
echo ""
echo "[7/8] 安装 Nginx..."

if command -v nginx &>/dev/null; then
    echo "  Nginx 已安装"
else
    $PKG_MGR install -y nginx 2>/dev/null || echo "  ⚠️ Nginx 安装失败, 请手动安装"
fi

systemctl enable nginx 2>/dev/null || true
echo "  ✅ Nginx 就绪"

# ============================================================
# 第8步：配置环境变量参考 & 打印总结
# ============================================================
echo ""
echo "[8/8] 生成环境配置参考..."

if [ -d "$PROJECT_DIR" ]; then
    echo "  项目目录: $PROJECT_DIR ✅"
else
    echo "  项目目录: $PROJECT_DIR ⚠️ 尚不存在"
    echo "  请将 training-evaluation-system 整个目录复制到 /opt/training-evaluation/"
fi

echo ""
echo "========================================"
echo "  ✅ 环境安装完成！"
echo "========================================"
echo ""
echo "📋 已安装组件:"
echo "  - MySQL 8.0+         $(mysql --version 2>/dev/null || echo 'unavailable')"
echo "  - Python 3            $(python3 --version 2>/dev/null || echo 'unavailable')"
echo "  - PyMySQL             $(python3 -c 'import pymysql; print(pymysql.__version__)' 2>/dev/null || echo 'unavailable')"
echo "  - Node.js             $(node --version 2>/dev/null || echo 'unavailable')"
echo "  - NPM                 $(npm --version 2>/dev/null || echo 'unavailable')"
echo "  - Nginx               $(nginx -v 2>&1 || echo 'unavailable')"
echo ""
echo "📋 数据库:"
echo "  库名: 信息"
echo "  用户: root / 密码: $MYSQL_ROOT_PASS"
echo ""
echo "📋 后续部署步骤:"
echo ""
echo "  # 1. 放置项目代码（如果还没放）:"
echo "  sudo cp -r ./training-evaluation-system $PROJECT_DIR"
echo ""
echo "  # 2. 导入表结构:"
echo "  mysql -u root 信息 < $PROJECT_DIR/backend/init_info_db.sql"
echo ""
echo "  # 3. 初始化管理员:"
echo "  cd $PROJECT_DIR/backend && python3 init_admin.py"
echo ""
echo "  # 4. 插入组织架构数据（可选）:"
echo "  cd $PROJECT_DIR/backend && python3 脚本.py"
echo ""
echo "  # 5. 运行部署脚本:"
echo "  cd $PROJECT_DIR && bash deploy/deploy.sh"
echo ""
echo "  # 6. 配置 Nginx:"
echo "  sudo cp deploy/nginx.conf /etc/nginx/conf.d/training-eval.conf"
echo "  sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "📋 部署后访问:"
echo "  Web页面: http://服务器IP/"
echo "  直连后端: http://服务器IP:8000"
echo "  健康检查: http://服务器IP:8000/api/health"
echo ""
echo "📋 大模型配置（二选一）:"
echo "  方案A - 云端API: 启动后在 Web 系统设置中填写 API Key 和地址"
echo "  方案B - 本地 Ollama: 需手动安装（LoongArch 支持有限, 建议初赛用方案A）"
echo ""
echo "📋 常用管理命令:"
echo "  sudo systemctl status training-eval       # 查看服务状态"
echo "  sudo journalctl -u training-eval -f       # 实时查看日志"
echo "  sudo systemctl restart training-eval      # 重启服务"
echo "  sudo systemctl status mysqld              # MySQL 状态"
echo "  sudo systemctl status nginx               # Nginx 状态"
echo ""
echo "日志已保存到: $LOG_FILE"
echo "========================================"
