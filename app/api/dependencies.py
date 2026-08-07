"""Typed dependency placeholders for the FastAPI bootstrap."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, settings


def get_settings() -> Settings:
    """Provide the immutable application settings singleton to routes."""
    return settings


SettingsDependency = Annotated[Settings, Depends(get_settings)]
