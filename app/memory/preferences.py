"""Preference abstraction for briefing and notification settings."""

from __future__ import annotations

from app.memory.memory_types import UserPreferencesState


class PreferencesMemory:
    """Manage user preferences without touching external services or routes."""

    def __init__(self, state: UserPreferencesState | None = None) -> None:
        self._state = state or UserPreferencesState()

    async def load(self) -> UserPreferencesState:
        """Return the current preferences state."""
        return self._state

    async def save(self, *, state: UserPreferencesState) -> UserPreferencesState:
        """Persist the preferences state."""
        self._state = state
        return self._state

    async def update(self, **kwargs: object) -> UserPreferencesState:
        """Partially update preference fields."""
        for key, value in kwargs.items():
            setattr(self._state, key, value)
        return self._state
