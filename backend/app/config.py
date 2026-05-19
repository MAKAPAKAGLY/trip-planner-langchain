"""应用配置管理"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # LLM 配置
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"

    # 高德地图
    amap_api_key: str = ""

    # Unsplash
    unsplash_access_key: str = ""

    # 高德地图 Web JS Key (前端用)
    amap_web_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
