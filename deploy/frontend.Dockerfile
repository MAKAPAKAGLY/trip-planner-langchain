# ========================================
# 前端 Dockerfile — 构建静态文件 + Nginx 服务
# ========================================
FROM node:20-alpine AS builder

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .

# 构建时注入高德地图 Key（如有）
ARG VITE_AMAP_WEB_KEY
ENV VITE_AMAP_WEB_KEY=${VITE_AMAP_WEB_KEY}

RUN npm run build

# ── Nginx 运行阶段 ──
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 复制 Nginx 配置（反向代理 API 到后端）
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
