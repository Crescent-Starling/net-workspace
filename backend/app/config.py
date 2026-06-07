from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 在 Settings 初始化前加载 .env（确保 os.getenv 也能读取）
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv 未安装时不报错


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "NetWorkspace"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///./networkspace.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # DeepSeek / AI 配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    @property
    def database_url_sync(self) -> str:
        """Return a synchronous driver URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+aiosqlite", "").replace(
            "+asyncpg", "+psycopg"
        )


settings = Settings()
