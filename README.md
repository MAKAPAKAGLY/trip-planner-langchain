# ✈️ 智能旅行助手 — LangChain 版 (HelloAgents Trip Planner)

基于 LangChain/LangGraph 框架的 AI 旅行规划应用，输入目的地、日期和偏好，自动生成包含景点、酒店、餐饮、天气、预算的完整旅行计划，支持地图可视化和导出。

## 功能特性

- **智能行程规划** — 填写目的地、日期、偏好、预算等信息，AI 自动生成每日行程
- **多 Agent 协作** — 景点搜索、天气查询、酒店推荐、行程整合四个 Agent 并行工作
- **LangChain 框架** — 基于 `langgraph.prebuilt.create_react_agent` 的 ReAct Agent，自动处理工具调用循环
- **地图可视化** — 高德地图标注景点位置，一目了然
- **预算明细** — 自动计算门票、酒店、餐饮、交通四项费用
- **行程编辑** — 支持上移、下移、删除景点，实时调整计划
- **导出分享** — 支持导出为 PNG 图片或 PDF 文件
- **天气信息** — 集成天气预报，帮助合理安排行程

## 技术架构

```
┌─────────────────────────────────────────┐
│              前端 (Vue 3)                │
│    Ant Design Vue + 高德地图 JS API      │
└─────────────────┬───────────────────────┘
                  │ HTTP REST
┌─────────────────▼───────────────────────┐
│            后端 (FastAPI)                │
│        Pydantic 数据模型 + API 路由       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Agent 层 (LangChain)             │
│  create_agent ← ChatOpenAI +            │
│  langchain.agents 自动推理循环           │
│  ├─ AttractionSearchAgent (ReAct + 工具) │
│  ├─ WeatherQueryAgent    (ReAct + 工具)  │
│  ├─ HotelAgent           (ReAct + 工具)  │
│  └─ PlannerAgent         (纯推理)       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          外部服务                        │
│  高德地图 API  │  Unsplash  │  LLM API   │
└─────────────────────────────────────────┘
```

## 与原始版本的区别

本版本使用 **LangChain 框架** 替代了自定义的 Agent 实现：

| 组件 | 原始版本 | LangChain 版 |
|------|---------|-------------|
| Agent 实现 | SimpleAgent (自实现, 正则解析工具调用) | create_agent (langchain.agents, v1 API) |
| 工具系统 | Tool / ToolRegistry (自实现) | @tool 装饰器 (langchain_core.tools) |
| LLM 客户端 | openai.OpenAI (原始 SDK) | ChatOpenAI (langchain_openai) |
| 推理循环 | 手动 while 循环 + regex 解析 | LangGraph 状态图自动处理 |
| 工具调用格式 | [TOOL_CALL:name:key=val] 文本标记 | 原生 function calling |

## 项目结构

```
helloagents-trip-planner-langchain/
├── backend/
│   ├── .env                        # 环境变量配置
│   ├── requirements.txt            # Python 依赖 (langchain 系列)
│   ├── run.py                      # 启动入口
│   └── app/
│       ├── config.py               # 全局配置
│       ├── models/schemas.py       # Pydantic 数据模型
│       ├── tools/                  # 工具系统
│       │   ├── amap_tools.py       # 高德地图工具 (@tool 装饰器)
│       │   └── __init__.py
│       ├── agents/                 # 智能体层
│       │   ├── langchain_agents.py # LangChain Agent 工厂函数
│       │   ├── prompts.py          # 专门 Agent 提示词
│       │   ├── trip_planner.py     # 多 Agent 编排器
│       │   ├── simple_agent.py     # [已弃用] 原始自定义实现
│       │   └── __init__.py
│       ├── services/
│       │   ├── unsplash_service.py # Unsplash 图片服务
│       │   └── __init__.py
│       └── api/
│           ├── main.py             # FastAPI 应用
│           └── routes/
│               ├── trip.py         # 旅行规划 API
│               └── __init__.py
│
└── frontend/
    ├── .env                        # 前端环境变量
    ├── package.json                # npm 依赖
    ├── vite.config.ts              # Vite 构建配置
    └── src/
        ├── main.ts                 # 应用入口
        ├── App.vue                 # 根组件
        ├── types/index.ts          # TypeScript 类型定义
        ├── services/api.ts         # API 服务封装
        ├── router/index.ts         # 路由配置
        └── views/
            ├── Home.vue            # 首页 (表单)
            └── Result.vue          # 结果页 (计划展示)
```

## 环境要求

- Python 3.10+
- Node.js 16.0+
- npm 8.0+

## 快速开始

### 1. 获取 API 密钥

注册并获取以下密钥：

| 服务 | 地址 | 说明 |
|------|------|------|
| LLM API | OpenAI / DeepSeek 等 | 用于驱动 Agent 思考和规划 |
| 高德地图 | https://console.amap.com/ | Web 服务 Key (后端调用) + Web JS Key (前端地图) |
| Unsplash | https://unsplash.com/developers | 可选，用于获取景点配图 |

