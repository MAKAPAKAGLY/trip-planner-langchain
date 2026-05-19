#!/bin/bash
# ========================================
# 智能旅行助手 — 服务器端一键部署脚本
# 用法: chmod +x quick-deploy.sh && ./quick-deploy.sh
# 前提:
#   1. 已通过 git clone 获取项目代码
#   2. 前端 dist/ 已随代码一起拉取到服务器
#   3. Docker + Docker Compose 已安装
#   4. Ubuntu 20.04/22.04
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  智能旅行助手 — 服务器部署脚本"
echo "=========================================="
echo ""

# 1. 检查 Docker 环境
echo "[1/6] 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   curl -fsSL https://get.docker.com | bash"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 不可用，正在安装..."
    sudo apt update && sudo apt install docker-compose-plugin -y
fi

echo "✅ Docker $(docker --version | awk '{print $3}' | sed 's/,//')"
echo "✅ Docker Compose $(docker compose version --short)"

# 2. 检查前端 dist 目录
echo ""
echo "[2/6] 检查前端构建产物..."
DIST_DIR="$PROJECT_DIR/frontend/dist"
if [ ! -f "$DIST_DIR/index.html" ]; then
    echo "❌ 未找到前端构建产物 ($DIST_DIR/index.html)"
    echo ""
    echo "   请先在本地构建前端并推送："
    echo "   cd frontend && npm run build"
    echo "   git add frontend/dist && git commit && git push"
    echo "   然后在服务器 git pull 后再运行本脚本"
    exit 1
fi
echo "✅ 前端 dist/ 存在"

# 3. 检查 .env 文件
echo ""
echo "[3/6] 检查环境变量配置..."
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo "⚠️  未找到 .env 文件，从模板创建..."
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo "❌ 请编辑 deploy/.env 文件，填入 API 密钥后重新运行"
        echo "   nano $SCRIPT_DIR/.env"
        exit 1
    else
        echo "❌ 未找到 .env.example 模板文件"
        exit 1
    fi
fi

# 检查是否还有占位值
if grep -q "sk-your-key-here\|your-amap-key-here\|your-unsplash-key-here" "$SCRIPT_DIR/.env"; then
    echo "⚠️  .env 中存在未填写的占位值"
    echo "   nano $SCRIPT_DIR/.env"
    echo ""
    read -p "是否仍要继续？（y/N）" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo "✅ 环境变量已配置"

# 4. 检查端口占用
echo ""
echo "[4/6] 检查端口占用..."
PORT80_PID=$(lsof -t -i :80 2>/dev/null || true)
PORT8000_PID=$(lsof -t -i :8000 2>/dev/null || true)

if [ -n "$PORT80_PID" ]; then
    # 检查是否是自己的容器
    if docker ps --format '{{.Names}}' | grep -q "trip-planner-frontend"; then
        echo "⚠️  端口 80 被现有前端容器占用，将先停止旧容器"
        cd "$SCRIPT_DIR" && docker compose down
    else
        echo "❌ 端口 80 被其他进程占用:"
        lsof -i :80
        exit 1
    fi
fi

if [ -n "$PORT8000_PID" ]; then
    if docker ps --format '{{.Names}}' | grep -q "trip-planner-backend"; then
        echo "⚠️  端口 8000 被现有后端容器占用，将先停止旧容器"
        cd "$SCRIPT_DIR" && docker compose down
    else
        echo "❌ 端口 8000 被其他进程占用:"
        lsof -i :8000
        exit 1
    fi
fi
echo "✅ 端口检查通过"

# 5. 构建并启动
echo ""
echo "[5/6] 启动 Docker 服务..."
cd "$SCRIPT_DIR"

# 检查是否需要重新构建后端镜像
if docker images | grep -q "deploy-backend"; then
    echo "检测到已有后端镜像，快速重启..."
    docker compose up -d
else
    echo "首次部署，构建后端镜像（需要几分钟）..."
    docker compose up -d --build
fi

# 6. 验证部署
echo ""
echo "[6/6] 验证部署..."

# 等待后端启动
echo "等待后端就绪..."
HEALTHY=false
for i in $(seq 1 30); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/trip/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        HEALTHY=true
        echo "✅ 后端健康检查通过"
        break
    fi
    sleep 2
done

if [ "$HEALTHY" = false ]; then
    echo "⚠️  后端未在 60 秒内就绪，请手动检查:"
    echo "   docker compose logs backend"
fi

# 检查前端
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 前端页面可访问"
else
    echo "⚠️  前端返回 $HTTP_CODE，请检查 Nginx 配置"
fi

# 7. 显示部署信息
echo ""
echo "=========================================="
echo "  🎉 部署完成！"
echo "=========================================="
echo ""

# 尝试获取公网 IP
PUBLIC_IP=$(curl -s --connect-timeout 3 ifconfig.me 2>/dev/null || echo "你的服务器IP")

echo "访问地址:"
echo "  前端页面:  http://$PUBLIC_IP"
echo "  API 文档:  http://$PUBLIC_IP/api/docs"
echo "  健康检查:  http://$PUBLIC_IP/api/trip/health"
echo ""
echo "运维命令:"
echo "  查看日志:  docker compose -f $SCRIPT_DIR/docker-compose.yml logs -f"
echo "  重启后端:  docker compose -f $SCRIPT_DIR/docker-compose.yml up -d --build backend"
echo "  重启前端:  docker compose -f $SCRIPT_DIR/docker-compose.yml restart frontend"
echo "  停止服务:  docker compose -f $SCRIPT_DIR/docker-compose.yml down"
echo ""
echo "⚠️  提醒："
echo "  1. 确保阿里云安全组已开放 80 端口"
echo "  2. 修改前端代码后：本地 npm run build → git push → 服务器 git pull → docker compose restart frontend"
echo "  3. 修改后端代码后：git push → 服务器 git pull → docker compose up -d --build backend"
echo ""
