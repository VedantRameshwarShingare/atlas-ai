"""Environment identity and dotenv file selection helpers."""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

from dotenv import dotenv_values


class Environment(StrEnum):
    """Supported Atlas AI deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def current_environment() -> Environment:
    """Resolve the active environment from process variables or the base dotenv file."""
    base_values = dotenv_values(PROJECT_ROOT / ".env")
    raw_value = os.getenv("ENVIRONMENT") or base_values.get("ENVIRONMENT") or Environment.DEVELOPMENT.value
    return Environment(raw_value.lower())


def environment_files(environment: Environment | None = None) -> tuple[Path, ...]:
    """Return dotenv files in increasing precedence for the requested environment.

    Shared values load from ``.env`` first, local overrides load next, and only the
    active environment file is loaded last. This prevents test values from leaking
    into production configuration.
    """
    selected = environment or current_environment()
    files: list[Path] = [PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local"]
    if selected is Environment.TESTING:
        files.append(PROJECT_ROOT / ".env.test")
    elif selected is Environment.PRODUCTION:
        files.append(PROJECT_ROOT / ".env.production")
    return tuple(files)
