"""Custom exception classes for application configuration and runtime errors."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Raised when application configuration is invalid."""


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""


class ExternalAPIError(Exception):
    """Raised when an external API request fails."""


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""


class MemoryError(Exception):
    """Raised when memory operations fail."""


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class ConversationNotFoundError(Exception):
    """Raised when a requested conversation is unavailable to the caller."""


class ProviderConfigurationError(Exception):
    """Raised when a required AI provider configuration value is missing."""


class ProviderUnavailableError(Exception):
    """Raised when an AI provider cannot complete a request safely."""
