"""Global application constants used by the configuration layer."""

from __future__ import annotations

APPLICATION_NAME: str = "Atlas AI"
APPLICATION_VERSION: str = "0.1.0"
DEFAULT_TIMEZONE: str = "UTC"
DEFAULT_LANGUAGE: str = "en"
SUPPORTED_FILE_TYPES: tuple[str, ...] = (".pdf", ".txt", ".md", ".csv")
MAX_UPLOAD_SIZE_MB: int = 25
CHUNK_SIZE: int = 1000
EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
