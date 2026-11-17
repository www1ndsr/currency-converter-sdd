"""Shared error types for the Currency Converter application."""

from typing import Optional


class CurrencyConverterError(Exception):
    """Base exception for all Currency Converter domain and infrastructure errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ValidationError(CurrencyConverterError):
    """Raised when an entered currency amount or input parameter is invalid."""
    pass


class NetworkError(CurrencyConverterError):
    """Raised when an external HTTP request to BNM fails, times out, or returns a non-200 status."""
    pass


class EmptyDateError(CurrencyConverterError):
    """Raised when BNM returns an empty body or valid XML with no rate records for a date."""
    pass


class RateParsingError(CurrencyConverterError):
    """Raised when BNM XML is malformed, missing required elements, or contains invalid rate records."""
    pass


class CurrencyUnavailableError(CurrencyConverterError):
    """Raised when a selected currency is not available in the loaded rate set."""
    pass


class CacheError(CurrencyConverterError):
    """Raised when reading or writing local cache data fails or cache data is corrupted."""
    pass
