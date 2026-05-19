"""TripPlannerAgent — 基于 LangChain 的多智能体协作编排器

协调四个专门 Agent 完成旅行规划:
  1. AttractionSearchAgent — 搜索景点 (ReAct Agent + Amap tools)
  2. WeatherQueryAgent — 查询天气 (ReAct Agent + Amap tools)
  3. HotelAgent — 搜索酒店 (ReAct Agent + Amap tools)
  4. PlannerAgent — 整合生成计划 (纯推理 Agent, 无工具)
"""
import json
import logging
import concurrent.futures
from datetime import date, datetime, timedelta

from app.config import Settings, get_settings
from app.models.schemas import TripPlanRequest, TripPlan
from app.tools import create_amap_tools
from app.agents.langchain_agents import build_agent
from app.agents.prompts import (
    ATTRACTION_AGENT_PROMPT,
    WEATHER_AGENT_PROMPT,
    HOTEL_AGENT_PROMPT,
    PLANNER_AGENT_PROMPT,
)

logger = logging.getLogger(__name__)

# 高德天气 API 最多提供 4 天预报（今天 + 未来 3 天）
AMAP_FORECAST_DAYS = 4


class TripPlannerAgent:
    """旅行规划编排器 — 基于 LangChain 框架的多智能体协作"""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

        # 创建共享的高德地图工具 (LangChain 工具)
        amap_tools = create_amap_tools(self.settings.amap_api_key)

        # 通用 LLM 参数
        llm_kwargs = {
            "model": self.settings.llm_model,
            "api_key": self.settings.llm_api_key,
            "base_url": self.settings.llm_base_url,
        }

        # 创建四个专门的 LangChain Agent
        self.attraction_agent = build_agent(
            name="AttractionSearchAgent",
            system_prompt=ATTRACTION_AGENT_PROMPT,
            tools=amap_tools,
            **llm_kwargs,
        )

        self.weather_agent = build_agent(
            name="WeatherQueryAgent",
            system_prompt=WEATHER_AGENT_PROMPT,
            tools=amap_tools,
            **llm_kwargs,
        )

        self.hotel_agent = build_agent(
            name="HotelAgent",
            system_prompt=HOTEL_AGENT_PROMPT,
            tools=amap_tools,
            **llm_kwargs,
        )

        self.planner_agent = build_agent(
            name="PlannerAgent",
            system_prompt=PLANNER_AGENT_PROMPT,
            tools=[],  # Planner 不需要工具, 只做整合
            max_tokens=8192,  # Planner 需要输出完整 JSON 计划, 配额加大
            **llm_kwargs,
        )

    def _parse_date(self, date_str: str) -> date:
        """解析日期字符串为 date 对象，支持 YYYY-MM-DD 和 ISO 格式"""
        for fmt in ("%Y-%m-%d",):
            try:
                return datetime.strptime(date_str[:10], fmt).date()
            except (ValueError, IndexError):
                pass
        # 尝试 ISO 格式
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            pass
        raise ValueError(f"无法解析日期: {date_str}")

    def _check_weather_availability(
        self, start_date: str, end_date: str
    ) -> tuple[bool, str]:
        """
        检查旅行日期是否在天气预报窗口内。
        返回 (是否有可用天气, 状态描述)
        """
        try:
            trip_start = self._parse_date(start_date)
            trip_end = self._parse_date(end_date)
        except ValueError as e:
            logger.warning(f"日期解析失败, 回退到默认天气查询: {e}")
            return True, ""

        today = date.today()
        forecast_end = today + timedelta(days=AMAP_FORECAST_DAYS - 1)

        if trip_start > forecast_end:
            return False, (
                f"旅行开始日期({trip_start})超出天气预报窗口"
                f"({today}~{forecast_end}), 天气数据暂不可用。"
                f"请在 overall_suggestions 中提醒用户临近出发时再次查询天气。"
            )
        elif trip_end > forecast_end:
            return True, (
                f"注意: 旅行日期({trip_start}~{trip_end})仅有前"
                f"{(forecast_end - trip_start).days + 1}天有天气预报覆盖,"
                f"后续日期天气暂不可用。请在 weather_info 中只包含有数据的日期,"
                f"并在 overall_suggestions 中提醒用户后续日期临近时查询。"
            )
        return True, ""

    def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        """
        完整的旅行规划流程:
        1. 并行搜索景点、天气、酒店 (LangChain ReAct Agents)
        2. 整合生成旅行计划
        3. 解析为 Pydantic 模型
        """
        print(f"\n🚀 开始多智能体协作规划旅行 (LangChain 框架)...")
        print(f"   目的地: {request.city}")
        print(f"   偏好: {request.preferences} | 预算: {request.budget}")
        print(f"   交通: {request.transportation} | 住宿: {request.accommodation}")
        print("=" * 60)

        # ── 检查天气可用性 ──
        weather_available, weather_note = self._check_weather_availability(
            request.start_date, request.end_date
        )

        # ── 步骤 1-3: 并行执行搜索 Agent ──
        attraction_query = (
            f"请根据用户偏好'{request.preferences}'"
            f"搜索{request.city}的旅游景点。"
            f"请搜索2-3次,使用不同的关键词,确保覆盖足够的景点。"
        )
        weather_query = (
            f"请查询{request.city}的天气信息"
            if weather_available
            else "天气数据不可用"
        )
        hotel_query = (
            f"请搜索{request.city}的{request.accommodation}"
        )

        print("📍 步骤1: 并行搜索景点、天气、酒店 (LangChain ReAct Agents)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_attr = executor.submit(self.attraction_agent, attraction_query)
            future_hotel = executor.submit(self.hotel_agent, hotel_query)
            if weather_available:
                future_weather = executor.submit(
                    self.weather_agent, weather_query
                )

            attraction_response = future_attr.result(timeout=180)
            hotel_response = future_hotel.result(timeout=180)
            weather_response = (
                future_weather.result(timeout=180)
                if weather_available
                else "天气数据暂不可用（旅行日期超出预报窗口）"
            )

        print(f"   ✅ 景点搜索完成 ({len(attraction_response)} 字符)")
        if weather_available:
            print(f"   ✅ 天气查询完成 ({len(weather_response)} 字符)")
        else:
            print(f"   ⏭️  天气跳过 (日期超出预报窗口)")
        print(f"   ✅ 酒店搜索完成 ({len(hotel_response)} 字符)")

        # ── 步骤 4: Planner 整合生成计划 ──
        print("\n📋 步骤2: AI 生成行程计划...")
        planner_query = self._build_planner_query(
            request, attraction_response, weather_response, hotel_response,
            weather_note
        )
        planner_response = self.planner_agent(planner_query)
        print(f"   ✅ 计划生成完成 ({len(planner_response)} 字符)")

        # ── 步骤 5: 解析 JSON → TripPlan ──
        trip_plan = self._parse_trip_plan(planner_response)
        print(f"   📅 共 {len(trip_plan.days)} 天行程, "
              f"{sum(len(d.attractions) for d in trip_plan.days)} 个景点")

        return trip_plan

    def _build_planner_query(
        self,
        request: TripPlanRequest,
        attraction_response: str,
        weather_response: str,
        hotel_response: str,
        weather_note: str = "",
    ) -> str:
        """构建 Planner Agent 的完整查询"""
        weather_section = f"""**天气查询结果:**
{weather_response}"""

        if weather_note:
            weather_section += f"""

**天气数据重要提示:**
{weather_note}"""

        notes_section = ""
        if request.notes:
            notes_section = f"""
**用户补充说明 (重要,需特别关注):**
{request.notes}"""

        return f"""
请根据以下信息生成{request.city}的{request.days}日旅行计划:

**用户需求:**
- 目的地: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.days}天
- 偏好: {request.preferences}
- 预算: {request.budget}
- 交通方式: {request.transportation}
- 住宿类型: {request.accommodation}{notes_section}

**景点搜索结果:**
{attraction_response}

{weather_section}

**酒店搜索结果:**
{hotel_response}

请严格按照JSON格式生成详细的旅行计划,包括每天的景点安排、餐饮推荐、住宿信息和预算明细。
直接输出JSON,不要包含```json标记。"""

    def _parse_trip_plan(self, raw_response: str) -> TripPlan:
        """解析 Planner 返回的 JSON 为 TripPlan 模型"""
        json_str = raw_response.strip()

        # 移除可能的 markdown 代码块标记
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            json_str = "\n".join(lines)

        # 查找 JSON 对象的起始和结束位置
        start_idx = json_str.find("{")
        if start_idx == -1:
            raise ValueError(f"无法在响应中找到 JSON 对象: {raw_response[:200]}...")

        # 找到匹配的结束括号
        brace_count = 0
        end_idx = -1
        for i in range(start_idx, len(json_str)):
            if json_str[i] == "{":
                brace_count += 1
            elif json_str[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break

        if end_idx == -1:
            raise ValueError("JSON 格式不完整")

        json_str = json_str[start_idx:end_idx]

        try:
            data = json.loads(json_str)
            return TripPlan(**data)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"解析失败: {e}\n原始响应片段: {json_str[:500]}...")
            raise ValueError(f"旅行计划 JSON 解析失败: {e}") from e
