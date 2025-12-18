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
Advertising Platform API Python SDK

A comprehensive Python SDK for the Advertising Platform API,
generated from OpenAPI specification.

Features:
- Domain-driven design with bounded contexts
- Full type safety with Pydantic models
- Async/sync HTTP client support
- JWT and API key authentication
- Comprehensive error handling
- Built-in rate limiting awareness
"""

from .client import AdvertisingPlatformClient
from .exceptions import *
from .models import *

__version__ = "1.0.0"
__all__ = [
    "AdvertisingPlatformClient",
    # Models will be exported dynamically
]
