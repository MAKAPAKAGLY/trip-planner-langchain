# 阿里云 ECS 部署指南 — 智能旅行助手 (LangChain 版)

本文档详细说明如何通过 GitHub 将 HelloAgents Trip Planner 项目部署到阿里云 ECS (Ubuntu 22.04) 服务器上。

**部署流程：** 本地构建前端 → 推送代码到 GitHub → 服务器拉取 → Docker Compose 启动。

## 部署架构

```
用户浏览器 (http://公网IP)
       │
       ▼
┌──────────────────┐
│  Nginx (port 80) │  ← Docker 容器: trip-planner-frontend
│  静态文件 + 反向代理 │     dist/ 从宿主机挂载（本地构建产物）
└────────┬─────────┘
         │ /api/* → proxy_pass
         ▼
┌──────────────────┐
│  FastAPI (8000)  │  ← Docker 容器: trip-planner-backend
│  LangChain Agent │     Python 源码 + 依赖打包在镜像中
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
 DeepSeek   高德地图 / Unsplash
  (LLM)     (外部 API)
```

- **前端**：Nginx 直接托管从宿主机挂载的 `frontend/dist/` 静态文件，服务器不需要 Node.js
- **后端**：Docker 镜像内打包 Python + 所有依赖，启动即可运行
- **通信**：两个容器通过 Docker 内部网络通信，Nginx 将 `/api/` 请求代理到后端

## 前置条件

### 本地开发机

- Node.js 16+ / npm 8+（用于构建前端）
- Git（用于推送代码到 GitHub）
- 项目已推送到一个 GitHub 仓库（公开或私有均可）

### 阿里云 ECS 服务器

- Ubuntu 20.04 或 22.04，建议 2 核 4GB 及以上
- Docker 20.10+ + Docker Compose v2
- 安全组已开放 80 端口（HTTP）和 22 端口（SSH）
- Git 已安装（用于从 GitHub 拉取代码）

### API 密钥

| 服务 | 获取地址 | 用途 |
|------|---------|------|
| DeepSeek (或 OpenAI) | platform.deepseek.com | 驱动 AI Agent 推理 |
| 高德地图 | console.amap.com | 景点搜索与地图展示 |
| Unsplash | unsplash.com/developers | 景点配图（可选） |

---

## 第一部分：本地准备（在你的电脑上操作）

### 1. 构建前端

在项目目录下执行：

```bash
cd helloagents-trip-planner-langchain/frontend

# 首次需要安装依赖
npm install

# 构建生产版本（产物在 dist/ 目录）
npm run build
```

构建完成后，确认 `frontend/dist/` 目录存在且包含 `index.html`：

```bash
ls frontend/dist/index.html
```

### 2. 提交并推送到 GitHub

```bash
cd helloagents-trip-planner-langchain

# 确认 dist 已从 .gitignore 中移除（首次需检查）
git status

# 添加所有变更（包括 dist/）
git add .

# 提交
git commit -m "deploy: 构建前端 dist"

# 推送到 GitHub
git push origin main
```

> `.gitignore` 已配置为 **不忽略** `dist/` 目录，因此前端构建产物会随代码一起推送到 GitHub。每次修改前端代码后，需要重新 `npm run build` 并推送新的 `dist/`。

---

## 第二部分：服务器配置（在阿里云 ECS 上操作）

### 1. 连接服务器

```bash
ssh root@<你的服务器公网IP>
```

### 2. 确认 Docker 环境

```bash
docker --version         # ≥ 20.10
docker compose version   # ≥ v2.0
```

如果 Docker Compose 不可用：

```bash
sudo apt update && sudo apt install docker-compose-plugin -y
```

### 3. 安装 Git 并克隆项目

```bash
# 安装 Git（通常已预装）
sudo apt install git -y

# 克隆项目
cd ~
git clone <你的GitHub仓库地址>
cd helloagents-trip-planner-langchain
```

### 4. 配置环境变量

```bash
cd deploy
cp .env.example .env
nano .env
```

填入真实密钥：

```env
# LLM API 配置（推荐 DeepSeek，性价比高）
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 高德地图 Web 服务 Key（用于后端 API 调用）
AMAP_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Unsplash Access Key（可选，用于景点配图）
UNSPLASH_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 高德地图 Key（后端 pydantic-settings 读取）
AMAP_WEB_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 高德地图 Web JS Key（用于前端地图展示，可与 AMAP_WEB_KEY 相同）
VITE_AMAP_WEB_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **高德 Key 说明**：在 console.amap.com 创建应用时需同时勾选「Web 服务」和「Web JS API」平台类型。`AMAP_WEB_KEY` 和 `VITE_AMAP_WEB_KEY` 可以填相同的值。

保存退出（`Ctrl+X` → `Y` → `Enter`）。

### 5. 确认前端 dist 目录存在

由于前端是本地构建好推送到 GitHub 的，克隆后应该已经有 dist 目录：

```bash
ls ~/helloagents-trip-planner-langchain/frontend/dist/index.html
```

如果提示文件不存在，说明你还没有在本地构建并推送前端。请回到「第一部分」执行构建和推送步骤。

### 6. 启动服务

```bash
cd ~/helloagents-trip-planner-langchain/deploy

