import asyncio
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tracking import init_tracking, get_tracking_manager
from unittest.mock import patch, MagicMock
from config import Settings

@pytest.mark.asyncio
async def test_bot_url_generation():
    # Create a mock settings instance using the bot's Settings class
    mock_settings_instance = Settings(
        bot_token="test_bot_token",
        tracker_domain="http://test-tracker.com",
        landing_url="http://test-landing.com",
        campaign_id="test_campaign_123"
    )

    # Patch the global settings instance
    with patch('tracking.settings', new=mock_settings_instance):
        await init_tracking()
        manager = get_tracking_manager()

    # Simulate what happens when user clicks 'get offer'
    result = await manager.generate_tracking_link(
        user_id=6820152910,
        source='telegram_bot_start',
        additional_params={
            'sub1': 'telegram_bot_start',
            'sub2': 'telegram',
            'sub3': 'callback_offer',
            'sub4': 'aaa_4441',
            'sub5': 'premium_offer'
        }
    )

    print('Bot-generated short tracking URL:')
    print(result['tracking_url'])
    print(f'Click ID: {result["click_id"]}')

if __name__ == '__main__':
    asyncio.run(test_bot_url_generation())
