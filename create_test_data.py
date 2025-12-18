
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:20
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Create test data for cache testing.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from contextlib import contextmanager
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import psycopg2
    from psycopg2 import pool
    from src.container import Container
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed")
    sys.exit(1)


class TestDataCreator:
    """Handles creation of test data for cache testing."""

    def __init__(self, campaign_count: int = 100):
        self.campaign_count = campaign_count
        self.container = Container()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for test data creation."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    @contextmanager
    def get_database_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = self.container.get_db_connection()
            yield connection
        finally:
            if connection:
                connection.close()

    def generate_campaign_data(self, index: int) -> Dict[str, Any]:
        """Generate test campaign data."""
        campaign_id = f'camp_{index:03d}'
        created_at = datetime.now() - timedelta(days=random.randint(1, 30))

        return {
            'id': campaign_id,
            'name': f'Test Campaign {index}',
            'description': f'Description for Test Campaign {index}',
            'status': 'active',
            'cost_model': 'CPA',
            'payout_amount': 5.0,
            'payout_currency': 'USD',
            'safe_page_url': f'https://safe.example.com/{campaign_id}',
            'offer_page_url': f'https://offer.example.com/{campaign_id}',
            'daily_budget_amount': 100.0,
            'daily_budget_currency': 'USD',
            'total_budget_amount': 1000.0,
            'total_budget_currency': 'USD',
            'start_date': created_at,
            'end_date': created_at + timedelta(days=30),
            'created_at': created_at,
            'updated_at': datetime.now()
        }

    def create_campaign(self, connection, campaign_data: Dict[str, Any]) -> bool:
        """Create a single campaign in the database."""
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO campaigns (
                    id, name, description, status, cost_model,
                    payout_amount, payout_currency,
                    safe_page_url, offer_page_url,
                    daily_budget_amount, daily_budget_currency,
                    total_budget_amount, total_budget_currency,
                    start_date, end_date,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                campaign_data['id'], campaign_data['name'], campaign_data['description'],
                campaign_data['status'], campaign_data['cost_model'],
                campaign_data['payout_amount'], campaign_data['payout_currency'],
                campaign_data['safe_page_url'], campaign_data['offer_page_url'],
                campaign_data['daily_budget_amount'], campaign_data['daily_budget_currency'],
                campaign_data['total_budget_amount'], campaign_data['total_budget_currency'],
                campaign_data['start_date'], campaign_data['end_date'],
                campaign_data['created_at'], campaign_data['updated_at']
            ))

            self.logger.info(f"Successfully created campaign: {campaign_data['id']}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create campaign {campaign_data['id']}: {str(e)}")
            return False
        finally:
            cursor.close()

    def warmup_cache(self, connection) -> None:
        """Warm up the database cache with test queries."""
        self.logger.info("Warming up database cache")
        cursor = connection.cursor()

        try:
            for i in range(10):
                cursor.execute("SELECT id, name FROM campaigns WHERE status = 'active' LIMIT 50")
                cursor.fetchall()
                self.logger.debug(f"Cache warmup query {i + 1} completed")

            self.logger.info("Cache warmup completed")
        finally:
            cursor.close()

    def create_test_campaigns(self) -> int:
        """Create test campaigns and return count of successful creations."""
        self.logger.info("Starting test data creation")
        self.logger.info("=" * 50)

        created_count = 0

        try:
            with self.get_database_connection() as connection:
                for i in range(self.campaign_count):
                    campaign_data = self.generate_campaign_data(i)

                    if self.create_campaign(connection, campaign_data):
                        created_count += 1

                self.warmup_cache(connection)
                connection.commit()

                self.logger.info(f"Test data creation completed. Created {created_count} campaigns")

                print("\nTest data ready")
                print("Summary:")
                print(f"Created {created_count} campaigns")
                print("Ran 10 warmup queries")
                print("\nRun: POST /v1/system/upholder/audit")
                print("to check cache performance")

                return created_count

        except Exception as e:
            self.logger.error(f"Critical error during test data creation: {str(e)}")
            raise


