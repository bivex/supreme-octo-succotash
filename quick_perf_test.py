# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:01
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Quick PostgreSQL performance test script.
Measures basic database performance metrics.
"""

import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict

import psycopg2


class DatabaseConfig:
    """Database configuration settings."""

    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'supreme_octosuccotash_db')
        self.user = os.getenv('DB_USER', 'app_user')
        self.password = os.getenv('DB_PASSWORD', 'app_password')

    def get_connection_params(self) -> Dict[str, str]:
        """Get connection parameters as dictionary."""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }


class PerformanceTester:
    """Handles database performance testing operations."""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    def get_connection(self) -> psycopg2.extensions.connection:
        """Create and return a database connection."""
        return psycopg2.connect(**self.config.get_connection_params())

    def test_connection_pooling(self) -> None:
        """Test connection pooling performance."""
        print("Testing connection pooling...")

        start_time = time.time()
        connections_created = 0

        # Create 50 connections quickly
        for i in range(50):
            try:
                conn = self.get_connection()
                conn.close()
                connections_created += 1
            except Exception as e:
                print(f"Connection failed: {e}")
                break

        connection_time = time.time() - start_time
        print(f"Created {connections_created} connections in {connection_time:.2f}s")
        print(f"Rate: {connections_created / connection_time:.1f} connections/second")

    def test_simple_queries(self) -> None:
        """Test simple query performance."""
        print("\nTesting simple queries...")

        conn = self.get_connection()
        cursor = conn.cursor()

        # Test different query types
        queries = [
            ("SELECT COUNT(*) FROM campaigns", "Count campaigns"),
            ("SELECT COUNT(*) FROM clicks", "Count clicks"),
            ("SELECT COUNT(*) FROM events", "Count events"),
            ("SELECT * FROM campaigns LIMIT 10", "Select 10 campaigns"),
            ("SELECT * FROM clicks LIMIT 10", "Select 10 clicks"),
            ("SELECT id, name FROM campaigns WHERE status = 'active' LIMIT 5", "Filter active campaigns"),
        ]

        for query, description in queries:
            start_time = time.time()
            cursor.execute(query)
            result = cursor.fetchall()
            exec_time = time.time() - start_time

            result_count = len(result) if result else 0
            print(f"{description}: {exec_time:.4f}s ({result_count} rows)")

        conn.close()

    def test_concurrent_reads(self) -> None:
        """Test concurrent read performance."""
        print("\nTesting concurrent reads...")

        def worker_read(worker_id: int, config: DatabaseConfig) -> int:
            """Worker function for concurrent read testing."""
            conn = psycopg2.connect(**config.get_connection_params())
            cursor = conn.cursor()

            start_time = time.time()
            queries = 0

            # Run queries for 10 seconds
            while time.time() - start_time < 10:
                cursor.execute("SELECT COUNT(*) FROM campaigns")
                cursor.fetchone()
                queries += 1

            conn.close()
            return queries

        # Test with different concurrency levels
        for concurrency in [1, 2, 4, 8]:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                start_time = time.time()
                futures = [executor.submit(worker_read, i, self.config) for i in range(concurrency)]
                results = [future.result() for future in futures]
                total_time = time.time() - start_time

            total_queries = sum(results)
            qps = total_queries / total_time

            print(f"{concurrency} concurrent: {total_queries} queries in {total_time:.1f}s = {qps:.0f} QPS")

    def test_index_performance(self) -> None:
        """Test index performance."""
        print("\nTesting index performance...")

        conn = self.get_connection()
        cursor = conn.cursor()

        # Test indexed vs non-indexed queries
        test_queries = [
            ("SELECT * FROM campaigns WHERE id = 'test_campaign_1'", "Primary key lookup"),
            ("SELECT * FROM clicks WHERE campaign_id = 'test_campaign_1' LIMIT 5", "Foreign key lookup"),
            ("SELECT COUNT(*) FROM campaigns WHERE status = 'active'", "Status filter"),
            ("SELECT * FROM events ORDER BY created_at DESC LIMIT 10", "Ordered by timestamp"),
        ]

        for query, description in test_queries:
            # Run query multiple times and average
            times = []
            for _ in range(5):
                start_time = time.time()
                cursor.execute(query)
                cursor.fetchall()
                times.append(time.time() - start_time)

            avg_time = statistics.mean(times)
            print(f"{description}: {avg_time:.4f}s average")

        conn.close()

    def test_write_performance(self) -> None:
        """Test write performance."""
        print("\nTesting write performance...")

        conn = self.get_connection()
        cursor = conn.cursor()

        # Test INSERT performance
        start_time = time.time()
        inserts = 0

        try:
            for i in range(100):
                cursor.execute("""
                               INSERT INTO events (id, click_id, event_type, event_data, created_at)
                               VALUES (%s, %s, %s, %s, %s)
                               """, (
                                   f'perf_test_event_{i}',
                                   'test_click_1' if i % 2 == 0 else None,
                                   'page_view',
                                   '{"url": "/test", "duration": 100}',
                                   datetime.now()
                               ))
                inserts += 1

            conn.commit()
            insert_time = time.time() - start_time

            print(f"Inserted {inserts} events in {insert_time:.2f}s")
            print(f"Rate: {inserts / insert_time:.0f} inserts/second")
        except Exception as e:
            print(f"Write test failed: {e}")
            conn.rollback()
        finally:
            # Cleanup
            try:
                cursor.execute("DELETE FROM events WHERE id LIKE 'perf_test_event_%'")
                conn.commit()
            except Exception as e:
                print(f"Cleanup failed: {e}")

        conn.close()

    def run_all_tests(self) -> None:
        """Run all performance tests."""
        print("Quick PostgreSQL Performance Test")
        print("=" * 50)
        print(f"Started: {datetime.now()}")
        print()

        self.test_connection_pooling()
        self.test_simple_queries()
        self.test_concurrent_reads()
        self.test_index_performance()
        self.test_write_performance()

        print("\nPerformance test completed!")
        print(f"Finished: {datetime.now()}")


def main():
    """Main entry point for the performance test script."""
    config = DatabaseConfig()
    tester = PerformanceTester(config)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
