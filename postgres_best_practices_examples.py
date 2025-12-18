# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:04
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
PostgreSQL Best Practices Examples
Demonstrating correct usage patterns for high performance
"""

import csv
import io
import time
from datetime import datetime, timedelta

import psycopg2


class PostgresBestPracticesDemo:
    def __init__(self):
        self.conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'supreme_octosuccotash_db',
            'user': 'app_user',
            'password': 'app_password'
        }

    def demonstrate_prepared_statements(self):
        """Demonstrate prepared statements for long-running services."""
        print("🔧 Prepared Statements Demo")
        print("=" * 50)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Prepare statement once
        cursor.execute("""
            PREPARE get_campaign_events AS
            SELECT e.id, e.event_type, e.event_data, e.created_at
            FROM events e
            WHERE e.click_id = $1
            ORDER BY e.created_at DESC
            LIMIT $2
        """)

        click_ids = ['test_click_1', 'test_click_2', 'test_click_3']

        start_time = time.time()
        total_queries = 0

        # Execute prepared statement multiple times with different parameters
        for i in range(100):
            click_id = click_ids[i % len(click_ids)]
            limit = (i % 5) + 1  # 1-5

            cursor.execute("EXECUTE get_campaign_events (%s, %s)", (click_id, limit))
            results = cursor.fetchall()
            total_queries += 1

        exec_time = time.time() - start_time

        print(f"✅ Executed {total_queries} prepared queries in {exec_time:.3f}s")
        print(f"    Rate: {total_queries / exec_time:.0f} queries/sec")
        # Clean up
        cursor.execute("DEALLOCATE get_campaign_events")
        conn.close()

    def demonstrate_explain_analyze(self):
        """Demonstrate EXPLAIN ANALYZE for query profiling."""
        print("\n🔍 EXPLAIN ANALYZE Query Profiling")
        print("=" * 50)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Example query that might need optimization
        query = """
                SELECT c.id,
                       c.name,
                       c.status,
                       COUNT(e.id)       as event_count,
                       MAX(e.created_at) as last_event
                FROM campaigns c
                         LEFT JOIN events e ON c.id = e.click_id
                WHERE c.status = 'active'
                GROUP BY c.id, c.name, c.status
                ORDER BY event_count DESC LIMIT 10 \
                """

        print("Query:")
        print(query.strip())
        print("\nEXPLAIN ANALYZE output:")
        print("-" * 50)

        cursor.execute(f"EXPLAIN ANALYZE {query}")
        explain_result = cursor.fetchall()

        for row in explain_result:
            print(row[0])

        conn.close()

    def demonstrate_index_usage_analysis(self):
        """Demonstrate proper indexing strategies."""
        print("\n📊 Index Usage Analysis")
        print("=" * 50)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Check current index usage
        cursor.execute("""
                       SELECT schemaname,
                              relname                                      as table_name,
                              indexrelname                                 as index_name,
                              idx_scan,
                              idx_tup_read,
                              idx_tup_fetch,
                              pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                       FROM pg_stat_user_indexes
                       WHERE schemaname = 'public'
                       ORDER BY idx_scan DESC LIMIT 10
                       """)

        print("Most used indexes:")
        print("Table".ljust(20), "Index".ljust(30), "Scans".ljust(8), "Size")
        print("-" * 70)

        for row in cursor.fetchall():
            print(row[1].ljust(20), row[2].ljust(30), str(row[3]).ljust(8), row[6])

        # Demonstrate index impact on query performance
        print("\nTesting query with and without index...")

        # Query without index (if possible)
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'page_view'")
        count1 = cursor.fetchone()[0]
        time1 = time.time() - start_time

        # Same query with index (should be faster)
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'page_view'")
        count2 = cursor.fetchone()[0]
        time2 = time.time() - start_time

        print(f"Query result: {count1} events")
        print(f"Without index: {time1:.4f}s")
        print(f"With index: {time2:.4f}s")
        conn.close()

    def demonstrate_partitioning_setup(self):
        """Demonstrate table partitioning concepts."""
        print("\n🗂️  Table Partitioning Concepts")
        print("=" * 50)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Create a partitioned table example (if not exists)
        try:
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS events_partitioned
                           (
                               id
                               TEXT
                               NOT
                               NULL,
                               click_id
                               TEXT,
                               event_type
                               TEXT
                               NOT
                               NULL,
                               event_data
                               JSONB,
                               created_at
                               TIMESTAMP
                               NOT
                               NULL
                               DEFAULT
                               NOW
                           (
                           )
                               ) PARTITION BY RANGE
                           (
                               created_at
                           )
                           """)

            # Create partitions for different time ranges
            current_date = datetime.now()

            for i in range(3):  # Create 3 monthly partitions
                # Calculate proper date ranges
                partition_start_date = current_date.replace(day=1) + timedelta(days=30 * i)
                partition_end_date = current_date.replace(day=1) + timedelta(days=30 * (i + 1))

                partition_name = partition_start_date.strftime('y%Ym%m')

                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS events_partitioned_{partition_name}
                    PARTITION OF events_partitioned
                    FOR VALUES FROM ('{partition_start_date.strftime('%Y-%m-%d')}')
                    TO ('{partition_end_date.strftime('%Y-%m-%d')}')
                """)

            conn.commit()
            print("✅ Created partitioned table with monthly partitions")
            print("Partitions created for current and next 2 months")

        except Exception as e:
            print(f"Note: Partitioning setup skipped: {e}")
            conn.rollback()  # Rollback transaction on error
        else:
            conn.commit()

        # Show partition information (outside try block to avoid transaction issues)
        try:
            cursor.execute("""
                           SELECT tablename,
                                  pg_size_pretty(pg_relation_size(tablename::regclass)) as size
                           FROM pg_tables
                           WHERE tablename LIKE 'events_partitioned%'
                           ORDER BY tablename
                           """)

            partitions = cursor.fetchall()
            if partitions:
                print("\nPartition sizes:")
                for partition, size in partitions:
                    print(f"  {partition}: {size}")
        except Exception as e:
            print(f"Could not retrieve partition info: {e}")

        conn.close()

    def demonstrate_bulk_copy(self):
        """Demonstrate COPY command for bulk loading."""
        print("\n📤 Bulk COPY Loading Demo")
        print("=" * 50)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Create sample CSV data in memory
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)

        # Write CSV header
        writer.writerow(['id', 'event_type', 'event_data', 'created_at'])

        # Generate sample data
        for i in range(1000):
            writer.writerow([
                f'bulk_event_{i}',
                'page_view' if i % 3 == 0 else 'click' if i % 3 == 1 else 'conversion',
                f'{{"url": "/page{i}", "duration": {100 + i}}}',
                datetime.now().isoformat()
            ])

        csv_data.seek(0)

        # Use COPY to bulk load data
        start_time = time.time()

        cursor.copy_expert("""
            COPY events (id, event_type, event_data, created_at)
            FROM STDIN WITH CSV HEADER
        """, csv_data)

        conn.commit()
        copy_time = time.time() - start_time

        print("✅ Bulk loaded 1000 events using COPY")
        print(f"    Time: {copy_time:.2f}s")
        print(f"    Rate: {1000 / copy_time:.0f} rows/sec")
        # Compare with individual INSERTs
        print("\nComparing with individual INSERTs...")

        start_time = time.time()
        for i in range(100):  # Only 100 to keep demo reasonable
            cursor.execute("""
                           INSERT INTO events (id, event_type, event_data, created_at)
                           VALUES (%s, %s, %s, %s)
                           """, (
                               f'individual_event_{i}',
                               'test_event',
                               '{"method": "individual"}',
                               datetime.now()
                           ))

        conn.commit()
        insert_time = time.time() - start_time

        print(f"    Time: {insert_time:.2f}s")
        print(f"    Rate: {100 / insert_time:.0f} rows/sec")
        print(f"    COPY is {insert_time / copy_time:.1f}x faster than individual INSERTs")
        # Cleanup test data
        cursor.execute("DELETE FROM events WHERE id LIKE 'bulk_event_%' OR id LIKE 'individual_event_%'")
        conn.commit()

        conn.close()

    def demonstrate_connection_pooling(self):
        """Demonstrate connection pooling concepts."""
        print("\n🔗 Connection Pooling Concepts")
        print("=" * 50)

        print("Connection pooling benefits:")
        print("• Reuse database connections")
        print("• Reduce connection overhead")
        print("• Control maximum connections")
        print("• Handle connection failures gracefully")

        print("\nRecommended poolers:")
        print("• PgBouncer - lightweight connection pooler")
        print("• Pgpool-II - advanced middleware with load balancing")
        print("• Application-level pools (SQLAlchemy, HikariCP, etc.)")

        # Demonstrate connection reuse simulation
        print("\nSimulating connection reuse benefits...")

        # Simulate multiple operations with connection reuse
        conn = psycopg2.connect(**self.conn_params)

        start_time = time.time()
        operations = 0

        # Reuse single connection for multiple operations
        cursor = conn.cursor()
        for i in range(100):
            cursor.execute("SELECT COUNT(*) FROM campaigns")
            cursor.fetchone()
            operations += 1

        reuse_time = time.time() - start_time

        conn.close()

        print(f"✅ {operations} operations with connection reuse: {reuse_time:.3f}s")
        print(f"    Rate: {operations / reuse_time:.0f} operations/sec")

    def run_all_demos(self):
        """Run all demonstration functions."""
        print("🚀 PostgreSQL Best Practices Demonstrations")
        print("=" * 60)
        print(f"Started: {datetime.now()}")

        try:
            self.demonstrate_prepared_statements()
            self.demonstrate_explain_analyze()
            self.demonstrate_index_usage_analysis()
            self.demonstrate_partitioning_setup()
            self.demonstrate_bulk_copy()
            self.demonstrate_connection_pooling()

        except Exception as e:
            print(f"❌ Demo failed: {e}")

        print(f"\n✅ All demonstrations completed: {datetime.now()}")

        print("\n💡 Key Takeaways:")
        print("• Use prepared statements for repeated queries")
        print("• Always EXPLAIN ANALYZE before optimizing")
        print("• Index WHERE/JOIN/ORDER BY columns")
        print("• Partition large tables by time/hash")
        print("• Use COPY for bulk loading")
        print("• Implement connection pooling")
        print("• Continuously benchmark and iterate")


def main():
    demo = PostgresBestPracticesDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()