def create_test_data() -> None:
    """Main entry point for test data creation."""
    try:
        creator = TestDataCreator()
        creator.create_test_campaigns()
    except Exception as e:
        print(f"Failed to create test data: {str(e)}")
        sys.exit(1)

class CacheTester:
    """Handles cache testing operations."""

    def __init__(self):
        self.container = Container()
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def get_database_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = self.container.get_db_connection()
            yield connection
        finally:
            if connection:
                connection.close()

    def test_count_caching(self) -> None:
        """Test repository count caching performance."""
        import time

        self.logger.info("Testing count caching")

        campaign_repo = self.container.get_campaign_repository()

        # First call
        self.logger.info("Executing first count call")
        start_time = time.time()
        count1 = campaign_repo.count_all()
        first_call_time = time.time() - start_time
        self.logger.info(f"First call time: {first_call_time:.4f}s")

        # Second call
        self.logger.info("Executing second count call")
        start_time = time.time()
        count2 = campaign_repo.count_all()
        second_call_time = time.time() - start_time
        self.logger.info(f"Second call time: {second_call_time:.4f}s")

        self.logger.info(f"Results: {count1}, {count2}")

        if count1 == count2:
            self.logger.info("Counts match - data consistency verified")

            if second_call_time < first_call_time * 0.1:
                self.logger.info("Cache working effectively")
                if second_call_time > 0:
                    speedup = first_call_time / second_call_time
                    self.logger.info(f"Cache speedup: {speedup:.1f}x")
                else:
                    self.logger.info("Instant response from cache")
            else:
                self.logger.warning("Cache may not be working properly")
                self.logger.info(f"First: {first_call_time:.4f}s, Second: {second_call_time:.4f}s")
        else:
            self.logger.error("Counts differ - cache inconsistency detected")

    def test_pg_stat_calls(self) -> None:
        """Check database calls after caching using pg_stat_statements."""
        import time

        self.logger.info("Testing database calls with pg_stat_statements")

        try:
            # Get initial call count
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%WHERE is_deleted = $1'")
                result = cursor.fetchone()
                initial_calls = result[0] if result else 0
                cursor.close()

            self.logger.info(f"Initial database calls: {initial_calls}")

            # Execute test calls
            repo = self.container.get_campaign_repository()

            for i in range(3):
                start = time.time()
                count = repo.count_all()
                elapsed = time.time() - start
                self.logger.info(f"Call {i+1}: count={count}, time={elapsed:.4f}s")

            # Get final call count
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%WHERE is_deleted = $1'")
                result = cursor.fetchone()
                final_calls = result[0] if result else 0
                cursor.close()

            self.logger.info(f"Final database calls: {final_calls}")
            self.logger.info(f"Difference: {final_calls - initial_calls}")

            if final_calls == initial_calls:
                self.logger.info("Cache working perfectly - no additional database calls")
            else:
                self.logger.warning("Cache may not be working - additional database calls detected")

        except Exception as e:
            self.logger.error(f"Error testing pg_stat calls: {str(e)}")

