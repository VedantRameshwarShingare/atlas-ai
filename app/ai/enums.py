"""Enums for AI orchestration types and intents."""

from __future__ import annotations

from enum import StrEnum


class IntentType(StrEnum):
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
    FINANCE_QUOTE = "FINANCE_QUOTE"
    FINANCE_COMPANY = "FINANCE_COMPANY"
    FINANCE_HISTORY = "FINANCE_HISTORY"
    FINANCE_SEARCH = "FINANCE_SEARCH"
    UNKNOWN = "UNKNOWN"


class ToolType(StrEnum):
    """Supported tool categories for orchestration."""

    SEARCH = "SEARCH"
    DOCUMENT = "DOCUMENT"
    MEMORY = "MEMORY"
    WATCHLIST = "WATCHLIST"
    ALERT = "ALERT"
    MARKET = "MARKET"
    RESEARCH = "RESEARCH"
    FINANCE = "FINANCE"
    UNKNOWN = "UNKNOWN"


class ResponseType(StrEnum):
    """Supported response output formats."""

    MARKDOWN = "MARKDOWN"
    TELEGRAM = "TELEGRAM"
    SOURCES = "SOURCES"
