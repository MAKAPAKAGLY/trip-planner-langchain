"""高德地图 API 工具集 — LangChain 版本

使用 LangChain 的 @tool 装饰器封装高德地图 API。
提供的工具:
  - amap_text_search: POI 关键字搜索
  - amap_weather: 天气查询
"""
import httpx
from typing import Any, Dict, Optional
from langchain_core.tools import tool


# ── 模块级 API key 存储 (由 create_amap_tools 注入) ──
_amap_api_key: str = ""


def set_amap_api_key(key: str) -> None:
    """设置高德地图 API key"""
    global _amap_api_key
    _amap_api_key = key


def _get_api_key() -> str:
    return _amap_api_key


# ── LangChain Tools ─────────────────────────────────────────


@tool
def amap_text_search(
    keywords: str,
    city: str = "",
    page: int = 1,
) -> str:
    """搜索高德地图 POI 地点信息。

    适用场景: 搜索景点、酒店、餐厅等地点。

    Args:
        keywords: 搜索关键词，如"景点"、"博物馆"、"快捷酒店"
        city: 城市名，如"北京"、"上海"
        page: 页码，从1开始，每页最多10条结果

    Returns:
        格式化的搜索结果文本
    """
    api_key = _get_api_key()
    if not keywords:
        return "错误: 缺少 keywords 参数"

    try:
        url = "https://restapi.amap.com/v3/place/text"
        params: Dict[str, Any] = {
            "keywords": keywords,
            "city": city or "",
            "key": api_key,
            "output": "json",
            "offset": 10,
            "page": page,
        }
        resp = httpx.get(url, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "1":
            return f"API 错误: {data.get('info', '未知错误')}"

        pois = data.get("pois", [])
        total = int(data.get("count", 0))

        if not pois:
            return f"在{city or '指定区域'}未找到 '{keywords}' 相关结果"

        lines = [f"搜索 '{keywords}' 结果 (第{page}页, 共{total}条, 本页{len(pois)}条):"]
        for i, poi in enumerate(pois[:10], 1):
            name = poi.get("name", "未知")
            address = poi.get("address", "未知")
            location = poi.get("location", "0,0")
            biz_type = poi.get("type", "")
            rating = poi.get("biz_ext", {}).get("rating", "") or poi.get(
                "business_area", ""
            )
            tel = poi.get("tel", "")
            lines.append(
                f"  {i}. {name} | 地址: {address} | 坐标: {location}"
                f"{' | 评分: ' + rating if rating else ''}"
                f"{' | 电话: ' + tel if tel else ''}"
                f"{' | 类型: ' + biz_type if biz_type else ''}"
            )

        return "\n".join(lines)

    except httpx.HTTPError as e:
        return f"网络请求失败: {e}"
    except Exception as e:
        return f"搜索异常: {e}"


@tool
def amap_weather(city: str) -> str:
    """查询指定城市的天气预报。

    适用场景: 查询目的地未来几天的天气，帮助安排行程。

    Args:
        city: 城市名，如"北京"、"杭州"

    Returns:
        格式化的天气预报文本
    """
    api_key = _get_api_key()
    if not city:
        return "错误: 缺少 city 参数"

    try:
        # 先查城市 adcode
        geo_url = "https://restapi.amap.com/v3/config/district"
        geo_params: Dict[str, Any] = {
            "keywords": city,
            "subdistrict": 0,
            "key": api_key,
        }
        geo_resp = httpx.get(geo_url, params=geo_params, timeout=10.0)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        adcode = ""
        if geo_data.get("status") == "1":
            districts = geo_data.get("districts", [])
            if districts:
                adcode = districts[0].get("adcode", "")

        if not adcode:
            return f"未找到城市 '{city}' 的行政区划代码"

        # 查天气
        weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        weather_params: Dict[str, Any] = {
            "city": adcode,
            "key": api_key,
            "extensions": "all",
        }
        weather_resp = httpx.get(weather_url, params=weather_params, timeout=10.0)
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        if weather_data.get("status") != "1":
            return f"天气查询失败: {weather_data.get('info', '未知错误')}"

        forecasts = weather_data.get("forecasts", [])
        if not forecasts:
            return f"未获取到 {city} 的天气信息"

        lines = [f"{city} 天气 forecast 信息:"]
        for forecast in forecasts:
            casts = forecast.get("casts", [])
            for cast in casts:
                date = cast.get("date", "")
                day_weather = cast.get("dayweather", "")
                night_weather = cast.get("nightweather", "")
                day_temp = cast.get("daytemp", "")
                night_temp = cast.get("nighttemp", "")
                wind_dir = cast.get("daywind", "")
                wind_power = cast.get("daypower", "")
                lines.append(
                    f"  {date} | 白天: {day_weather} {day_temp}°C"
                    f" | 夜间: {night_weather} {night_temp}°C"
                    f" | 风向: {wind_dir} | 风力: {wind_power}级"
                )

        return "\n".join(lines)

    except httpx.HTTPError as e:
        return f"网络请求失败: {e}"
    except Exception as e:
        return f"天气查询异常: {e}"


def create_amap_tools(api_key: str) -> list:
    """创建并返回所有高德地图 LangChain 工具"""
    set_amap_api_key(api_key)
    return [amap_text_search, amap_weather]
