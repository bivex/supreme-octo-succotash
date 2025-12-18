# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

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
