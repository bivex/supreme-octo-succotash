
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
Simple load test without matplotlib dependencies
"""

import asyncio
import aiohttp
import time
import statistics
from datetime import datetime


async def simple_load_test():
    """Simple load test without matplotlib dependencies"""
    print("Running simple load test with increased connection pool...")

    base_url = "http://localhost:5000"
    duration = 30  # 30 seconds for more realistic test
    workers = 10   # Increased workers to test connection pool

    results = {
        'requests': [],
        'success_count': 0,
        'fail_count': 0,
        'errors': []
    }

    async def make_request(session, worker_id, request_id):
        try:
            # Use only endpoints that work without authentication
            endpoints = [
                '/health',        # GET - no auth required
                '/events/track',  # POST - no auth required
            ]

            endpoint = endpoints[request_id % len(endpoints)]

            data = None
            method = 'GET'

            if endpoint == '/events/track':
                method = 'POST'
                data = {
                    'event_type': 'test',
                    'event_name': f'test_{worker_id}_{request_id}',
                    'user_id': f'user_{worker_id}'
                }

            url = f"{base_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}

            start_time = time.time()
            async with session.request(method, url, json=data, headers=headers) as response:
                response_time = time.time() - start_time

                result = {
                    'endpoint': endpoint,
                    'status': response.status,
                    'time': response_time,
                    'success': response.status < 400,
                    'worker_id': worker_id,
                    'request_id': request_id
                }

                results['requests'].append(result)

                if result['success']:
                    results['success_count'] += 1
                else:
                    results['fail_count'] += 1

                return result

        except Exception as e:
            error_result = {
                'endpoint': endpoint if 'endpoint' in locals() else 'unknown',
                'status': 0,
                'time': 0,
                'success': False,
                'worker_id': worker_id,
                'request_id': request_id,
                'error': str(e)
            }

            results['requests'].append(error_result)
            results['fail_count'] += 1
            results['errors'].append(str(e))

            return error_result

    async def worker(worker_id):
        request_id = 0
        async with aiohttp.ClientSession() as session:
            end_time = time.time() + duration

            while time.time() < end_time:
                await make_request(session, worker_id, request_id)
                request_id += 1

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.05)  # 50ms delay

    print(f"Starting load test: {workers} workers for {duration} seconds")

    start_time = time.time()
    tasks = [asyncio.create_task(worker(i)) for i in range(workers)]
    await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()

    # Calculate statistics
    total_requests = len(results['requests'])
    duration_actual = end_time - start_time
    rps = total_requests / duration_actual if duration_actual > 0 else 0

    response_times = [r['time'] for r in results['requests'] if r['time'] > 0]
    avg_response_time = statistics.mean(response_times) if response_times else 0
    median_response_time = statistics.median(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0

    if response_times:
        sorted_times = sorted(response_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
    else:
        p95 = p99 = 0

    success_rate = (results['success_count'] / total_requests * 100) if total_requests > 0 else 0

    # Print results
    print("\n" + "="*80)
    print("LOAD TEST RESULTS REPORT")
    print("="*80)
    print(f"Workers: {workers}")
    print(f"Duration: {duration_actual:.2f}s")
    print(f"Total Requests: {total_requests}")
    print(f"Requests Per Second: {rps:.2f}")
    print(f"Successful: {results['success_count']}")
    print(f"Failed: {results['fail_count']}")
    print(f"Success Rate: {success_rate:.2f}%")
    print()

    print("RESPONSE TIMES:")
    print(".3f")
    print(".3f")
    print(".3f")
    print(".3f")
    print(".3f")
    print(".3f")
    print()

    print("PERFORMANCE ASSESSMENT:")
    print("-" * 40)

    if success_rate >= 95:
        print("SUCCESS: EXCELLENT (>=95%)")
    elif success_rate >= 90:
        print("SUCCESS: GOOD (>=90%)")
    else:
        print("SUCCESS: POOR (<90%)")

    if p95 <= 0.5:
        print("RESPONSE TIME: EXCELLENT (P95 <= 0.5s)")
    elif p95 <= 1.0:
        print("RESPONSE TIME: GOOD (P95 <= 1.0s)")
    else:
        print("RESPONSE TIME: POOR (P95 > 1.0s)")

    if rps >= 100:
        print("THROUGHPUT: EXCELLENT (>=100 RPS)")
    elif rps >= 50:
        print("THROUGHPUT: GOOD (>=50 RPS)")
    else:
        print("THROUGHPUT: POOR (<50 RPS)")

    print()
    print("ERRORS:")
    if results['errors']:
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(results['errors']) > 5:
            print(f"  ... and {len(results['errors']) - 5} more")
    else:
        print("  None")

    print("\n" + "="*80)


async def main():
    """Main function"""
    await simple_load_test()


if __name__ == "__main__":
    asyncio.run(main())