# 首次启动（构建后端 Docker 镜像）
docker compose up -d --build
```

首次构建需要几分钟（下载 Python 镜像 + 安装 pip 依赖）。后续重启只需 `docker compose up -d`。

查看启动状态：

```bash
docker compose ps
```

正常输出两个容器状态均为 `Up`：

```
NAME                     STATUS
trip-planner-backend     Up (healthy)
trip-planner-frontend    Up
```

查看后端日志：

```bash
docker compose logs backend
```

---

## 第三部分：验证部署

### 1. 健康检查

```bash
curl http://localhost:8000/api/trip/health
```

应返回：

```json
{
  "status": "ok",
  "llm_configured": true,
  "amap_configured": true,
  "unsplash_configured": true
}
```

### 2. 浏览器访问

在浏览器打开 `http://<你的服务器公网IP>`：

- 首页显示旅行规划表单
- 填写目的地、日期和偏好，点击「开始规划」
- 等待 10-30 秒，AI 生成完整旅行计划

### 3. API 文档

访问 `http://<你的服务器公网IP>/api/docs` 查看 Swagger 交互式文档。

---

## 日常更新流程

当你修改了代码后，完整的更新步骤如下：

### 在本机上

```bash
cd helloagents-trip-planner-langchain

# 1. 如果修改了前端代码，重新构建
cd frontend && npm run build && cd ..

# 2. 提交并推送
git add .
git commit -m "描述你的变更"
git push origin main
```

### 在服务器上

```bash
cd ~/helloagents-trip-planner-langchain

# 拉取最新代码（包括新的 dist/）
git pull

# 如果只改了前端：重启前端容器即可
cd deploy && docker compose restart frontend

# 如果改了后端代码：重新构建后端镜像
cd deploy && docker compose up -d --build backend

# 如果改了 .env：重启所有服务
cd deploy && docker compose restart
```

---

## 常用运维命令

```bash
cd ~/helloagents-trip-planner-langchain/deploy

# 查看容器状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 查看后端日志
docker compose logs backend --tail 100

# 查看前端 Nginx 日志
docker compose logs frontend

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 进入后端容器调试
docker exec -it trip-planner-backend bash
```

---

## 端口与安全组

| 端口 | 用途 | 公网开放 |
|------|------|---------|
| 22   | SSH  | 是 |
| 80   | HTTP（前端 + API） | 是 |
| 8000 | 后端 API | 否 |

阿里云 ECS 控制台 → 安全组 → 配置规则 → **入方向**：

| 协议 | 端口范围 | 授权对象 |
|------|---------|---------|
| TCP  | 80/80   | 0.0.0.0/0 |
| TCP  | 22/22   | 0.0.0.0/0 |

---

## 资源配置建议

| 配置 | 最低 | 推荐 |
|------|------|------|
| CPU  | 2 核 | 2 核 |
| 内存 | 4 GB  | 4 GB  |
| 硬盘 | 20 GB | 40 GB |
| 带宽 | 1 Mbps | 3 Mbps |

---

## 故障排查

### 后端启动失败

```bash
docker compose logs backend
```

常见原因：
- `.env` 未配置或密钥格式错误
- Docker 内存不足（`free -h` 检查）
- 端口 8000 被占用（`lsof -i :8000`）

### 前端 502 Bad Gateway

通常是后端挂了：

```bash
docker compose ps backend
docker compose logs backend --tail 30
```

### 前端页面白屏或 404

确认 dist 已正确部署：

```bash
ls -la ~/helloagents-trip-planner-langchain/frontend/dist/
docker exec trip-planner-frontend ls /usr/share/nginx/html/
```

### API 请求超时

Agent 调用外部 LLM 可能耗时较长。Nginx 已配置 `proxy_read_timeout 300s`（5分钟），如需更长可在 `nginx.conf` 中调大。

### 高德地图不显示

- 确认高德 Key 已启用「Web JS API」平台类型
- 浏览器 F12 查看控制台是否有 Key 相关报错
- 确认 `VITE_AMAP_WEB_KEY` 在前端构建时已正确注入

### 安全组未开放

如果无法通过公网 IP 访问，检查阿里云安全组入方向是否开放了 80 端口。

---

## 可选增强

### 配置 HTTPS（Let's Encrypt 免费证书）

需要先绑定域名到服务器 IP，然后：

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
sudo certbot renew --dry-run   # 测试自动续期
```

### 日志轮转（防止磁盘占满）

编辑 `/etc/docker/daemon.json`：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker
# 重启 Docker 后需要重新 docker compose up -d
```

---

## 文件清单

```
deploy/
├── DEPLOY_GUIDE.md        # 本部署指南
├── .env.example           # 环境变量模板（提交到 Git）
├── .env                   # 真实密钥（服务器本地创建，不提交）
├── docker-compose.yml     # 容器编排（前端挂载 dist，后端构建镜像）
├── backend.Dockerfile     # 后端 Python 镜像
├── frontend.Dockerfile    # 前端多阶段构建镜像（备选，服务器无 Node 时不用）
├── nginx.conf             # Nginx 反向代理 + SPA 路由
├── quick-deploy.sh        # 一键部署脚本
└── RENDER.md              # Render.com 免费部署说明（海外备选）
```
