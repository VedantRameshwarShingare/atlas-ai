"""Onboarding state for Telegram sessions."""

from __future__ import annotations


class OnboardingState:
    """Track conversational onboarding progress without inline menus."""

    def __init__(self) -> None:
        self._step = 0

    async def handle_message(self, message: str) -> str:
        """Advance onboarding with a simple conversational flow."""
        if self._step == 0:
            self._step = 1
            return "Welcome to Atlas AI. Tell me what you want to explore today."
        return f"Thanks. I received: {message}"
