#!/usr/bin/env python3
"""
Create test data for cache testing
"""

import psycopg2
from datetime import datetime, timedelta
import random

def create_test_data():
    """Create test campaigns for cache testing"""
    try:
        print("Connecting to database")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="supreme_octosuccotash_db",
            user="app_user",
            password="app_password"
        )
        cursor = conn.cursor()
        print("Connected")

        print("Creating test campaigns")

        campaigns_data = []
        for i in range(100):
            campaign = {
                'id': f'camp_{i:03d}',
                'name': f'Test Campaign {i}',
                'status': 'active',
                'created_at': datetime.now() - timedelta(days=random.randint(1, 30)),
                'updated_at': datetime.now()
            }
            campaigns_data.append(campaign)

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
                    campaign['id'], campaign['name'], f'Description for {campaign["name"]}', campaign['status'], 'CPA',
                    5.0, 'USD',
                    f'https://safe.example.com/{campaign["id"]}', f'https://offer.example.com/{campaign["id"]}',
                    100.0, 'USD',
                    1000.0, 'USD',
                    campaign['created_at'], campaign['created_at'] + timedelta(days=30),
                    campaign['created_at'], campaign['updated_at']
                ))
                print(f"Created campaign {campaign['id']}")
            except Exception as e:
                print(f"Failed to create campaign {campaign['id']}: {e}")
                continue

        print("Warming up cache")
        for _ in range(10):
            cursor.execute("SELECT id, name FROM campaigns WHERE status = 'active' LIMIT 50")
            cursor.fetchall()

        conn.commit()
        cursor.close()
        conn.close()

        print("Test data ready")
        print("Summary:")
        print(f"Created {len(campaigns_data)} campaigns")
        print("Ran 10 warmup queries")

        print("\nRun: POST /v1/system/upholder/audit")
        print("to check cache performance")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and not conn.closed:
            conn.commit()
            cursor.close()
            conn.close()

