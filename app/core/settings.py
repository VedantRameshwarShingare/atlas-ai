"""Application settings and environment configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load runtime configuration from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = Field(default="Atlas AI", alias="PROJECT_NAME")
    project_version: str = Field(default="0.1.0", alias="PROJECT_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="ENVIRONMENT",
    )
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(default="", alias="TELEGRAM_WEBHOOK_SECRET")

    database_url: str = Field(default="sqlite:///./atlas_ai.db", alias="DATABASE_URL")
    chroma_db_path: str = Field(default="./data/embeddings", alias="CHROMA_DB_PATH")

    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
    sec_api_key: str = Field(default="", alias="SEC_API_KEY")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="UTC", alias="TIMEZONE")

    @classmethod
    def load(cls) -> "Settings":
        """Load settings and raise a descriptive error on invalid values."""
        try:
            return cls()
        except ValidationError as exc:
            raise ValueError(f"Invalid configuration: {exc}") from exc


settings = Settings.load()
