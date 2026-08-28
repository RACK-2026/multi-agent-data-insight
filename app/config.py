"""
配置管理 - 通过环境变量加载可选配置
"""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "Multi-Agent Data Insight Demo"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Optional external data source integration. Keep disabled in the public demo.
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    BITABLE_APP_TOKEN: str = ""
    TABLE_MAIN: str = ""
    TABLE_REVIEW: str = ""
    TABLE_ACCOUNT: str = ""
    TABLE_TEAM: str = ""

    # LLM 配置（默认豆包）
    LLM_PROVIDER: Literal["doubao", "openai", "custom"] = "doubao"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = "doubao-seed-2-0-lite-260428"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7

    # 本地数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/demo.db"

    # 审核阈值
    REVIEW_SCORE_THRESHOLD: float = 70.0

    # Web 前端静态目录
    STATIC_DIR: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# 确保data目录存在
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

