"""Alert management tool for monitoring events and thresholds."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class AlertService(Protocol):
    """Service interface for alert operations."""

    async def create_alert(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        """Create a new alert."""

    async def delete_alert(self, user_id: str, alert_id: str) -> dict[str, Any]:
        """Delete an alert."""

    async def enable_alert(self, user_id: str, alert_id: str) -> dict[str, Any]:
        """Enable an alert."""

    async def disable_alert(self, user_id: str, alert_id: str) -> dict[str, Any]:
        """Disable an alert."""

    async def list_alerts(self, user_id: str) -> list[dict[str, Any]]:
        """List alerts for a user."""


class AlertsTool(BaseTool):
    """Manage alert subscriptions for a user."""

    name = "alerts"
    description = "Creates, updates, enables, disables, and lists alerts"
    supported_intents = (IntentType.ALERT,)

    def __init__(self, service: AlertService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Dispatch alert actions based on the requested operation."""
        action = kwargs.get("action", "list")
        user_id = kwargs.get("user_id", "")

        if action == "create":
            data = await self._service.create_alert(user_id, **kwargs)
        elif action == "delete":
            data = await self._service.delete_alert(user_id, kwargs.get("alert_id", ""))
        elif action == "enable":
            data = await self._service.enable_alert(user_id, kwargs.get("alert_id", ""))
        elif action == "disable":
            data = await self._service.disable_alert(user_id, kwargs.get("alert_id", ""))
        else:
            data = await self._service.list_alerts(user_id)

        return ToolResult(success=True, tool_name=self.name, data={"action": action, "result": data})
