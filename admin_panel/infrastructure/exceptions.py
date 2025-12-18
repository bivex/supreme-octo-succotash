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
Infrastructure Exceptions

Technical errors related to external systems and infrastructure.
"""

from typing import Optional


class InfrastructureException(Exception):
    """Base exception for infrastructure-related errors."""
    pass


class APIException(InfrastructureException):
    """Raised when API operations fail."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[str] = None):
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NetworkException(APIException):
    """Raised when network-related errors occur."""
    pass


class ConfigurationException(InfrastructureException):
    """Raised when configuration is invalid or missing."""
    pass


class RepositoryException(InfrastructureException):
    """Raised when repository operations fail."""
    pass