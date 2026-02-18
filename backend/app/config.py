"""Application configuration settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App settings
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    # Database settings
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://finuser:finpass@localhost:5432/financial_analyzer",
        alias="DATABASE_URL",
    )

    # Redis settings
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    # OpenAI settings
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")

    # CrewAI settings
    crewai_verbose: bool = Field(default=True, alias="CREWAI_VERBOSE")

    # Cache settings
    cache_ttl_conversation: int = Field(default=3600, alias="CACHE_TTL_CONVERSATION")  # 1 hour
    cache_ttl_llm: int = Field(default=86400, alias="CACHE_TTL_LLM")  # 24 hours

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
