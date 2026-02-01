from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Financial Document Analyzer"
    app_version: str = "0.1.0"

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "fin_analyzer"

    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60

    storage_dir: str = "data/uploads"
    cors_allow_origins: List[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

