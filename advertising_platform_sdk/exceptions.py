"""
Advertising Platform API Exceptions

Custom exceptions for the Advertising Platform API client.
"""


class AdvertisingPlatformError(Exception):
    """Base exception for Advertising Platform API errors."""
    pass


class APIConnectionError(AdvertisingPlatformError):
    """Raised when there's a connection error with the API."""
    pass


class APIError(AdvertisingPlatformError):
    """Raised for general API errors."""
    pass


class AuthenticationError(AdvertisingPlatformError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(AdvertisingPlatformError):
    """Raised when authorization fails (insufficient permissions)."""
    pass


class ValidationError(AdvertisingPlatformError):
    """Raised when request validation fails."""
    pass


class NotFoundError(AdvertisingPlatformError):
    """Raised when a requested resource is not found."""
    pass


class ConflictError(AdvertisingPlatformError):
    """Raised when there's a resource conflict."""
    pass


class RateLimitError(AdvertisingPlatformError):
    """Raised when rate limit is exceeded."""
    pass


class ServerError(AdvertisingPlatformError):
    """Raised for server-side errors."""
    pass