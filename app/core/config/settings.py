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
    DEFAULT_PORT,
    DEFAULT_SCHEDULER_TIMEZONE,
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
    """LLM provider configuration."""

    api_key: SecretStr | None = None
    model: str = "openai/gpt-oss-20b"
    base_url: str = "https://api.groq.com/openai/v1"


class HuggingFaceSettings(BaseModel):
    """Hugging Face inference configuration."""

    api_key: SecretStr | None = None
    embedding_model: str = "BAAI/bge-small-en-v1.5"


class TelegramSettings(BaseModel):
    """Telegram integration configuration; values are intentionally optional."""

    bot_token: SecretStr | None = None
    webhook_secret: SecretStr | None = None
    request_timeout_seconds: float = Field(default=10.0, gt=0.1, le=60.0)


class FinanceAPISettings(BaseModel):
    """Credentials for financial-data providers."""

    finnhub_api_key: SecretStr | None = None
    yahoo_enabled: bool = True
    sec_user_agent: str | None = None
    request_timeout_seconds: float = Field(default=10.0, gt=0.1, le=60.0)


class LoggingSettings(BaseModel):
    """Application logging configuration."""

    level: str = DEFAULT_LOG_LEVEL
    json_logs: bool = False


class SchedulerSettings(BaseModel):
    """Background scheduler configuration."""

    enabled: bool = True
    timezone: str = DEFAULT_SCHEDULER_TIMEZONE


class AuthSettings(BaseModel):
    """Authentication and JWT configuration."""

    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


class ChatSettings(BaseModel):
    """Chat orchestration limits that protect LLM context size."""

    history_limit: int = Field(default=20, ge=1, le=100)


class DocumentSettings(BaseModel):
    """Workspace document upload and ingestion constraints."""

    storage_directory: str = "data/uploads/documents"
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    allowed_extensions: list[str] = Field(default_factory=lambda: [".pdf", ".txt", ".docx"])
    allowed_content_types: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
    )


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
    huggingface: HuggingFaceSettings = Field(default_factory=HuggingFaceSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    finance: FinanceAPISettings = Field(default_factory=FinanceAPISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    chat: ChatSettings = Field(default_factory=ChatSettings)
    documents: DocumentSettings = Field(default_factory=DocumentSettings)


settings = Settings()
