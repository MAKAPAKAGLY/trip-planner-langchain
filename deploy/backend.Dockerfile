# ========================================
# 后端 Dockerfile
# ========================================
FROM python:3.10-slim

WORKDIR /app

# 强制替换 Debian 源
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb https://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# pip 换源
RUN pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    -r requirements.txt

# 复制后端代码
COPY backend/ .

# 暴露端口
EXPOSE 8000

# 启动
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]