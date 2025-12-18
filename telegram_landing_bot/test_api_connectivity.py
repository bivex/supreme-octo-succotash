
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:51
# Last Updated: 2025-12-18T12:12:51
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Test script to verify API connectivity for tracking system."""

import asyncio
import pytest
import os
import sys
import json
from tracking import TrackingManager

@pytest.mark.asyncio
async def test_api_connectivity():
    """Test that the tracking system can connect to the API."""
    print("Testing API connectivity...")

    # Create tracking manager
    manager = TrackingManager()

    # Initialize session
    async with manager:
        try:
            # Test the API endpoint directly
            payload = {
                "base_url": manager.api_base_url,
                "campaign_id": 9061,
                "tracking_params": {
                    "click_id": "test123",
                    "source": "test",
                    "sub1": "test",
                    "sub2": "telegram",
                    "sub3": "callback_offer",
                    "sub4": "test_user",
                    "sub5": "premium_offer",
                    "user_id": 123456,
                    "bot_source": "telegram",
                    "generated_at": 1234567890
                }
            }

            print(f"API Base URL: {manager.api_base_url}")
            print(f"Full endpoint URL: {manager.api_base_url}/clicks/generate")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            # Make the request
            url = f"{manager.api_base_url}/clicks/generate"
            async with manager.session.post(url, json=payload) as response:
                print(f"Response status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print("SUCCESS: API call successful!")
                    print(f"Response: {json.dumps(result, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"ERROR: API call failed with status {response.status}: {error_text}")
                    return False

        except Exception as e:
            print(f"ERROR: Exception during API call: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_api_connectivity())
    sys.exit(0 if success else 1)