"""启动后端服务"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,            # 若端口被占用可改为 8001 等
        reload=True,
    )
