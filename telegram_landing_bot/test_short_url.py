# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:50
# Last Updated: 2025-12-18T12:12:50
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import asyncio
import pytest
import sys
import os
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tracking import init_tracking, get_tracking_manager
from config import Settings

@pytest.mark.asyncio
async def test_short_url():
    # Create a mock settings instance
    mock_settings_instance = Settings(
        bot_token="test_bot_token",
        tracker_domain="http://test-tracker.com",
        landing_url="http://test-landing.com",
        campaign_id="test_campaign_123"
    )

    # Patch the global settings instance
    with patch('tracking.settings', new=mock_settings_instance):
        print(f"Settings campaign_id: {mock_settings_instance.campaign_id}")
        await init_tracking()
        manager = get_tracking_manager()

    # Generate a short tracking URL
    result = await manager.generate_tracking_link(
        user_id=6820152910,
        source='telegram_bot',
        additional_params={
            'sub1': 'telegram_bot_start',
            'sub2': 'telegram',
            'sub3': 'callback_offer',
            'sub4': 'aaa_4441',
            'sub5': 'premium_offer'
        }
    )

    print('Generated short tracking URL:')
    print(result['tracking_url'])
    print(f'Click ID: {result["click_id"]}')

if __name__ == '__main__':
    asyncio.run(test_short_url())
