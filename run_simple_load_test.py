# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:57
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Simple PostgreSQL load test - quick performance check.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Dict

import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = 'localhost'
    port: int = 5432
    database: str = 'supreme_octosuccotash_db'
    user: str = 'app_user'
    password: str = 'app_password'


@dataclass
class TestResult:
    """Result of a load test."""
    concurrency: int
    total_queries: int
    duration: float
    qps: float


class DatabaseConnectionManager:
    """Manages database connections with proper cleanup."""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            yield conn
        finally:
            if conn:
                conn.close()


class LoadTestBase:
    """Base class for load tests."""

    def __init__(self, db_manager: DatabaseConnectionManager):
        self.db_manager = db_manager

    def run_test(self, concurrency: int, duration: int) -> TestResult:
        """Run the load test with given concurrency and duration."""
        logger.info(f"Testing {self.__class__.__name__} with {concurrency} concurrent connections...")

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            start_time = time.time()
            if hasattr(self, '_worker_with_id'):
                futures = [executor.submit(self._worker_with_id, i) for i in range(concurrency)]
            else:
                futures = [executor.submit(self._worker) for _ in range(concurrency)]
            results = [future.result() for future in futures]
            total_time = time.time() - start_time

        total_queries = sum(results)
        qps = total_queries / total_time if total_time > 0 else 0

        logger.info(f"Completed {total_queries} operations in {total_time:.1f}s = {qps:.0f} QPS")
        return TestResult(concurrency, total_queries, total_time, qps)

    def _worker(self) -> int:
        """Worker function to be implemented by subclasses."""
        raise NotImplementedError


class SelectLoadTest(LoadTestBase):
    """Test SELECT performance under load."""

    def _worker(self) -> int:
        """Execute SELECT queries for the test duration."""
        queries = 0
        start_time = time.time()
        duration = getattr(self, '_test_duration', 30)

        while time.time() - start_time < duration:
            try:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM campaigns")
                        cursor.fetchone()
                        queries += 1
            except psycopg2.Error as e:
                logger.warning(f"SELECT query failed: {e}")
                continue

        return queries


class InsertLoadTest(LoadTestBase):
    """Test INSERT performance under load."""

    def _worker_with_id(self, worker_id: int) -> int:
        """Execute INSERT queries for the test duration."""
        queries = 0
        start_time = time.time()
        duration = getattr(self, '_test_duration', 30)

        while time.time() - start_time < duration:
            try:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        click_id = f'loadtest_click_{worker_id}_{int(time.time() * 1000000)}'
                        cursor.execute("""
                                       INSERT INTO events (id, event_type, event_data, created_at)
                                       VALUES (%s, %s, %s, NOW())
                                       """, (click_id, 'load_test', '{"test": true}',))
                        conn.commit()
                        queries += 1
            except psycopg2.IntegrityError:
                # Ignore duplicate key errors
                continue
            except psycopg2.Error as e:
                logger.warning(f"INSERT query failed: {e}")
                continue

        self._cleanup_test_data()
        return queries

    def _cleanup_test_data(self):
        """Clean up test data."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM events WHERE event_type = 'load_test'")
                    conn.commit()
        except psycopg2.Error as e:
            logger.warning(f"Cleanup failed: {e}")


class MixedLoadTest(LoadTestBase):
    """Test mixed read/write load."""

    def _worker_with_id(self, worker_id: int) -> int:
        """Execute mixed operations for the test duration."""
        queries = 0
        start_time = time.time()
        duration = getattr(self, '_test_duration', 30)

        while time.time() - start_time < duration:
            try:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        operation_type = queries % 3

                        if operation_type == 0:
                            # SELECT
                            cursor.execute("SELECT COUNT(*) FROM campaigns")
                            cursor.fetchone()
                        elif operation_type == 1:
                            # UPDATE
                            cursor.execute(
                                "UPDATE campaigns SET updated_at = NOW() WHERE id = (SELECT id FROM campaigns LIMIT 1)")
                            conn.commit()
                        else:
                            # INSERT
                            event_id = f'mixed_load_{worker_id}_{queries}'
                            cursor.execute("""
                                           INSERT INTO events (id, event_type, event_data, created_at)
                                           VALUES (%s, %s, %s, NOW())
                                           """, (event_id, 'mixed_test', '{"mixed": true}',))
                            conn.commit()

                        queries += 1
            except psycopg2.Error as e:
                logger.warning(f"Mixed operation failed: {e}")
                continue

        self._cleanup_test_data()
        return queries

    def _cleanup_test_data(self):
        """Clean up test data."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM events WHERE event_type IN ('load_test', 'mixed_test')")
                    conn.commit()
        except psycopg2.Error as e:
            logger.warning(f"Cleanup failed: {e}")


