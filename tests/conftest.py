# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
Test configuration and fixtures for Advertising Platform SDK tests.
"""

import pytest
from advertising_platform_sdk.client import AdvertisingPlatformClient


@pytest.fixture(scope="session")
def test_client():
    """Create a test client with mock configuration."""
    return AdvertisingPlatformClient(
        base_url="https://api.test.example.com/v1",
        bearer_token="test-bearer-token",
        timeout=5.0,
    )


@pytest.fixture(scope="session")
def test_client_api_key():
    """Create a test client with API key authentication."""
    return AdvertisingPlatformClient(
        base_url="https://api.test.example.com/v1",
        api_key="test-api-key",
        timeout=5.0,
    )