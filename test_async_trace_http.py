
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:50
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Test script to demonstrate async-trace in action with HTTP requests.
This script makes HTTP requests to the server to show the full async call stack.
"""

import asyncio
import pytest
import aiohttp
import time
import sys

@pytest.mark.asyncio
async def test_campaign_creation():
    """Test creating a campaign to see the async trace in action."""
    print("🌐 Testing campaign creation with async-trace...")

    campaign_data = {
        "name": "Test Campaign Async Trace",
        "description": "Testing async-trace integration",
        "costModel": "CPA",
        "payout": {"amount": 1.50, "currency": "USD"}
    }

    try:
        async with aiohttp.ClientSession() as session:
            print("📤 Sending POST request to create campaign...")
            async with session.post(
                'http://localhost:8000/v1/campaigns',
                json=campaign_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                print(f"📥 Response status: {response.status}")
                if response.status == 201:
                    result = await response.json()
                    print(f"✅ Campaign created: {result.get('id', 'unknown')}")
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")

    except aiohttp.ClientConnectorError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running with: python main_clean.py --async-trace")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

@pytest.mark.asyncio
async def test_campaign_offer_creation():
    """Test creating an offer for a campaign."""
    print("\n🎯 Testing campaign offer creation...")

    # First, we need to get a campaign ID. For demo, we'll try with a placeholder
    campaign_id = "test-campaign-id"

    offer_data = {
        "name": "Test Offer Async Trace",
        "url": "https://example.com/landing",
        "offerType": "direct",
        "weight": 100,
        "isActive": True,
        "isControl": False,
        "payout": {"amount": 2.00, "currency": "USD"},
        "revenueShare": 0.0
    }

    try:
        async with aiohttp.ClientSession() as session:
            print(f"📤 Sending POST request to create offer for campaign {campaign_id}...")
            async with session.post(
                f'http://localhost:8000/v1/campaigns/{campaign_id}/offers',
                json=offer_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                print(f"📥 Response status: {response.status}")
                if response.status in [201, 400, 404]:  # 400/404 are expected for test
                    try:
                        result = await response.json()
                        print(f"📄 Response: {result}")
                    except:
                        text = await response.text()
                        print(f"📄 Response: {text}")
                else:
                    error_text = await response.text()
                    print(f"❌ Unexpected error: {error_text}")

    except aiohttp.ClientConnectorError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running with: python main_clean.py --async-trace")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

@pytest.mark.asyncio
async def test_multiple_requests():
    """Test multiple concurrent requests to see task traces."""
    print("\n🔄 Testing multiple concurrent requests...")

    async def make_request(request_id):
        """Make a single request."""
        try:
            async with aiohttp.ClientSession() as session:
                # Simple health check request
                async with session.get('http://localhost:8000/health') as response:
                    return f"Request {request_id}: status {response.status}"
        except Exception as e:
            return f"Request {request_id}: error {e}"

    # Make 5 concurrent requests
    print("🚀 Making 5 concurrent requests...")
    tasks = [make_request(i) for i in range(1, 6)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        print(f"📊 {result}")

async def simulate_server_processing():
    """Simulate server request processing with async-trace."""
    print("🎭 Simulating server request processing with async-trace...")

    async def simulate_http_request_handler(endpoint: str):
        """Simulate an HTTP request handler with async-trace."""
        from src.utils.async_debug import debug_http_request, debug_database_call, debug_before_await, debug_after_await

        debug_http_request(f"POST {endpoint}")

        # Simulate request validation
        await asyncio.sleep(0.01)

        # Simulate database call
        debug_before_await("campaign database save")
        await asyncio.sleep(0.1)  # Simulate DB latency
        debug_after_await("campaign database save")

        # Simulate response
        await asyncio.sleep(0.01)

        return {"status": "success", "endpoint": endpoint}

    async def simulate_concurrent_requests():
        """Simulate multiple concurrent requests."""
        print("🔄 Simulating 3 concurrent HTTP requests...")

        endpoints = ["/campaigns", "/campaigns/123/offers", "/analytics"]
        tasks = []

        for i, endpoint in enumerate(endpoints):
            task = asyncio.create_task(simulate_http_request_handler(endpoint))
            tasks.append(task)
            from src.utils.async_debug import debug_task_creation
            debug_task_creation()

        results = await asyncio.gather(*tasks)
        print("📊 All requests completed:")
        for result in results:
            print(f"  ✅ {result}")

    await simulate_concurrent_requests()

async def main():
    """Main test function."""
    print("🎭 Async-Trace Demonstration")
    print("=" * 50)

    print("🚀 This demo shows async-trace working in a simulated server environment")
    print("🔍 You'll see the complete async call stacks for each operation!")
    print()

    # Give user time to see instructions
    await asyncio.sleep(1)

    # Simulate server processing
    await simulate_server_processing()

    print("\n🎉 Demo completed!")
    print("\n💡 To see this in action with real HTTP requests:")
    print("   1. Start server: python main_clean.py --async-trace")
    print("   2. Run: python test_async_trace_http.py")
    print("   3. Watch server logs for detailed async call stacks!")
    print("\n📖 Read ASYNC_TRACE_README.md for complete usage guide")

if __name__ == "__main__":
    asyncio.run(main())
