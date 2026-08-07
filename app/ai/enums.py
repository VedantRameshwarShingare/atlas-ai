"""Enums for AI orchestration types and intents."""

from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    """Supported intents for request routing."""

    CHAT = "CHAT"
    COMPANY_RESEARCH = "COMPANY_RESEARCH"
    MARKET_NEWS = "MARKET_NEWS"
    DOCUMENT_SUMMARY = "DOCUMENT_SUMMARY"
    DOCUMENT_QA = "DOCUMENT_QA"
    WATCHLIST = "WATCHLIST"
    ALERT = "ALERT"
    MEETING_PREP = "MEETING_PREP"
    MORNING_BRIEF = "MORNING_BRIEF"
    SEARCH = "SEARCH"
    UNKNOWN = "UNKNOWN"


class ToolType(str, Enum):
    """Supported tool categories for orchestration."""

    SEARCH = "SEARCH"
    DOCUMENT = "DOCUMENT"
    MEMORY = "MEMORY"
    WATCHLIST = "WATCHLIST"
    ALERT = "ALERT"
    MARKET = "MARKET"
    RESEARCH = "RESEARCH"
    UNKNOWN = "UNKNOWN"


class ResponseType(str, Enum):
    """Supported response output formats."""

    MARKDOWN = "MARKDOWN"
    TELEGRAM = "TELEGRAM"
    SOURCES = "SOURCES"
