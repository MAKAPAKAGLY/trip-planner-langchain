# ========================================
# 前端 Dockerfile — 构建静态文件 + Nginx 服务
# ========================================

FROM node:20-alpine AS builder

WORKDIR /build

# npm 换国内源
RUN npm config set registry https://registry.npmmirror.com/

# 复制 package 文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制前端代码
COPY frontend/ .

# 构建时注入高德地图 Key（如有）
ARG VITE_AMAP_WEB_KEY
ENV VITE_AMAP_WEB_KEY=${VITE_AMAP_WEB_KEY}

# 构建前端
RUN npm run build

# ========================================
# Nginx 运行阶段
# ========================================

FROM nginx:alpine

# 复制构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]