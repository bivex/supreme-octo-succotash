import asyncio
from tracking import init_tracking, get_tracking_manager

class MockSettings:
    bot_token: str = "test_bot_token"
    tracker_domain: str = "http://test-tracker.com"
    landing_url: str = "http://test-landing.com"
    campaign_id: int = 12345

settings = MockSettings()


async def test_short_url():
    print(f"Settings campaign_id: {settings.campaign_id}")
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
