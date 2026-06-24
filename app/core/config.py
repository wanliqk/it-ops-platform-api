from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "企业 IT 报修与资产管理平台"
    app_env: str = "local"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 120
    scheduler_enabled: bool = True
    sla_check_interval_minutes: int = 5
    database_url: str = (
        "mysql+pymysql://it:123456@127.0.0.1:3306/"
        "it_ops_platform?charset=utf8mb4"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "dev", "development"}:
                return True
        return value

    @field_validator("sla_check_interval_minutes")
    @classmethod
    def validate_sla_check_interval_minutes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("SLA_CHECK_INTERVAL_MINUTES must be greater than 0")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
