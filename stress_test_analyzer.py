#!/usr/bin/env python3
"""
Advanced stress testing and performance analysis for supreme-octo-succotash
"""

import asyncio
import aiohttp
import time
import statistics
import json
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import gc


class StressTestAnalyzer:
    """Advanced stress testing with detailed performance analysis"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.results_history = []

        # Test scenarios
        self.scenarios = {
            'light_load': {'workers': 2, 'rps_per_worker': 5, 'duration': 30},
            'medium_load': {'workers': 5, 'rps_per_worker': 10, 'duration': 60},
            'heavy_load': {'workers': 10, 'rps_per_worker': 20, 'duration': 60},
            'extreme_load': {'workers': 20, 'rps_per_worker': 50, 'duration': 30}
        }

    async def run_scenario_test(self, scenario_name: str) -> Dict[str, Any]:
        """Run specific test scenario"""
        config = self.scenarios[scenario_name]
        print(f"\n🧪 Running {scenario_name.upper()} scenario...")
        print(f"   Workers: {config['workers']}")
        print(f"   RPS per worker: {config['rps_per_worker']}")
        print(f"   Duration: {config['duration']}s")
        print(f"   Total target RPS: {config['workers'] * config['rps_per_worker']}")

        # Run test
        profiler = LoadProfiler(self.base_url, config['duration'])
        analysis = await profiler.run_load_test(config['workers'], config['rps_per_worker'])

        # Add scenario info
        analysis['scenario'] = scenario_name
        analysis['config'] = config

        self.results_history.append(analysis)
        return analysis

    def run_comprehensive_test_suite(self):
        """Run all test scenarios"""
        print("🚀 STARTING COMPREHENSIVE STRESS TEST SUITE")
        print("=" * 60)

        results = {}
        for scenario in ['light_load', 'medium_load', 'heavy_load']:
            try:
                # Run in new event loop for each scenario
                analysis = asyncio.run(self.run_scenario_test(scenario))
                results[scenario] = analysis

                # Brief pause between tests
                time.sleep(5)

            except Exception as e:
                print(f"❌ Failed to run {scenario}: {e}")
                results[scenario] = {'error': str(e)}

        self.generate_comprehensive_report(results)
        return results

    def generate_comprehensive_report(self, results: Dict[str, Any]):
        """Generate comprehensive performance report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE STRESS TEST REPORT")
        print("="*80)

        # Summary table
        print("
SCENARIO COMPARISON:"        print("<12")
        print("-" * 65)

        for scenario, data in results.items():
            if 'error' in data:
                print("<12")
                continue

            summary = data['summary']
            response_times = data['response_times']

            print("<12")

        print("\n" + "="*80)

        # Performance trends
        self.analyze_performance_trends(results)

        # Recommendations
        self.generate_recommendations(results)

    def analyze_performance_trends(self, results: Dict[str, Any]):
        """Analyze performance trends across scenarios"""
        print("PERFORMANCE TRENDS ANALYSIS:")
        print("-" * 40)

        scenarios = ['light_load', 'medium_load', 'heavy_load']
        rps_values = []
        response_times = []
        success_rates = []

        for scenario in scenarios:
            if scenario in results and 'error' not in results[scenario]:
                data = results[scenario]
                rps_values.append(data['summary']['actual_rps'])
                response_times.append(data['response_times']['p95'])
                success_rates.append(data['summary']['success_rate'])

        if len(rps_values) >= 2:
            rps_trend = (rps_values[-1] - rps_values[0]) / rps_values[0] * 100
            rt_trend = (response_times[-1] - response_times[0]) / response_times[0] * 100

            print(f"RPS scaling: {rps_trend:+.1f}% from light to heavy load")
            print(f"Response time degradation: {rt_trend:+.1f}% from light to heavy load")

            if abs(rps_trend) < 50 and rt_trend < 200:
                print("✅ Good scalability - performance degrades gracefully")
            elif abs(rps_trend) < 100 and rt_trend < 500:
                print("⚠️  Acceptable scalability - some performance degradation")
            else:
                print("❌ Poor scalability - significant performance issues")

    def generate_recommendations(self, results: Dict[str, Any]):
        """Generate performance optimization recommendations"""
        print("\nOPTIMIZATION RECOMMENDATIONS:")
        print("-" * 40)

        recommendations = []

        # Analyze heavy load performance
        if 'heavy_load' in results and 'error' not in results['heavy_load']:
            heavy_data = results['heavy_load']

            if heavy_data['summary']['success_rate'] < 95:
                recommendations.append("❌ High error rate under load - optimize database queries and connection pooling")

            if heavy_data['response_times']['p95'] > 2.0:
                recommendations.append("❌ Slow response times - consider implementing caching and optimizing I/O operations")

            if heavy_data['system_resources']['max_cpu_percent'] > 80:
                recommendations.append("⚠️  High CPU usage - optimize CPU-intensive operations")

            if heavy_data['system_resources']['max_memory_percent'] > 80:
                recommendations.append("⚠️  High memory usage - check for memory leaks and optimize data structures")

        # General recommendations
        recommendations.extend([
            "✅ Consider implementing Redis caching for frequently accessed data",
            "✅ Optimize database queries with proper indexing",
            "✅ Implement request queuing for extreme loads",
            "✅ Add circuit breaker pattern for external service calls",
            "✅ Consider horizontal scaling with load balancer"
        ])

        for rec in recommendations:
            print(rec)

    def create_performance_charts(self, results: Dict[str, Any]):
        """Create performance visualization charts"""
        try:
            # Prepare data
            scenarios = []
            rps_data = []
            response_times = []
            success_rates = []

            for scenario, data in results.items():
                if 'error' not in data:
                    scenarios.append(scenario.replace('_', ' ').title())
                    rps_data.append(data['summary']['actual_rps'])
                    response_times.append(data['response_times']['p95'])
                    success_rates.append(data['summary']['success_rate'])

            if not scenarios:
                return

            # Create subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # RPS Chart
            bars1 = ax1.bar(scenarios, rps_data, color='skyblue')
            ax1.set_title('Requests Per Second by Scenario')
            ax1.set_ylabel('RPS')
            ax1.tick_params(axis='x', rotation=45)
            for bar, rps in zip(bars1, rps_data):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{rps:.1f}', ha='center', va='bottom')

            # Response Time Chart
            bars2 = ax2.bar(scenarios, response_times, color='lightcoral')
            ax2.set_title('95th Percentile Response Time by Scenario')
            ax2.set_ylabel('Response Time (seconds)')
            ax2.tick_params(axis='x', rotation=45)
            for bar, rt in zip(bars2, response_times):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{rt:.3f}s', ha='center', va='bottom')

            # Success Rate Chart
            bars3 = ax3.bar(scenarios, success_rates, color='lightgreen')
            ax3.set_title('Success Rate by Scenario')
            ax3.set_ylabel('Success Rate (%)')
            ax3.set_ylim(0, 100)
            ax3.tick_params(axis='x', rotation=45)
            for bar, sr in zip(bars3, success_rates):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{sr:.1f}%', ha='center', va='bottom')

            # Performance Trend
            ax4.plot(scenarios, rps_data, 'bo-', label='RPS', linewidth=2)
            ax4.set_ylabel('RPS', color='blue')
            ax4.tick_params(axis='y', labelcolor='blue')
            ax4.tick_params(axis='x', rotation=45)

            ax4_twin = ax4.twinx()
            ax4_twin.plot(scenarios, response_times, 'ro-', label='Response Time', linewidth=2)
            ax4_twin.set_ylabel('Response Time (s)', color='red')
            ax4_twin.tick_params(axis='y', labelcolor='red')

            ax4.set_title('Performance Trend: RPS vs Response Time')
            ax4.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig('stress_test_results.png', dpi=300, bbox_inches='tight')
            print("📊 Performance charts saved to: stress_test_results.png")

        except ImportError:
            print("⚠️  Matplotlib not available - skipping chart generation")
        except Exception as e:
            print(f"⚠️  Error creating charts: {e}")


class LoadProfiler:
    """Simplified load profiler for stress testing"""

    def __init__(self, base_url: str, duration: int):
        self.base_url = base_url.rstrip('/')
        self.duration = duration
        self.results = {
            'requests': [],
            'errors': [],
            'response_times': [],
            'cpu_usage': [],
            'memory_usage': []
        }

    async def single_request(self, session: aiohttp.ClientSession, endpoint: str,
                           method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
        """Make single HTTP request"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}

            async with session.request(method.upper(), url, json=data, headers=headers) as response:
                result = {
                    'method': method,
                    'endpoint': endpoint,
                    'status_code': response.status,
                    'response_time': time.time() - start_time,
                    'success': response.status < 400,
                    'error': None
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

    def monitor_resources(self):
        """Monitor system resources"""
        end_time = time.time() + self.duration
        while time.time() < end_time:
            self.results['cpu_usage'].append(psutil.cpu_percent(interval=0.1))
            self.results['memory_usage'].append(psutil.virtual_memory().percent)
            time.sleep(0.1)

    async def load_worker(self, worker_id: int, requests_per_second: int):
        """Worker for load testing"""
        async with aiohttp.ClientSession() as session:
            delay = 1.0 / requests_per_second if requests_per_second > 0 else 0
            end_time = time.time() + self.duration

            while time.time() < end_time:
                # Mix of request types
                request_types = [
                    ('/clicks', 'POST', {
                        "campaign_id": f"camp_load_{worker_id}",
                        "ip_address": f"192.168.1.{worker_id % 255}",
                        "user_agent": f"LoadTest/{worker_id}",
                        "referrer": "https://load-test.com"
                    }),
                    ('/events/track', 'POST', {
                        "event_type": "page_view",
                        "event_name": f"load_test_{worker_id}",
                        "user_id": f"user_{worker_id}",
                        "campaign_id": f"camp_load_{worker_id}",
                        "url": "https://test-page.com",
                        "user_agent": f"LoadTest/{worker_id}",
                        "ip_address": f"192.168.1.{worker_id % 255}"
                    }),
                    ('/conversions/track', 'POST', {
                        "click_id": f"click_load_{worker_id}",
                        "conversion_type": "sale",
                        "amount": 99.99,
                        "currency": "USD"
                    }),
                    ('/v1/campaigns', 'GET', None)
                ]

                for endpoint, method, data in request_types:
                    if time.time() >= end_time:
                        break

                    result = await self.single_request(session, endpoint, method, data)
                    self.results['requests'].append(result)

                    if not result['success']:
                        self.results['errors'].append(result)

                    if delay > 0:
                        await asyncio.sleep(delay)

    async def run_load_test(self, num_workers: int, requests_per_second: int) -> Dict[str, Any]:
        """Run load test"""
        self.results = {
            'requests': [],
            'errors': [],
            'response_times': [],
            'cpu_usage': [],
            'memory_usage': []
        }

        # Start resource monitoring
        monitor_thread = threading.Thread(target=self.monitor_resources, daemon=True)
        monitor_thread.start()

        # Create workers
        tasks = []
        for i in range(num_workers):
            task = asyncio.create_task(self.load_worker(i, requests_per_second))
            tasks.append(task)

        # Run test
        start_time = time.time()
        await asyncio.gather(*tasks, return_exceptions=True)
        actual_duration = time.time() - start_time

        # Analyze results
        return self.analyze_results(actual_duration)

    def analyze_results(self, actual_duration: float) -> Dict[str, Any]:
        """Analyze test results"""
        total_requests = len(self.results['requests'])
        successful_requests = len([r for r in self.results['requests'] if r['success']])

        response_times = [r['response_time'] for r in self.results['requests']] if self.results['requests'] else []

        analysis = {
            'summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': total_requests - successful_requests,
                'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                'actual_rps': total_requests / actual_duration if actual_duration > 0 else 0,
                'test_duration': actual_duration
            },
            'response_times': {
                'avg': statistics.mean(response_times) if response_times else 0,
                'median': statistics.median(response_times) if response_times else 0,
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'p95': np.percentile(response_times, 95) if response_times else 0,
                'p99': np.percentile(response_times, 99) if response_times else 0
            },
            'system_resources': {
                'avg_cpu_percent': statistics.mean(self.results['cpu_usage']) if self.results['cpu_usage'] else 0,
                'max_cpu_percent': max(self.results['cpu_usage']) if self.results['cpu_usage'] else 0,
                'avg_memory_percent': statistics.mean(self.results['memory_usage']) if self.results['memory_usage'] else 0,
                'max_memory_percent': max(self.results['memory_usage']) if self.results['memory_usage'] else 0
            },
            'errors': {
                'error_count': len(self.results['errors']),
                'error_types': {}
            }
        }

        # Count error types
        for error in self.results['errors']:
            error_type = error.get('error', 'unknown')
            analysis['errors']['error_types'][error_type] = analysis['errors']['error_types'].get(error_type, 0) + 1

        return analysis


def main():
    """Main function"""
    print("🔬 ADVANCED STRESS TEST ANALYZER")
    print("=" * 50)

    # Check server availability
    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding properly")
            return
    except:
        print("❌ Cannot connect to server at http://localhost:5000")
        print("Please start the server first: python main_clean.py")
        return

    # Run comprehensive test suite
    analyzer = StressTestAnalyzer()

    try:
        results = analyzer.run_comprehensive_test_suite()
        analyzer.create_performance_charts(results)

        print("
🎯 STRESS TEST COMPLETED!"        print("📊 Charts saved to: stress_test_results.png"        print("📈 Detailed results available in results object"

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    main()
