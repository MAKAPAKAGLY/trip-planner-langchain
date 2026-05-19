"""旅行规划 API 路由"""
import logging
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.schemas import TripPlanRequest, TripPlan
from app.agents.trip_planner import TripPlannerAgent
from app.services.unsplash_service import UnsplashService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trip", tags=["旅行规划"])

# 全局单例 (延迟初始化)
_trip_planner: TripPlannerAgent | None = None
_unsplash_service: UnsplashService | None = None


def get_trip_planner() -> TripPlannerAgent:
    global _trip_planner
    if _trip_planner is None:
        settings = get_settings()
        _trip_planner = TripPlannerAgent(settings)
    return _trip_planner


def get_unsplash_service() -> UnsplashService:
    global _unsplash_service
    if _unsplash_service is None:
        settings = get_settings()
        _unsplash_service = UnsplashService(settings.unsplash_access_key)
    return _unsplash_service


@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """创建旅行计划"""
    try:
        print("=" * 60)
        print("📥 收到旅行规划请求:")
        print(f"   城市: {request.city}")
        print(f"   日期: {request.start_date} — {request.end_date}")
        print(f"   天数: {request.days}天 | 偏好: {request.preferences}")
        print("=" * 60)

        # 生成旅行计划
        trip_planner = get_trip_planner()
        trip_plan = trip_planner.plan_trip(request)

        # 为每个景点获取 Unsplash 图片
        print("\n🖼️  获取景点图片...")
        unsplash = get_unsplash_service()
        image_count = 0
        total = sum(len(d.attractions) for d in trip_plan.days)
        for day in trip_plan.days:
            for attraction in day.attractions:
                if not attraction.image_url:
                    try:
                        # 先用景点名+城市搜索
                        image_url = unsplash.get_photo_url(
                            f"{attraction.name} {trip_plan.city}"
                        )
                        # 没找到则用类别+城市宽泛搜索
                        if not image_url and attraction.category:
                            image_url = unsplash.get_photo_url(
                                f"{attraction.category} {trip_plan.city} travel"
                            )
                        # 还找不到就只用城市名
                        if not image_url:
                            image_url = unsplash.get_photo_url(
                                f"{trip_plan.city} travel landmark"
                            )
                        if image_url:
                            attraction.image_url = image_url
                            image_count += 1
                    except Exception:
                        pass  # 单张失败忽略
        print(f"   ✅ 获取 {image_count}/{total} 张图片")

        print(f"\n✅ 旅行计划生成成功,准备返回响应\n")
        return trip_plan

    except ValueError as e:
        logger.error(f"规划失败: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"规划异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")


@router.get("/health")
async def health_check():
    """健康检查"""
    settings = get_settings()
    return {
        "status": "ok",
        "llm_configured": bool(settings.llm_api_key),
        "amap_configured": bool(settings.amap_api_key),
        "unsplash_configured": bool(settings.unsplash_access_key),
    }