class PerformanceAnalyzer:
    """Analyzes and reports performance results."""

    def __init__(self, results: Dict[str, List[TestResult]]):
        self.results = results

    def print_summary(self):
        """Print performance summary."""
        print("\nPERFORMANCE SUMMARY")
        print("=" * 50)

        for test_type, data in self.results.items():
            print(f"\n{test_type.upper()} Performance:")
            if not data:
                continue

            max_result = max(data, key=lambda x: x.qps)
            print(f"  Peak: {max_result.qps:.0f} QPS at {max_result.concurrency} concurrency")

            # Scaling efficiency
            if len(data) > 1:
                single_result = next((r for r in data if r.concurrency == 1), None)
                if single_result and single_result.qps > 0:
                    efficiency = (max_result.qps / single_result.qps) * 100 / max_result.concurrency
                    print(f"  Scaling efficiency: {efficiency:.1f}%")

    def print_recommendations(self):
        """Print optimization recommendations."""
        print("\nOPTIMIZATION RECOMMENDATIONS")
        print("=" * 50)

        max_select = max((r.qps for r in self.results.get('select', [])), default=0)
        max_insert = max((r.qps for r in self.results.get('insert', [])), default=0)
        max_mixed = max((r.qps for r in self.results.get('mixed', [])), default=0)

        print("Peak Performance Achieved:")
        print(f"  SELECT: {max_select:.0f} QPS")
        print(f"  INSERT: {max_insert:.0f} QPS")
        print(f"  MIXED:  {max_mixed:.0f} QPS")

        self._evaluate_performance("SELECT", max_select, 50000, 10000)
        self._evaluate_performance("INSERT", max_insert, 5000, 1000)

        # Optimal pool size calculation
        optimal_sizes = []
        for test_type, data in self.results.items():
            if data:
                optimal = max(data, key=lambda r: r.qps / r.concurrency if r.concurrency > 0 else 0)
                optimal_sizes.append(optimal.concurrency)

        if optimal_sizes:
            recommended_pool = int(sum(optimal_sizes) / len(optimal_sizes))
            print(f"  Recommended connection pool size: {recommended_pool}")

    def _evaluate_performance(self, test_type: str, qps: float, excellent_threshold: float, good_threshold: float):
        """Evaluate performance against thresholds."""
        if qps > excellent_threshold:
            print(f"  Excellent {test_type} performance!")
        elif qps > good_threshold:
            print(f"  Good {test_type} performance!")
        else:
            print(f"  {test_type} performance could be improved")


def main():
    """Main entry point for the load testing application."""
    print("PostgreSQL Load Testing Results")
    print("=" * 50)

    # Configuration
    db_config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(db_config)

    test_concurrencies = [1, 2, 4, 8, 16]
    test_duration = 10  # seconds

    # Initialize test runners
    tests = {
        'select': SelectLoadTest(db_manager),
        'insert': InsertLoadTest(db_manager),
        'mixed': MixedLoadTest(db_manager)
    }

    results = {name: [] for name in tests.keys()}

    # Run tests
    for concurrency in test_concurrencies:
        print(f"\nTesting with {concurrency} concurrent connections")

        for test_name, test_runner in tests.items():
            # Set test duration on the runner
            test_runner._test_duration = test_duration

            result = test_runner.run_test(concurrency, test_duration)
            results[test_name].append(result)

        print()

    # Analyze and report results
    analyzer = PerformanceAnalyzer(results)
    analyzer.print_summary()
    analyzer.print_recommendations()

    print("\nLoad testing completed!")


if __name__ == "__main__":
    main()
