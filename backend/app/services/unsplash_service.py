"""Unsplash 图片服务 — 为景点获取配图"""
import httpx
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class UnsplashService:
    """Unsplash 图片搜索服务"""

    def __init__(self, access_key: str):
        self.access_key = access_key
        self.base_url = "https://api.unsplash.com"

    def search_photos(self, query: str, per_page: int = 10) -> List[Dict]:
        """搜索图片, 返回图片信息列表"""
        if not self.access_key:
            return []

        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key,
            }
            resp = httpx.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            photos = []
            for r in results:
                photos.append({
                    "url": r["urls"]["regular"],
                    "thumb": r["urls"]["thumb"],
                    "description": r.get("description", "") or r.get("alt_description", ""),
                    "photographer": r["user"]["name"],
                })
            return photos

        except Exception:
            return []

    def get_photo_url(self, query: str) -> Optional[str]:
        """搜索并返回第一张图片的 URL"""
        photos = self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None

    def get_photos_for_attractions(
        self, attraction_names: list[str], city: str
    ) -> Dict[str, Optional[str]]:
        """批量为景点获取图片 URL"""
        result = {}
        for name in attraction_names:
            query = f"{name} {city}"
            result[name] = self.get_photo_url(query)
        return result