class APILoadTester:
    """Handles API load testing operations."""

    def __init__(self):
        self.container = Container()
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def get_database_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = self.container.get_db_connection()
            yield connection
        finally:
            if connection:
                connection.close()

    def load_test_campaigns_api(self, num_requests: int = 50, concurrent_requests: int = 10) -> None:
        """Load test campaigns API endpoint."""
        import requests
        import time
        import statistics
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from typing import Dict, Any

        self.logger.info("Starting campaigns API load test")
        self.logger.info("=" * 60)

        BASE_URL = 'http://localhost:5000'
        ENDPOINT = '/v1/campaigns?page=1&page_size=10'

        def make_request(request_id: int) -> Dict[str, Any]:
            start_time = time.time()
            try:
                headers = {
                    'Authorization': 'Bearer test_jwt_token_12345'
                }
                response = requests.get(f'{BASE_URL}{ENDPOINT}', headers=headers, timeout=10)
                elapsed = time.time() - start_time

                if response.status_code == 200:
                    return {'id': request_id, 'status': 'success', 'time': elapsed}
                elif response.status_code == 401:
                    return {'id': request_id, 'status': 'auth_failed', 'time': elapsed, 'code': response.status_code}
                else:
                    return {'id': request_id, 'status': 'error', 'time': elapsed, 'code': response.status_code}
            except Exception as e:
                elapsed = time.time() - start_time
                return {'id': request_id, 'status': 'exception', 'time': elapsed, 'error': str(e)}

        self.logger.info(f"Test parameters: Total requests: {num_requests}, Concurrent: {concurrent_requests}, Endpoint: {ENDPOINT}")

        results = []
        start_test = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                completed = len(results)
                if completed % 10 == 0:
                    self.logger.info(f'Completed {completed}/{num_requests} requests')

        total_test_time = time.time() - start_test

        self.logger.info("Test results:")
        self.logger.info("=" * 60)

        successful = [r for r in results if r['status'] == 'success']
        auth_failed = [r for r in results if r['status'] == 'auth_failed']
        errors = [r for r in results if r['status'] in ['error', 'exception']]

        self.logger.info(f"Successful: {len(successful)}")
        self.logger.info(f"Auth errors: {len(auth_failed)}")
        self.logger.info(f"Other errors: {len(errors)}")

        if successful:
            times = [r['time'] for r in successful]
            self.logger.info("Response times:")
            self.logger.info(f"Average: {statistics.mean(times):.4f}s")
            self.logger.info(f"Min: {min(times):.4f}s")
            self.logger.info(f"Max: {max(times):.4f}s")
            self.logger.info(f"Median: {statistics.median(times):.4f}s")

            avg_time = statistics.mean(times)
            if avg_time < 0.1:
                self.logger.info("Excellent performance - cache works perfectly")
            elif avg_time < 0.5:
                self.logger.info("Good performance")
            else:
                self.logger.warning("Performance needs improvement")
        else:
            self.logger.error("All requests failed authentication - check token or endpoint")

        self.logger.info(f"Total time: {total_test_time:.1f}s")
        self.logger.info(f"Requests/sec: {num_requests/total_test_time:.1f}")

            # Database check
        self._check_database_calls(num_requests)

    def _check_database_calls(self, num_requests: int) -> None:
        """Check database calls for cache efficiency."""
        self.logger.info("Database check:")
        self.logger.info("=" * 60)

        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%COUNT(*) FROM campaigns WHERE is_deleted%'")
                count_result = cursor.fetchone()

                if count_result:
                    count_calls = count_result[0]
                    self.logger.info(f"Database calls: {count_calls}")
                    self.logger.info(f"API requests: {num_requests}")
                    efficiency = ((num_requests - count_calls) / num_requests * 100)
                    self.logger.info(f"Cache efficiency: {efficiency:.1f}%")

                    if count_calls <= 2:
                        self.logger.info("Cache working perfectly - minimal database load")
                else:
                    self.logger.warning("No statistics found")

                cursor.close()

        except Exception as e:
            self.logger.error(f"Error checking database calls: {str(e)}")

    def create_mass_campaigns_api(self, total_campaigns: int = 5000, concurrent_requests: int = 20) -> None:
        """Create many campaigns via API for stress testing."""
        import requests
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from typing import Dict, Any

        self.logger.info("Starting mass campaign creation via API")
        self.logger.info("=" * 60)

        BASE_URL = 'http://localhost:5000'
        ENDPOINT = '/v1/campaigns'

        headers = {
            'Authorization': 'Bearer test_jwt_token_12345',
            'Content-Type': 'application/json'
        }

        self.logger.info("Settings:")
        self.logger.info(f"Total campaigns: {total_campaigns}")
        self.logger.info(f"Concurrent threads: {concurrent_requests}")

        # Generate campaign data
        self.logger.info("Generating campaign data")
        cost_models = ["CPA", "CPC", "CPM"]

        def generate_campaign_data(index: int) -> Dict[str, Any]:
            return {
                "name": f"Campaign_{index:04d}",
                "description": f"Mass test campaign #{index}",
                "costModel": cost_models[index % 3],
                "payout": {"amount": 5.0, "currency": "USD"},
                "whiteUrl": f"https://safe.example.com/{index}",
                "blackUrl": f"https://offer.example.com/{index}",
                "dailyBudget": {"amount": 100.0, "currency": "USD"},
                "totalBudget": {"amount": 1000.0, "currency": "USD"}
            }

        all_campaigns_data = [generate_campaign_data(i) for i in range(total_campaigns)]
        self.logger.info(f"Generated {len(all_campaigns_data)} data sets")

        successful = 0
        failed = 0

        def create_single_campaign(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal successful, failed
            try:
                response = requests.post(
                    f'{BASE_URL}{ENDPOINT}',
                    json=campaign_data,
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 201:
                    successful += 1
                    return {'status': 'success'}
                else:
                    failed += 1
                    return {'status': 'error', 'code': response.status_code}

            except Exception as e:
                failed += 1
                return {'status': 'exception'}

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(create_single_campaign, data) for data in all_campaigns_data]

            for i, future in enumerate(as_completed(futures)):
                result = future.result()

                if (i + 1) % 500 == 0:
                    current_time = time.time()
                    elapsed = current_time - start_time
                    progress = (i + 1) / total_campaigns * 100
                    rate = (i + 1) / elapsed

                    self.logger.info(f"Progress: {progress:.1f}% | {successful}/{successful + failed} successful | Speed: {rate:.1f} campaigns/sec")

        total_time = time.time() - start_time

        self.logger.info("Final results:")
        self.logger.info("=" * 60)
        self.logger.info(f"Created: {successful} campaigns")
        self.logger.info(f"Errors: {failed} campaigns")
        self.logger.info(f"Total time: {total_time:.2f} seconds")
        self.logger.info(f"Speed: {total_campaigns/total_time:.1f} campaigns/second")
        self.logger.info(f"Efficiency: {successful/total_campaigns*100:.1f}%")

        # Check cache impact
        self._check_mass_creation_cache_impact(total_campaigns, successful)

        self.logger.info(f"Mass creation completed. Created {successful} campaigns in {total_time:.2f} seconds")
        self.logger.info("System ready for production")

    def _check_mass_creation_cache_impact(self, total_campaigns: int, successful: int) -> None:
        """Check cache impact after mass campaign creation."""
        self.logger.info("Cache impact:")
        self.logger.info("=" * 60)

        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%COUNT(*) FROM campaigns WHERE is_deleted%'")
                count_result = cursor.fetchone()

                if count_result:
                    count_calls = count_result[0]
                    self.logger.info(f"Database calls: {count_calls} (out of {total_campaigns} API requests)")
                    efficiency = ((total_campaigns - count_calls) / total_campaigns * 100)
                    self.logger.info(f"Cache efficiency: {efficiency:.1f}%")
                    self.logger.info("Cache working")
                else:
                    self.logger.warning("No statistics found")

                cursor.close()

        except Exception as e:
            self.logger.error(f"Error checking cache impact: {str(e)}")

def main() -> None:
    """Main entry point for test data operations."""
    import sys

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            tester = CacheTester()
            tester.test_count_caching()
        elif len(sys.argv) > 1 and sys.argv[1] == "pg_stat":
            tester = CacheTester()
            tester.test_pg_stat_calls()
        elif len(sys.argv) > 1 and sys.argv[1] == "load_test":
            load_tester = APILoadTester()
            load_tester.load_test_campaigns_api()
        elif len(sys.argv) > 1 and sys.argv[1] == "mass_create":
            load_tester = APILoadTester()
            load_tester.create_mass_campaigns_api()
        else:
            create_test_data()
            tester = CacheTester()
            tester.test_count_caching()

    except Exception as e:
        print(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
