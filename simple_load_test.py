#!/usr/bin/env python3
"""
Simple PostgreSQL load test - quick performance check.
"""

import psycopg2
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor

def run_select_load(concurrency, duration=30):
    """Test SELECT performance under load."""
    def worker():
        conn = psycopg2.connect(
            host='localhost', port=5432,
            database='supreme_octosuccotash_db',
            user='app_user', password='app_password'
        )
        cursor = conn.cursor()

        queries = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            cursor.execute("SELECT COUNT(*) FROM campaigns")
            cursor.fetchone()
            queries += 1

        conn.close()
        return queries

    print(f"🏃 Testing SELECT with {concurrency} concurrent connections...")

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        start_time = time.time()
        futures = [executor.submit(worker) for _ in range(concurrency)]
        results = [future.result() for future in futures]
        total_time = time.time() - start_time

    total_queries = sum(results)
    qps = total_queries / total_time

    print(f"  ✅ {total_queries} queries in {total_time:.1f}s = {qps:.0f} QPS")
    return qps

def run_insert_load(concurrency, duration=30):
    """Test INSERT performance under load."""
    def worker(worker_id):
        queries = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            conn = psycopg2.connect(
                host='localhost', port=5432,
                database='supreme_octosuccotash_db',
                user='app_user', password='app_password'
            )
            cursor = conn.cursor()

            try:
                click_id = f'loadtest_click_{worker_id}_{int(time.time() * 1000000)}'
                cursor.execute("""
                    INSERT INTO events (id, event_type, event_data, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (click_id, 'load_test', '{"test": true}',))
                conn.commit()
                queries += 1
            except Exception as e:
                pass  # Ignore duplicate key errors
            finally:
                conn.close()

        # Cleanup
        try:
            conn = psycopg2.connect(
                host='localhost', port=5432,
                database='supreme_octosuccotash_db',
                user='app_user', password='app_password'
            )
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE event_type = 'load_test'")
            conn.commit()
            conn.close()
        except:
            pass

        return queries

    print(f"📝 Testing INSERT with {concurrency} concurrent connections...")

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        start_time = time.time()
        futures = [executor.submit(worker, i) for i in range(concurrency)]
        results = [future.result() for future in futures]
        total_time = time.time() - start_time

    total_queries = sum(results)
    qps = total_queries / total_time if total_time > 0 else 0

    print(f"  ✅ {total_queries} inserts in {total_time:.1f}s = {qps:.0f} QPS")
    return qps

def run_mixed_load(concurrency, duration=30):
    """Test mixed read/write load."""
    def worker(worker_id):
        queries = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            conn = psycopg2.connect(
                host='localhost', port=5432,
                database='supreme_octosuccotash_db',
                user='app_user', password='app_password'
            )
            cursor = conn.cursor()

            try:
                # Mix of operations
                if queries % 3 == 0:
                    # SELECT
                    cursor.execute("SELECT COUNT(*) FROM campaigns")
                    cursor.fetchone()
                elif queries % 3 == 1:
                    # UPDATE
                    cursor.execute("UPDATE campaigns SET updated_at = NOW() WHERE id = (SELECT id FROM campaigns LIMIT 1)")
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
            except Exception as e:
                pass
            finally:
                conn.close()

        # Cleanup
        try:
            conn = psycopg2.connect(
                host='localhost', port=5432,
                database='supreme_octosuccotash_db',
                user='app_user', password='app_password'
            )
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE event_type IN ('load_test', 'mixed_test')")
            conn.commit()
            conn.close()
        except:
            pass

        return queries

    print(f"🔄 Testing MIXED load with {concurrency} concurrent connections...")

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        start_time = time.time()
        futures = [executor.submit(worker, i) for i in range(concurrency)]
        results = [future.result() for future in futures]
        total_time = time.time() - start_time

    total_queries = sum(results)
    qps = total_queries / total_time if total_time > 0 else 0

    print(f"  ✅ {total_queries} operations in {total_time:.1f}s = {qps:.0f} QPS")
    return qps

def main():
    print("🚀 PostgreSQL Load Testing Results")
    print("=" * 50)

    test_concurrencies = [1, 2, 4, 8, 16]

    results = {
        'select': [],
        'insert': [],
        'mixed': []
    }

    for concurrency in test_concurrencies:
        print(f"\n🔥 Testing with {concurrency} concurrent connections")

        # SELECT test
        select_qps = run_select_load(concurrency, 10)  # 10 seconds
        results['select'].append((concurrency, select_qps))

        # INSERT test
        insert_qps = run_insert_load(concurrency, 10)
        results['insert'].append((concurrency, insert_qps))

        # MIXED test
        mixed_qps = run_mixed_load(concurrency, 10)
        results['mixed'].append((concurrency, mixed_qps))

        print()

    # Summary
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 50)

    for test_type, data in results.items():
        print(f"\n{test_type.upper()} Performance:")
        max_qps = max(data, key=lambda x: x[1])
        print(f"  Peak: {max_qps[1]:.0f} QPS at {max_qps[0]} concurrency")

        # Scaling efficiency
        if len(data) > 1:
            single_qps = data[0][1]
            max_concurrent_qps = max_qps[1]
            efficiency = (max_concurrent_qps / single_qps) * 100 / max_qps[0] if single_qps > 0 else 0
            print(f"    Scaling efficiency: {efficiency:.1f}%")
    # Recommendations
    print("\n💡 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 50)

    max_select = max(results['select'], key=lambda x: x[1])[1]
    max_insert = max(results['insert'], key=lambda x: x[1])[1]
    max_mixed = max(results['mixed'], key=lambda x: x[1])[1]

    print("🏆 Peak Performance Achieved:")
    print(f"  SELECT: {max_select:.0f} QPS")
    print(f"  INSERT: {max_insert:.0f} QPS")
    print(f"  MIXED:  {max_mixed:.0f} QPS")

    if max_select > 50000:
        print("  ✅ Excellent SELECT performance!")
    elif max_select > 10000:
        print("  ✅ Good SELECT performance!")
    else:
        print("  ⚠️  SELECT performance could be improved")

    if max_insert > 5000:
        print("  ✅ Excellent INSERT performance!")
    elif max_insert > 1000:
        print("  ✅ Good INSERT performance!")
    else:
        print("  ⚠️  INSERT performance could be improved")

    # Optimal pool size
    optimal_select = max(results['select'], key=lambda x: x[1]/x[0] if x[0] > 0 else 0)[0]
    optimal_insert = max(results['insert'], key=lambda x: x[1]/x[0] if x[0] > 0 else 0)[0]
    optimal_mixed = max(results['mixed'], key=lambda x: x[1]/x[0] if x[0] > 0 else 0)[0]

    recommended_pool = int((optimal_select + optimal_insert + optimal_mixed) / 3)
    print(f"  🎯 Recommended connection pool size: {recommended_pool}")

    print("\n✅ Load testing completed!")

if __name__ == "__main__":
    main()
