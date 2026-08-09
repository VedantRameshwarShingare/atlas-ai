"""Finance-domain exceptions and provider error normalization."""

from __future__ import annotations


class FinanceError(Exception):
    """Base finance-domain error."""


class FinanceValidationError(FinanceError):
    """Raised when client-provided finance input is invalid."""


class FinanceNotFoundError(FinanceError):
    """Raised when requested finance resources are unavailable."""


class FinanceRateLimitError(FinanceError):
    """Raised when a provider rate limit is reached."""


class FinanceProviderUnavailableError(FinanceError):
    """Raised when a provider is unavailable or timed out."""


class FinanceConfigurationError(FinanceError):
    """Raised when required finance configuration is missing."""
