#!/usr/bin/env python3
"""
Simple profiling script without matplotlib dependencies
"""

import cProfile
import pstats
import io
import asyncio
import aiohttp
import time
import statistics


async def simple_load_test():
    """Simple load test without matplotlib dependencies"""
    print("Running simple load test...")

    base_url = "http://localhost:5000"
    duration = 10  # 10 seconds for quick test

    async def make_request(session, endpoint, method='GET', data=None):
        try:
            url = f"{base_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}

            start_time = time.time()
            async with session.request(method, url, json=data, headers=headers) as response:
                response_time = time.time() - start_time
                return {
                    'endpoint': endpoint,
                    'status': response.status,
                    'time': response_time,
                    'success': response.status < 400
                }
        except Exception as e:
            return {
                'endpoint': endpoint,
                'status': 0,
                'time': 0,
                'success': False,
                'error': str(e)
            }

    async def worker(worker_id):
        async with aiohttp.ClientSession() as session:
            end_time = time.time() + duration

            while time.time() < end_time:
                # Make different types of requests
                await make_request(session, '/health')
                await make_request(session, '/v1/campaigns')
                await make_request(session, '/events/track', 'POST', {
                    'event_type': 'test',
                    'event_name': f'test_{worker_id}',
                    'user_id': f'user_{worker_id}'
                })

                await asyncio.sleep(0.1)  # Small delay

    # Run 3 workers for 10 seconds
    tasks = [asyncio.create_task(worker(i)) for i in range(3)]
    await asyncio.gather(*tasks, return_exceptions=True)

    print("Simple load test completed")


def main():
    """Main profiling function"""
    print("Starting profiling...")

    # Profile the async load test
    profiler = cProfile.Profile()
    profiler.enable()

    # Run the load test
    asyncio.run(simple_load_test())

    profiler.disable()

    # Save stats
    stats = pstats.Stats(profiler)
    stats.dump_stats('simple_profile.pstat')

    print("Profiling data saved to simple_profile.pstat")

    # Print top 20 functions
    print("\nTop 20 most time-consuming functions:")
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative').print_stats(20)
    print(s.getvalue())


if __name__ == "__main__":
    main()
