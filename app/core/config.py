"""Typed application settings from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "dev", "staging", "prod", "test"] = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://scoring:scoring@localhost:5432/scoring",
        description="Async SQLAlchemy database URL",
    )

    openai_api_key: str = Field(default="", description="API key for OpenAI-compatible endpoint")
    openai_base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 120.0
    llm_max_retries: int = 3

    s3_bucket: str = ""
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None

    api_key: str = Field(default="", description="Optional shared secret for API authentication")

    worker_poll_interval_seconds: float = 2.0
    worker_batch_size: int = 1

    default_score_profile: str = "credibility_v1"
    score_profile_version: str = "1"

    otel_exporter_otlp_endpoint: str | None = None

    job_queue_backend: Literal["database", "sqs"] = "database"
    sqs_queue_url: str = ""
    sqs_visibility_timeout_seconds: float = 900.0

    @field_validator("database_url")
    @classmethod
    def ensure_async_driver(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear settings cache (for tests)."""
    get_settings.cache_clear()
