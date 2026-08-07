"""Typed, sectioned application settings loaded through pydantic-settings."""

from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.constants import (
    DEFAULT_APPLICATION_NAME,
    DEFAULT_APPLICATION_VERSION,
    DEFAULT_DATABASE_URL,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_PORT,
    DEFAULT_SCHEDULER_TIMEZONE,
    DEFAULT_TIMEZONE,
)
from app.core.config.environment import Environment, environment_files


class ApplicationSettings(BaseModel):
    """Identity and runtime-mode settings for Atlas AI."""

    name: str = DEFAULT_APPLICATION_NAME
    version: str = DEFAULT_APPLICATION_VERSION
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False


class ServerSettings(BaseModel):
    """HTTP server bind settings."""

    host: str = DEFAULT_HOST
    port: int = Field(default=DEFAULT_PORT, ge=1, le=65535)


class DatabaseSettings(BaseModel):
    """Database connection configuration."""

    url: str = DEFAULT_DATABASE_URL
    echo: bool = False


class OpenAISettings(BaseModel):
    """OpenAI integration configuration; values are intentionally optional."""

    api_key: SecretStr | None = None
    model: str = DEFAULT_OPENAI_MODEL


class TelegramSettings(BaseModel):
    """Telegram integration configuration; values are intentionally optional."""

    bot_token: SecretStr | None = None
    webhook_secret: SecretStr | None = None


class FinanceAPISettings(BaseModel):
    """Credentials for financial-data providers."""

    finnhub_api_key: SecretStr | None = None
    yahoo_enabled: bool = True
    sec_api_key: SecretStr | None = None


class LoggingSettings(BaseModel):
    """Application logging configuration."""

    level: str = DEFAULT_LOG_LEVEL
    json_logs: bool = False


class SchedulerSettings(BaseModel):
    """Background scheduler configuration."""

    enabled: bool = True
    timezone: str = DEFAULT_SCHEDULER_TIMEZONE


class Settings(BaseSettings):
    """Atlas AI settings composed from environment variables and dotenv files.

    Nested variables use a double underscore, for example ``SERVER__PORT=9000``
    and ``OPENAI__API_KEY=...``. Environment variables override dotenv values.
    """

    model_config = SettingsConfigDict(
        env_file=environment_files(),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    finance: FinanceAPISettings = Field(default_factory=FinanceAPISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)


settings = Settings()
