# Render.com 部署步骤

## 前置条件

1. 代码已推送到 **GitHub 公开仓库**（Render 免费版只支持公开仓库）
2. 已注册 Render 账号（https://render.com，用 GitHub 账号直接登录）

---

## 总览

部署两个服务：

| 服务 | 类型 | URL |
|------|------|-----|
| trip-planner-backend | Web Service | `https://trip-planner-backend.onrender.com` |
| trip-planner-frontend | Static Site | `https://trip-planner-frontend.onrender.com` |

用户在浏览器访问前端 URL，前端通过 CORS 直接调用后端 API。

---

## 第一步：部署后端（Web Service）

1. 登录 [Render Dashboard](https://dashboard.render.com)，点 **New → Web Service**

2. 在 "Connect a repository" 中选择你的 GitHub 仓库，点 **Connect**

3. 填写配置：

   | 字段 | 值 |
   |------|-----|
   | Name | `trip-planner-backend` |
   | Region | `Singapore`（亚洲延迟最低） |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r backend/requirements.txt` |
   | Start Command | `cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port $PORT` |
   | Plan | **Free** |

4. 在 **Environment Variables** 中添加（点 "Add Environment Variable"）：

   ```
   LLM_API_KEY              = sk-你的密钥
   LLM_BASE_URL             = https://dashscope.aliyuncs.com/compatible-mode/v1
   LLM_MODEL                = deepseek-v4-pro
   AMAP_API_KEY             = 你的高德Key
   UNSPLASH_ACCESS_KEY      = 你的Unsplash Key
   PYTHON_VERSION           = 3.10
   ```

5. 点 **Create Web Service**。等待 3-5 分钟构建完成。

6. 验证：打开 `https://trip-planner-backend.onrender.com/api/trip/health`，应返回 `{"status": "ok", ...}`

---

## 第二步：部署前端（Static Site）

1. 在 Render Dashboard 点 **New → Static Site**

2. 选择同一个 GitHub 仓库，点 **Connect**

3. 填写配置：

   | 字段 | 值 |
   |------|-----|
   | Name | `trip-planner-frontend` |
   | Build Command | `cd frontend && npm install && npm run build` |
   | Publish Directory | `frontend/dist` |

4. 在 **Environment Variables** 中添加：

   ```
   VITE_AMAP_WEB_KEY        = 你的高德Web JS Key（和上面的可以同一个）
   VITE_API_BASE_URL        = https://trip-planner-backend.onrender.com/api
   ```

5. 展开 **Advanced → Rewrite Rules**，添加一条：

   | Source | Destination |
   |--------|-------------|
   | `/*` | `/index.html` |

   （这条规则让 Vue Router 的 SPA 路由正常工作——刷新页面不会 404）

6. 点 **Create Static Site**。等待 2-3 分钟构建完成。

7. 打开 `https://trip-planner-frontend.onrender.com` 即可使用。

---

## 第三步：测试

1. 打开前端页面 `https://trip-planner-frontend.onrender.com`
2. 填写目的地（如"北京"）、日期、偏好
3. 点击"开始规划"
4. 等待 Agent 执行（注意：免费版后端 15 分钟无请求会自动休眠，冷启动首次请求可能需要等待 30-60 秒）

---

## 关于免费版的限制

| 限制 | 影响 |
|------|------|
| 15 分钟无请求自动休眠 | 打开页面后第一次请求会有 **30-60 秒**的冷启动等待 |
| 每月 750 小时运行时间 | 免费额度够一个实例 24/7 运行 |
| 512 MB RAM + 0.1 vCPU | Agent 调用 LLM 是 I/O 密集足够用，但并发用户不能太多 |
| 静态站点 100 GB 带宽 | 足够 Demo 使用 |

**应对冷启动**：可以自己写一个 cron job 每 14 分钟请求一次 `/api/trip/health` 防止休眠（需要外部的免费 cron 服务如 cron-job.org）。

---

## 如要绑定自己的域名

Static Site 的 Settings 里有 "Custom Domain" 选项，添加你的域名并配置 DNS CNAME 记录即可。

Backend 同理，但后端自定义域名需要**付费套餐**（$7/月起）。如果只需要展示，用免费 `onrender.com` 域名即可。

---

## 常见问题

**Q: 前端页面打开白屏？**

F12 打开浏览器 Console 看错误。常见原因：
- `VITE_API_BASE_URL` 没配置或写错
- 确保后端已部署成功（访问后端 health 端点确认）

**Q: 后端报 502 / 503？**

- 免费版冷启动需要耐心等 30-60 秒
- 检查 Environment Variables 是否全部填写
- 查看 Render Dashboard → Logs 确认错误详情

**Q: 提示 CORS 错误？**

后端 `app/api/main.py` 已配置 `allow_origins=["*"]`，一般不会有 CORS 问题。如果出现，检查是否两边的 URL 配置一致。
