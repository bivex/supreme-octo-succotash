#!/usr/bin/env python3
"""
Comprehensive PostgreSQL load testing and performance analysis script.
Tests database performance under various loads and provides optimization recommendations.
"""

import psycopg2
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import random
import string
import json
import os

class DatabaseLoadTester:
    def __init__(self):
        self.conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'supreme_octosuccotash_db',
            'user': 'app_user',
            'password': 'app_password'
        }

        # Test configuration
        self.test_duration = 60  # seconds per test
        self.warmup_time = 10    # seconds
        self.concurrency_levels = [1, 2, 4, 8, 16, 32]

        # Test data
        self.test_campaigns = []
        self.test_clicks = []

        # Results storage
        self.results = {}

    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.conn_params)

    def create_test_data(self):
        """Create test data for load testing."""
        print("🔧 Creating test data for load testing...")

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Create test campaigns
            for i in range(100):
                cursor.execute("""
                    INSERT INTO campaigns (
                        id, name, description, status, cost_model,
                        payout_amount, payout_currency, safe_page_url, offer_page_url,
                        daily_budget_amount, daily_budget_currency,
                        total_budget_amount, total_budget_currency,
                        start_date, end_date, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f'test_campaign_{i}',
                    f'Test Campaign {i}',
                    f'Description for test campaign {i}',
                    'active',
                    'CPA',
                    15.0 + random.uniform(-5, 5), 'USD',
                    f'https://example.com/safe{i}',
                    f'https://example.com/offer{i}',
                    200.0 + random.uniform(-50, 50), 'USD',
                    5000.0 + random.uniform(-1000, 1000), 'USD',
                    datetime.now(),
                    datetime.now() + timedelta(days=30),
                    datetime.now(),
                    datetime.now()
                ))
                self.test_campaigns.append(f'test_campaign_{i}')

            # Create test clicks
            for i in range(1000):
                campaign_id = random.choice(self.test_campaigns)
                cursor.execute("""
                    INSERT INTO clicks (
                        id, campaign_id, user_id, ip_address, user_agent,
                        created_at, is_valid, click_url, referer
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f'test_click_{i}',
                    campaign_id,
                    f'user_{random.randint(1, 1000)}',
                    f'192.168.1.{random.randint(1, 255)}',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    datetime.now() - timedelta(minutes=random.randint(0, 1440)),
                    True,
                    f'https://example.com/click{i}',
                    f'https://google.com/search?q=test{i}'
                ))
                self.test_clicks.append(f'test_click_{i}')

            conn.commit()
            print(f"✅ Created {len(self.test_campaigns)} test campaigns and {len(self.test_clicks)} test clicks")

        finally:
            conn.close()

    def cleanup_test_data(self):
        """Clean up test data."""
        print("🧹 Cleaning up test data...")

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Delete test data
            cursor.execute("DELETE FROM clicks WHERE id LIKE 'test_click_%'")
            cursor.execute("DELETE FROM campaigns WHERE id LIKE 'test_campaign_%'")
            conn.commit()
            print("✅ Test data cleaned up")
        finally:
            conn.close()

    def run_select_test(self, thread_id, results, duration):
        """Run SELECT performance test."""
        conn = self.get_connection()
        cursor = conn.cursor()

        start_time = time.time()
        queries_executed = 0
        latencies = []

        try:
            while time.time() - start_time < duration:
                query_start = time.time()

                # Random SELECT queries
                if random.choice([True, False]):
                    # Get campaign by ID
                    campaign_id = random.choice(self.test_campaigns)
                    cursor.execute("SELECT * FROM campaigns WHERE id = %s", (campaign_id,))
                else:
                    # Get clicks for random campaign
                    campaign_id = random.choice(self.test_campaigns)
                    cursor.execute("SELECT * FROM clicks WHERE campaign_id = %s LIMIT 10", (campaign_id,))

                cursor.fetchone()  # Consume result
                queries_executed += 1
                latencies.append(time.time() - query_start)

        finally:
            conn.close()

        results[thread_id] = {
            'queries': queries_executed,
            'avg_latency': statistics.mean(latencies) if latencies else 0,
            'p95_latency': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0,
            'p99_latency': statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies) if latencies else 0
        }

    def run_insert_test(self, thread_id, results, duration):
        """Run INSERT performance test."""
        start_time = time.time()
        queries_executed = 0
        latencies = []

        try:
            while time.time() - start_time < duration:
                conn = self.get_connection()
                cursor = conn.cursor()
                query_start = time.time()

                try:
                    # Insert test click
                    campaign_id = random.choice(self.test_campaigns)
                    click_id = f'load_test_click_{thread_id}_{int(time.time() * 1000000)}'

                    cursor.execute("""
                        INSERT INTO clicks (
                            id, campaign_id, user_id, ip_address, user_agent,
                            created_at, is_valid, click_url, referer
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        click_id,
                        campaign_id,
                        f'user_{random.randint(1, 1000)}',
                        f'192.168.1.{random.randint(1, 255)}',
                        'Mozilla/5.0 Load Test',
                        datetime.now(),
                        True,
                        f'https://example.com/click_load_{thread_id}',
                        'https://loadtest.com'
                    ))

                    conn.commit()
                    queries_executed += 1
                    latencies.append(time.time() - query_start)

                finally:
                    conn.close()

        except Exception as e:
            print(f"Error in insert test thread {thread_id}: {e}")

        results[thread_id] = {
            'queries': queries_executed,
            'avg_latency': statistics.mean(latencies) if latencies else 0,
            'p95_latency': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0,
            'p99_latency': statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies) if latencies else 0
        }

    def run_mixed_test(self, thread_id, results, duration):
        """Run mixed read/write test."""
        start_time = time.time()
        queries_executed = 0
        latencies = []

        try:
            while time.time() - start_time < duration:
                conn = self.get_connection()
                cursor = conn.cursor()
                query_start = time.time()

                try:
                    # Mix of SELECT and INSERT operations
                    if random.choice([True, False, False]):  # 50% SELECT, 50% other
                        # SELECT
                        campaign_id = random.choice(self.test_campaigns)
                        cursor.execute("SELECT COUNT(*) FROM clicks WHERE campaign_id = %s", (campaign_id,))
                        cursor.fetchone()
                    elif random.choice([True, False]):
                        # INSERT click
                        campaign_id = random.choice(self.test_campaigns)
                        click_id = f'mixed_test_click_{thread_id}_{int(time.time() * 1000000)}'

                        cursor.execute("""
                            INSERT INTO clicks (
                                id, campaign_id, user_id, ip_address, user_agent,
                                created_at, is_valid, click_url, referer
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            click_id, campaign_id,
                            f'user_{random.randint(1, 1000)}',
                            f'192.168.1.{random.randint(1, 255)}',
                            'Mozilla/5.0 Mixed Test',
                            datetime.now(), True,
                            f'https://example.com/click_mixed_{thread_id}',
                            'https://mixedtest.com'
                        ))
                        conn.commit()
                    else:
                        # UPDATE
                        campaign_id = random.choice(self.test_campaigns)
                        cursor.execute("""
                            UPDATE campaigns
                            SET clicks_count = clicks_count + 1, updated_at = %s
                            WHERE id = %s
                        """, (datetime.now(), campaign_id))
                        conn.commit()

                    queries_executed += 1
                    latencies.append(time.time() - query_start)

                finally:
                    conn.close()

        except Exception as e:
            print(f"Error in mixed test thread {thread_id}: {e}")

        results[thread_id] = {
            'queries': queries_executed,
            'avg_latency': statistics.mean(latencies) if latencies else 0,
            'p95_latency': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0,
            'p99_latency': statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies) if latencies else 0
        }

    def run_load_test(self, test_type, concurrency, duration):
        """Run load test with specified parameters."""
        print(f"🏃 Running {test_type} test with {concurrency} concurrent connections for {duration}s...")

        results = {}
        threads = []

        # Create threads
        for i in range(concurrency):
            if test_type == 'select':
                thread = threading.Thread(target=self.run_select_test, args=(i, results, duration))
            elif test_type == 'insert':
                thread = threading.Thread(target=self.run_insert_test, args=(i, results, duration))
            elif test_type == 'mixed':
                thread = threading.Thread(target=self.run_mixed_test, args=(i, results, duration))

            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time
        total_queries = sum(result['queries'] for result in results.values())
        avg_latency = statistics.mean([result['avg_latency'] for result in results.values()])

        qps = total_queries / total_time if total_time > 0 else 0

        test_result = {
            'concurrency': concurrency,
            'total_queries': total_queries,
            'qps': qps,
            'avg_latency': avg_latency,
            'p95_latency': statistics.mean([result['p95_latency'] for result in results.values()]),
            'p99_latency': statistics.mean([result['p99_latency'] for result in results.values()]),
            'duration': total_time
        }

        print(f"  Result: {result['qps']:.1f} QPS, {result['avg_latency']*1000:.2f}ms avg latency")
        return test_result

    def run_comprehensive_test(self):
        """Run comprehensive load testing suite."""
        print("🚀 Starting Comprehensive PostgreSQL Load Testing")
        print("=" * 60)

        # Create test data
        self.create_test_data()

        test_types = ['select', 'insert', 'mixed']
        results = {test_type: [] for test_type in test_types}

        try:
            for test_type in test_types:
                print(f"\n📊 Testing {test_type.upper()} Operations")
                print("-" * 40)

                for concurrency in self.concurrency_levels:
                    # Warmup
                    if concurrency > 1:
                        print(f"🔥 Warmup with {concurrency} connections...")
                        self.run_load_test(test_type, min(concurrency, 4), self.warmup_time)

                    # Actual test
                    result = self.run_load_test(test_type, concurrency, self.test_duration)
                    results[test_type].append(result)

                    # Prevent overwhelming the system
                    time.sleep(2)

            # Generate report
            self.generate_report(results)

        finally:
            # Cleanup
            self.cleanup_test_data()

    def generate_report(self, results):
        """Generate comprehensive performance report."""
        print("\n🎯 LOAD TESTING RESULTS")
        print("=" * 60)

        for test_type, test_results in results.items():
            print(f"\n🏆 {test_type.upper()} Test Results")
            print("-" * 40)
            print(f"{'Concurrency':<12} {'QPS':<8} {'Avg Latency':<12} {'P95 Latency':<12} {'P99 Latency':<12}")
            print("-" * 60)

            for result in test_results:
                print(f"{result['concurrency']:<12} {result['qps']:<8.0f} {result['avg_latency']*1000:<12.1f} {result['p95_latency']*1000:<12.1f} {result['p99_latency']*1000:<12.1f}"))

        # Performance analysis
        self.analyze_performance(results)

    def analyze_performance(self, results):
        """Analyze performance results and provide recommendations."""
        print("\n🔍 PERFORMANCE ANALYSIS & RECOMMENDATIONS")
        print("=" * 60)

        # Find optimal concurrency
        max_qps = {}
        for test_type, test_results in results.items():
            max_result = max(test_results, key=lambda x: x['qps'])
            max_qps[test_type] = max_result

        print("🏆 Peak Performance:")
        for test_type, result in max_qps.items():
            print(f"  {test_type.upper()}: {result['qps']:.0f} QPS at {result['concurrency']} concurrency")

        # Latency analysis
        print("\n⏱️  Latency Analysis:")
        for test_type, result in max_qps.items():
            print(f"  {test_type.upper()}:")
            print(f"    Avg: {result['avg_latency']*1000:.1f}ms")
            print(f"    P95: {result['p95_latency']*1000:.1f}ms")
            print(f"    P99: {result['p99_latency']*1000:.1f}ms")

        # Check for bottlenecks
        print("\n🔍 Bottleneck Analysis:")

        # Check if performance degrades significantly at high concurrency
        for test_type, test_results in results.items():
            if len(test_results) >= 2:
                low_conc = test_results[0]  # Usually concurrency 1
                high_conc = test_results[-1]  # Highest concurrency

                degradation = (high_conc['qps'] / low_conc['qps']) * 100 if low_conc['qps'] > 0 else 0
                print(f"  {test_type.upper()} scaling: {degradation:.1f}% efficiency at high concurrency")

                if degradation < 50:
                    print(f"    ⚠️  Poor scaling detected - check connection pooling, locks, or hardware limits")

        # Recommendations
        print("\n💡 Optimization Recommendations:")

        # Memory recommendations
        max_qps_all = max([result['qps'] for results_list in results.values() for result in results_list])
        if max_qps_all < 1000:
            print("  📈 Low QPS detected - consider:")
            print("     - Increasing shared_buffers")
            print("     - Adding more CPU cores")
            print("     - Optimizing query plans")

        # Latency recommendations
        avg_latencies = [result['avg_latency'] for results_list in results.values() for result in results_list]
        if avg_latencies and statistics.mean(avg_latencies) > 0.1:  # > 100ms
            print("  🐌 High latency detected - consider:")
            print("     - Adding missing indexes")
            print("     - Query optimization")
            print("     - Connection pooling")
            print("     - Hardware upgrades")

        # Concurrency recommendations
        optimal_conc = {}
        for test_type, test_results in results.items():
            optimal = max(test_results, key=lambda x: x['qps'] / x['concurrency'])  # QPS per connection
            optimal_conc[test_type] = optimal['concurrency']

        avg_optimal = int(statistics.mean(list(optimal_conc.values())))
        print(f"  🎯 Recommended connection pool size: {avg_optimal}")

        print("\n✅ Load testing completed successfully!")

def main():
    tester = DatabaseLoadTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