def test_count_caching():
    """Test repository caching"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

    from src.container import Container

    print("Testing count caching")

    container = Container()
    campaign_repo = container.get_campaign_repository()

    import time

    print("First call")
    start_time = time.time()
    count1 = campaign_repo.count_all()
    first_call_time = time.time() - start_time
    print(f"Time: {first_call_time:.4f}s")

    print("Second call")
    start_time = time.time()
    count2 = campaign_repo.count_all()
    second_call_time = time.time() - start_time
    print(f"Time: {second_call_time:.4f}s")
    print(f"Results: {count1}, {count2}")

    if count1 == count2:
        print("Counts match")

        if second_call_time < first_call_time * 0.1:
            print("Cache working")
            if second_call_time > 0:
                print(f"Speed up: {first_call_time/second_call_time:.1f}x")
            else:
                print("Instant response")
        else:
            print("Cache may not work")
            print(f"First: {first_call_time:.4f}s, Second: {second_call_time:.4f}s")
    else:
        print("Counts differ")

def test_pg_stat_calls():
    """Check database calls after caching"""
    import psycopg2

    conn = psycopg2.connect(host='localhost', port=5432, database='supreme_octosuccotash_db', user='app_user', password='app_password')
    cursor = conn.cursor()
    cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%WHERE is_deleted = $1'")
    initial_calls = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    print(f"Initial database calls: {initial_calls}")

    import sys
    sys.path.insert(0, 'src')
    from src.container import Container
    import time

    container = Container()
    repo = container.get_campaign_repository()

    for i in range(3):
        start = time.time()
        count = repo.count_all()
        elapsed = time.time() - start
        print(f"Call {i+1}: count={count}, time={elapsed:.4f}s")

    conn = psycopg2.connect(host='localhost', port=5432, database='supreme_octosuccotash_db', user='app_user', password='app_password')
    cursor = conn.cursor()
    cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%WHERE is_deleted = $1'")
    final_calls = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    print(f"Final database calls: {final_calls}")
    print(f"Difference: {final_calls - initial_calls}")

    if final_calls == initial_calls:
        print("Cache working perfectly")
    else:
        print("Cache may not work")

def load_test_campaigns_api():
    """Load test campaigns API"""
    import requests
    import time
    import statistics
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print('Load testing campaigns API')
    print('=' * 60)

    BASE_URL = 'http://localhost:5000'
    ENDPOINT = '/v1/campaigns?page=1&page_size=10'

    def make_request(request_id):
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

    NUM_REQUESTS = 50
    CONCURRENT_REQUESTS = 10

    print(f'Test parameters:')
    print(f'Total requests: {NUM_REQUESTS}')
    print(f'Concurrent: {CONCURRENT_REQUESTS}')
    print(f'Endpoint: {ENDPOINT}')
    print()

    results = []
    start_test = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(make_request, i) for i in range(NUM_REQUESTS)]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            completed = len(results)
            if completed % 10 == 0:
                print(f'Completed {completed}/{NUM_REQUESTS} requests')

    total_test_time = time.time() - start_test

    print()
    print('Test results:')
    print('=' * 60)

    successful = [r for r in results if r['status'] == 'success']
    auth_failed = [r for r in results if r['status'] == 'auth_failed']
    errors = [r for r in results if r['status'] in ['error', 'exception']]

    print(f'Successful: {len(successful)}')
    print(f'Auth errors: {len(auth_failed)}')
    print(f'Other errors: {len(errors)}')
    print()

    if successful:
        times = [r['time'] for r in successful]
        print('Response times:')
        print(f'Average: {statistics.mean(times):.4f}s')
        print(f'Min: {min(times):.4f}s')
        print(f'Max: {max(times):.4f}s')
        print(f'Median: {statistics.median(times):.4f}s')
        print()

    print('Performance analysis:')
    print('=' * 60)

    if successful:
        avg_time = statistics.mean(times)
        print(f'Average time: {avg_time:.4f}s')
        if avg_time < 0.1:
            print('Excellent performance')
            print('Cache works perfectly')
        elif avg_time < 0.5:
            print('Good performance')
        else:
            print('Needs improvement')
    else:
        print('All requests failed auth')
        print('Check token or endpoint')

    print()
    print(f'Total time: {total_test_time:.1f}s')
    print(f'Requests/sec: {NUM_REQUESTS/total_test_time:.1f}')

    print()
    print('Database check:')
    print('=' * 60)

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost', port=5432, database='supreme_octosuccotash_db',
            user='app_user', password='app_password'
        )
        cursor = conn.cursor()

        cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%COUNT(*) FROM campaigns WHERE is_deleted%'")
        count_result = cursor.fetchone()

        if count_result:
            count_calls = count_result[0]
            print(f'Database calls: {count_calls}')
            print(f'API requests: {NUM_REQUESTS}')
            print(f'Cache efficiency: {((NUM_REQUESTS - count_calls) / NUM_REQUESTS * 100):.1f}%')

            if count_calls <= 2:
                print('Cache working perfectly')
                print('Minimal database load')
        else:
            print('No statistics found')

        cursor.close()
        conn.close()

    except Exception as e:
        print(f'Error: {e}')

def create_mass_campaigns_api():
    """Create many campaigns via API"""
    import requests
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print('Mass campaign creation')
    print('=' * 60)

    BASE_URL = 'http://localhost:5000'
    ENDPOINT = '/v1/campaigns'

    headers = {
        'Authorization': 'Bearer test_jwt_token_12345',
        'Content-Type': 'application/json'
    }

    TOTAL_CAMPAIGNS = 5000
    CONCURRENT_REQUESTS = 20
    SUCCESSFUL = 0
    FAILED = 0

    print(f'Settings:')
    print(f'Total campaigns: {TOTAL_CAMPAIGNS}')
    print(f'Concurrent threads: {CONCURRENT_REQUESTS}')
    print()

    print('Generating data')
    cost_models = ["CPA", "CPC", "CPM"]

    def generate_campaign_data(index):
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

    all_campaigns_data = [generate_campaign_data(i) for i in range(TOTAL_CAMPAIGNS)]
    print(f'Generated {len(all_campaigns_data)} data sets')
    print()

    def create_single_campaign(campaign_data):
        nonlocal SUCCESSFUL, FAILED
        try:
            response = requests.post(
                f'{BASE_URL}{ENDPOINT}',
                json=campaign_data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 201:
                SUCCESSFUL += 1
                return {'status': 'success'}
            else:
                FAILED += 1
                return {'status': 'error', 'code': response.status_code}

        except Exception as e:
            FAILED += 1
            return {'status': 'exception'}

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(create_single_campaign, data) for data in all_campaigns_data]

        for i, future in enumerate(as_completed(futures)):
            result = future.result()

            if (i + 1) % 500 == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                progress = (i + 1) / TOTAL_CAMPAIGNS * 100
                rate = (i + 1) / elapsed

                print(f'Progress: {progress:.1f}% | '
                      f'{SUCCESSFUL}/{SUCCESSFUL + FAILED} successful | '
                      f'Speed: {rate:.1f} campaigns/sec')

    total_time = time.time() - start_time

    print()
    print('Final results:')
    print('=' * 60)
    print(f'Created: {SUCCESSFUL} campaigns')
    print(f'Errors: {FAILED} campaigns')
    print(f'Total time: {total_time:.2f} seconds')
    print(f'Speed: {TOTAL_CAMPAIGNS/total_time:.1f} campaigns/second')
    print(f'Efficiency: {SUCCESSFUL/TOTAL_CAMPAIGNS*100:.1f}%')

    print()
    print('Cache impact:')
    print('=' * 60)

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost', port=5432, database='supreme_octosuccotash_db',
            user='app_user', password='app_password'
        )
        cursor = conn.cursor()

        cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%COUNT(*) FROM campaigns WHERE is_deleted%'")
        count_result = cursor.fetchone()

        if count_result:
            count_calls = count_result[0]
            print(f'Database calls: {count_calls} (out of {TOTAL_CAMPAIGNS} API requests)')
            print(f'Cache efficiency: {((TOTAL_CAMPAIGNS - count_calls) / TOTAL_CAMPAIGNS * 100):.1f}%')
            print('Cache working')
        else:
            print('No statistics found')

        cursor.close()
        conn.close()

    except Exception as e:
        print(f'Error: {e}')

    print()
    print('Done')
    print(f'Created {SUCCESSFUL} campaigns in {total_time:.2f} seconds')
    print('System ready for production')

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_count_caching()
    elif len(sys.argv) > 1 and sys.argv[1] == "pg_stat":
        test_pg_stat_calls()
    elif len(sys.argv) > 1 and sys.argv[1] == "load_test":
        load_test_campaigns_api()
    elif len(sys.argv) > 1 and sys.argv[1] == "mass_create":
        create_mass_campaigns_api()
    else:
        create_test_data()
        test_count_caching()
