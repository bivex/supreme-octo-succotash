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
from .models import *
from .exceptions import *

__version__ = "1.0.0"
__all__ = [
    "AdvertisingPlatformClient",
    # Models will be exported dynamically
]