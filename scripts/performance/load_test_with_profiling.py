
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
Load testing script with performance profiling for supreme-octo-succotash API
"""

import asyncio
import aiohttp
import cProfile
import pstats
import io
import time
import statistics
import json
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Any
try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class LoadTestProfiler:
    """Load testing with performance profiling"""

    def __init__(self, base_url: str = "http://localhost:5000", duration: int = 60):
        self.base_url = base_url.rstrip('/')
        self.duration = duration  # seconds
        self.results = {
            'requests': [],
            'errors': [],
            'response_times': [],
            'cpu_usage': [],
            'memory_usage': [],
            'threads_created': [],
            'start_time': None,
            'end_time': None
        }

        # Test data
        self.test_click_data = {
            "campaign_id": "camp_test_load",
            "ip_address": "192.168.1.100",
            "user_agent": "LoadTest/1.0",
            "referrer": "https://test-referrer.com"
        }

        self.test_event_data = {
            "event_type": "page_view",
            "event_name": "load_test_page_view",
            "user_id": "load_test_user",
            "campaign_id": "camp_test_load",
            "url": "https://test-page.com",
            "user_agent": "LoadTest/1.0",
            "ip_address": "192.168.1.100"
        }

        self.test_conversion_data = {
            "click_id": "load_test_click_123",
            "conversion_type": "sale",
            "amount": 99.99,
            "currency": "USD",
            "goal_id": "goal_test",
            "metadata": {
                "order_id": "order_load_test",
                "product_ids": ["prod_1", "prod_2"]
            }
        }

    async def single_request(self, session: aiohttp.ClientSession, endpoint: str,
                           method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
        """Make single HTTP request and measure response time"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}

            if method.upper() == 'GET':
                async with session.get(url, headers=headers) as response:
                    result = {
                        'method': method,
                        'endpoint': endpoint,
                        'status_code': response.status,
                        'response_time': time.time() - start_time,
                        'success': response.status < 400,
                        'error': None
                    }
            elif method.upper() == 'POST':
                async with session.post(url, json=data, headers=headers) as response:
                    result = {
                        'method': method,
                        'endpoint': endpoint,
                        'status_code': response.status,
                        'response_time': time.time() - start_time,
                        'success': response.status < 400,
                        'error': None
                    }
            else:
                result = {
                    'method': method,
                    'endpoint': endpoint,
                    'status_code': 0,
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': f'Unsupported method: {method}'
                }

        except Exception as e:
            result = {
                'method': method,
                'endpoint': endpoint,
                'status_code': 0,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }

        return result

    async def load_worker(self, worker_id: int, requests_per_second: int):
        """Worker function for load testing"""
        print(f"Worker {worker_id} started (target: {requests_per_second} req/sec)")

        async with aiohttp.ClientSession() as session:
            # Calculate delay between requests
            delay = 1.0 / requests_per_second if requests_per_second > 0 else 0

            while time.time() < self.results['end_time']:
                # Mix of different request types
                request_type = worker_id % 4

                if request_type == 0:
                    # Create click
                    result = await self.single_request(session, '/clicks', 'POST', self.test_click_data)
                    if result['success'] and 'click_id' in result:
                        # Update conversion data with real click_id for next requests
                        self.test_conversion_data['click_id'] = result.get('click_id', 'load_test_click_123')

                elif request_type == 1:
                    # Track event
                    result = await self.single_request(session, '/events/track', 'POST', self.test_event_data)

                elif request_type == 2:
                    # Track conversion
                    result = await self.single_request(session, '/conversions/track', 'POST', self.test_conversion_data)

                elif request_type == 3:
                    # Get campaigns (read operation)
                    result = await self.single_request(session, '/v1/campaigns', 'GET')

                self.results['requests'].append(result)

                if not result['success']:
                    self.results['errors'].append(result)

                if delay > 0:
                    await asyncio.sleep(delay)

        print(f"Worker {worker_id} finished")

    def monitor_system_resources(self):
        """Monitor system resources during load test"""
        while time.time() < self.results['end_time']:
            self.results['cpu_usage'].append(psutil.cpu_percent(interval=1))
            self.results['memory_usage'].append(psutil.virtual_memory().percent)
            self.results['threads_created'].append(threading.active_count())

    async def run_load_test(self, num_workers: int = 10, requests_per_second: int = 50):
        """Run load test with multiple workers"""
        print(f"=== Starting Load Test ===")
        print(f"Duration: {self.duration} seconds")
        print(f"Workers: {num_workers}")
        print(f"Target RPS: {requests_per_second * num_workers} total")
        print(f"Target RPS per worker: {requests_per_second}")
        print()

        self.results['start_time'] = time.time()
        self.results['end_time'] = self.results['start_time'] + self.duration

        # Start system monitoring in background thread
        monitor_thread = threading.Thread(target=self.monitor_system_resources, daemon=True)
        monitor_thread.start()

        # Create worker tasks
        tasks = []
        for i in range(num_workers):
            task = asyncio.create_task(self.load_worker(i, requests_per_second))
            tasks.append(task)

        # Run all workers
        start_time = time.time()
        await asyncio.gather(*tasks, return_exceptions=True)
        actual_duration = time.time() - start_time

        self.results['actual_duration'] = actual_duration

        return self.analyze_results()

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze load test results"""
        total_requests = len(self.results['requests'])
        successful_requests = len([r for r in self.results['requests'] if r['success']])
        failed_requests = len(self.results['errors'])

        if self.results['requests']:
            response_times = [r['response_time'] for r in self.results['requests']]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            if HAS_MATPLOTLIB and response_times:
                p95_response_time = np.percentile(response_times, 95)
                p99_response_time = np.percentile(response_times, 99)
            else:
                # Fallback using statistics
                sorted_times = sorted(response_times)
                n = len(sorted_times)
                if n > 0:
                    p95_idx = int(0.95 * (n - 1))
                    p99_idx = int(0.99 * (n - 1))
                    p95_response_time = sorted_times[min(p95_idx, n - 1)]
                    p99_response_time = sorted_times[min(p99_idx, n - 1)]
                else:
                    p95_response_time = p99_response_time = 0

            # Calculate actual RPS
            actual_duration = self.results.get('actual_duration', self.duration)
            actual_rps = total_requests / actual_duration if actual_duration > 0 else 0
        else:
            response_times = []
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
            actual_rps = 0

        # System resource analysis
        avg_cpu = statistics.mean(self.results['cpu_usage']) if self.results['cpu_usage'] else 0
        max_cpu = max(self.results['cpu_usage']) if self.results['cpu_usage'] else 0
        avg_memory = statistics.mean(self.results['memory_usage']) if self.results['memory_usage'] else 0
        max_memory = max(self.results['memory_usage']) if self.results['memory_usage'] else 0

        # Error analysis
        error_types = {}
        for error in self.results['errors']:
            error_type = error.get('error', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1

        analysis = {
            'summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                'actual_rps': actual_rps,
                'test_duration': actual_duration
            },
            'response_times': {
                'avg': avg_response_time,
                'median': median_response_time,
                'min': min_response_time,
                'max': max_response_time,
                'p95': p95_response_time,
                'p99': p99_response_time
            },
            'system_resources': {
                'avg_cpu_percent': avg_cpu,
                'max_cpu_percent': max_cpu,
                'avg_memory_percent': avg_memory,
                'max_memory_percent': max_memory
            },
            'errors': {
                'error_count': failed_requests,
                'error_types': error_types
            }
        }

        return analysis

    def generate_report(self, analysis: Dict[str, Any], profile_stats=None):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("LOAD TEST RESULTS REPORT")
        print("="*80)

        summary = analysis['summary']
        response_times = analysis['response_times']
        resources = analysis['system_resources']
        errors = analysis['errors']

        print("\nSUMMARY:")
        print(f"  Total Requests: {summary['total_requests']:,}")
        print(f"  Successful: {summary['successful_requests']:,}")
        print(f"  Failed: {summary['failed_requests']:,}")
        print(f"  Success Rate: {summary['success_rate']:.2f}%")
        print(f"  Actual RPS: {summary['actual_rps']:.2f}")
        print(f"  Test Duration: {summary['test_duration']:.2f}s")

        print("\nRESPONSE TIMES:")
        print(f"  Average: {response_times['avg']:.3f}s")
        print(f"  Median: {response_times['median']:.3f}s")
        print(f"  Min: {response_times['min']:.3f}s")
        print(f"  Max: {response_times['max']:.3f}s")
        print(f"  95th percentile: {response_times['p95']:.3f}s")
        print(f"  99th percentile: {response_times['p99']:.3f}s")

        print("\nSYSTEM RESOURCES:")
        print(f"  CPU Usage - Avg: {resources['avg_cpu_percent']:.1f}%, Max: {resources['max_cpu_percent']:.1f}%")
        print(f"  Memory Usage - Avg: {resources['avg_memory_percent']:.1f}%, Max: {resources['max_memory_percent']:.1f}%")

        if errors['error_count'] > 0:
            print("\nERRORS:")
            for error_type, count in errors['error_types'].items():
                print(f"  {error_type}: {count}")

        if profile_stats:
            print("\nPROFILING RESULTS:")
            print("  Top 10 most time-consuming functions:")
            profile_stats.sort_stats('cumulative').print_stats(10)

        print("\n" + "="*80)

        # Performance assessment
        self.assess_performance(analysis)

    def assess_performance(self, analysis: Dict[str, Any]):
        """Assess overall performance"""
        summary = analysis['summary']
        response_times = analysis['response_times']

        print("PERFORMANCE ASSESSMENT:")
        print("-" * 40)

        # Success rate assessment
        if summary['success_rate'] >= 99:
            print("✅ Success Rate: EXCELLENT (≥99%)")
        elif summary['success_rate'] >= 95:
            print("✅ Success Rate: GOOD (≥95%)")
        elif summary['success_rate'] >= 90:
            print("⚠️  Success Rate: ACCEPTABLE (≥90%)")
        else:
            print("❌ Success Rate: POOR (<90%)")

        # Response time assessment
        if response_times['p95'] <= 0.5:
            print("✅ Response Time: EXCELLENT (P95 ≤ 0.5s)")
        elif response_times['p95'] <= 1.0:
            print("✅ Response Time: GOOD (P95 ≤ 1.0s)")
        elif response_times['p95'] <= 2.0:
            print("⚠️  Response Time: ACCEPTABLE (P95 ≤ 2.0s)")
        else:
            print("❌ Response Time: POOR (P95 > 2.0s)")

        # RPS assessment (rough estimates)
        if summary['actual_rps'] >= 1000:
            print("✅ Throughput: EXCELLENT (≥1000 RPS)")
        elif summary['actual_rps'] >= 500:
            print("✅ Throughput: GOOD (≥500 RPS)")
        elif summary['actual_rps'] >= 100:
            print("⚠️  Throughput: ACCEPTABLE (≥100 RPS)")
        else:
            print("❌ Throughput: POOR (<100 RPS)")


async def main():
    """Main function to run load test with profiling"""

    # Configuration
    BASE_URL = "http://localhost:5000"
    TEST_DURATION = 30  # seconds
    NUM_WORKERS = 5     # concurrent workers
    RPS_PER_WORKER = 10 # requests per second per worker

    print("[START] Starting Load Test with Profiling")
    print(f"Target: {BASE_URL}")
    print(f"Duration: {TEST_DURATION}s")
    print(f"Workers: {NUM_WORKERS}")
    print(f"Total Target RPS: {NUM_WORKERS * RPS_PER_WORKER}")
    print()

    # Initialize profiler
    profiler = LoadTestProfiler(BASE_URL, TEST_DURATION)

    # Start profiling
    print("[DATA] Starting profiling...")
    pr = cProfile.Profile()
    pr.enable()

    try:
        # Run load test
        analysis = await profiler.run_load_test(NUM_WORKERS, RPS_PER_WORKER)

        # Stop profiling
        pr.disable()

        # Process profiling data
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()

        # Generate report
        profiler.generate_report(analysis, ps)

    except Exception as e:
        print(f"❌ Load test failed: {e}")
        pr.disable()


if __name__ == "__main__":
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding. Please start the server first.")
            exit(1)
    except:
        print("❌ Cannot connect to server. Please start the server first.")
        print("   Run: python main_clean.py")
        exit(1)

    # Run load test
    asyncio.run(main())
