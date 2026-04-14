from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "VOID VORTEX"
    env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    jwt_secret: str = Field("change-me-please-1234", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite+aiosqlite:///./void_vortex.db"
    redis_url: str = "redis://localhost:6379/0"

    docker_network: str = "void_vortex_net"
    docker_socket: str = "unix://var/run/docker.sock"
    deploy_root: Path = Path("./deployments")
    bot_log_root: Path = Path("./logs")

    github_clone_timeout: int = 240
    rate_limit_per_minute: int = 120

    stripe_webhook_secret: str = ""
    razorpay_webhook_secret: str = ""

    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_bot_token: str = ""


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.deploy_root.mkdir(parents=True, exist_ok=True)
    settings.bot_log_root.mkdir(parents=True, exist_ok=True)
    return settings