### 2. 配置环境变量

**后端配置** ：

```env
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
AMAP_API_KEY=your-amap-web-service-key
UNSPLASH_ACCESS_KEY=your-unsplash-access-key
```

**前端配置**：

```env
VITE_AMAP_WEB_KEY=your-amap-web-js-key
```

### 3. 启动后端

```bash
cd helloagents-trip-planner-langchain/backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python run.py
```

成功后在浏览器访问 http://localhost:8000/docs 可查看 API 文档。

### 4. 启动前端

```bash
cd helloagents-trip-planner-langchain/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

成功后在浏览器访问 http://localhost:5173 即可使用。

## 使用指南

1. 在首页表单中填写目的地城市、旅行日期、偏好、预算、交通及住宿类型
2. 点击「开始规划」按钮，等待 AI 生成计划（约 10-30 秒）
3. 结果页展示：
   - **行程概览** — 目的地、日期、天数和总费用
   - **预算明细** — 门票、酒店、餐饮、交通分项统计
   - **景点地图** — 高德地图标注所有景点位置
   - **每日行程** — 每天的具体景点、餐饮和住宿安排
   - **天气预报** — 每日天气信息
   - **出行建议** — AI 生成的整体建议
4. 点击「编辑行程」可自由调整景点顺序或删除景点
5. 通过「导出行程」下拉菜单将计划保存为图片或 PDF

## API 接口

### POST /api/trip/plan

生成旅行计划。

**请求体：**

```json
{
  "city": "北京",
  "start_date": "2026-05-10",
  "end_date": "2026-05-12",
  "days": 3,
  "preferences": "历史文化",
  "budget": "中等",
  "transportation": "公共交通",
  "accommodation": "经济型酒店"
}
```

**响应：** 完整的 TripPlan 对象，包含每日行程、景点、酒店、天气、预算等信息。

### GET /api/trip/health

健康检查，返回各服务配置状态。

## LangChain 框架说明

本版本引入以下 LangChain 核心组件：

- **langchain-openai** — ChatOpenAI 作为 LLM 驱动，支持原生 function calling
- **langchain.agents** — create_agent (v1 API) 提供标准 ReAct 循环
- **langchain-core** — @tool 装饰器定义工具，自动生成 function schema
- **langgraph** — 状态图引擎，底层编排 Agent 的执行流

## 部署指南

项目通过 GitHub + Docker Compose 部署到阿里云 ECS。前端在本地构建，dist 随代码一起推送到 GitHub，服务器 git pull 后直接挂载使用（服务器无需 Node.js）。

> 完整的分步教程：[deploy/DEPLOY_GUIDE.md](deploy/DEPLOY_GUIDE.md)

### 部署流程概览

```
本地:  npm run build → git push
                        ↓
服务器: git pull → docker compose up -d
```

### 本机操作（每次修改前端后）

```bash
# 1. 构建前端
cd frontend && npm run build && cd ..

# 2. 推送代码（包含 dist/）
git add . && git commit -m "deploy" && git push
```

### 服务器操作（首次部署）

```bash
# 1. 克隆项目
git clone <你的仓库地址> && cd helloagents-trip-planner-langchain/deploy

# 2. 配置密钥
cp .env.example .env && nano .env

# 3. 一键启动
chmod +x quick-deploy.sh && ./quick-deploy.sh
```

### 服务器操作（日常更新）

```bash
cd ~/helloagents-trip-planner-langchain
git pull
cd deploy

# 只改了前端 → 重启前端容器
docker compose restart frontend

# 改了后端 → 重新构建
docker compose up -d --build backend
```

### 部署文件一览

| 文件 | 说明 |
|------|------|
| `deploy/DEPLOY_GUIDE.md` | 详细部署文档（分步教程 + 架构图 + 故障排查） |
| `deploy/quick-deploy.sh` | 服务器端一键部署脚本 |
| `deploy/docker-compose.yml` | 容器编排（后端 Docker 构建 + 前端挂载 dist） |
| `deploy/backend.Dockerfile` | 后端 Python 镜像 |
| `deploy/frontend.Dockerfile` | 前端多阶段构建镜像（备选，服务器无 Node 时不用） |
| `deploy/nginx.conf` | Nginx 反向代理 + SPA 路由 |
| `deploy/.env.example` | 环境变量模板 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `LLM_API_KEY` | LLM API 密钥 |
| `LLM_BASE_URL` | LLM API 地址 |
| `LLM_MODEL` | 模型名称 |
| `AMAP_API_KEY` | 高德地图 Web 服务 Key |
| `AMAP_WEB_KEY` | 高德地图 Key（后端用） |
| `UNSPLASH_ACCESS_KEY` | Unsplash 图片 Key |
| `VITE_AMAP_WEB_KEY` | 高德地图 Web JS Key（前端构建时注入） |

## License

MIT
