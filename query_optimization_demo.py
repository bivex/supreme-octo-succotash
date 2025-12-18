# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:02
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
PostgreSQL Query Optimization Demo
Shows how to properly analyze and optimize queries using EXPLAIN ANALYZE
"""

import time
from datetime import datetime

import psycopg2


class QueryOptimizerDemo:
    def __init__(self):
        self.conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'supreme_octosuccotash_db',
            'user': 'app_user',
            'password': 'app_password'
        }

    def create_test_data(self):
        """Create test data for optimization demos."""
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Create larger test dataset
        print("Creating test data for optimization demos...")

        # Add more test campaigns
        for i in range(50, 100):
            cursor.execute("""
                           INSERT INTO campaigns (id, name, description, status, cost_model,
                                                  payout_amount, payout_currency, safe_page_url, offer_page_url,
                                                  daily_budget_amount, daily_budget_currency,
                                                  total_budget_amount, total_budget_currency,
                                                  start_date, end_date, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                   %s) ON CONFLICT (id) DO NOTHING
                           """, (
                               f'opt_campaign_{i}',
                               f'Optimization Test Campaign {i}',
                               f'Description for optimization test {i}',
                               'active' if i % 3 != 0 else 'paused',
                               'CPA',
                               15.0 + (i % 10), 'USD',
                               f'https://example.com/safe_opt_{i}',
                               f'https://example.com/offer_opt_{i}',
                               200.0 + (i % 50), 'USD',
                               5000.0 + (i % 1000), 'USD',
                               datetime.now(),
                               datetime.now().replace(day=28),
                               datetime.now(),
                               datetime.now()
                           ))

        # Add more test events
        for i in range(500):
            campaign_id = f'opt_campaign_{50 + (i % 50)}'
            cursor.execute("""
                           INSERT INTO events (id, click_id, event_type, event_data, created_at)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (
                               f'opt_event_{i}',
                               f'opt_click_{i % 100}',
                               ['page_view', 'click', 'conversion'][i % 3],
                               f'{{"campaign": "{campaign_id}", "position": {i % 10}}}',
                               datetime.now()
                           ))

        conn.commit()
        conn.close()
        print("✅ Test data created")

    def analyze_query_performance(self, query, description):
        """Analyze query performance with EXPLAIN ANALYZE."""
        print(f"\n🔍 {description}")
        print("=" * 60)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Get execution plan
        print("EXPLAIN output:")
        cursor.execute(f"EXPLAIN {query}")
        plan = cursor.fetchall()
        for row in plan:
            print(f"  {row[0]}")

        # Execute query and measure time
        start_time = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        exec_time = time.time() - start_time

        print(f"\nActual execution:")
        print(f"  Rows returned: {len(results)}")
        print(".4f"
        print(".0f"
        conn.close()
        return exec_time

    def demonstrate_index_impact(self):
        """Demonstrate the impact of indexes on query performance."""
        print("\n📊 Index Impact Demonstration")
        print("=" * 60)

        # Test query without index
        query1 = "SELECT * FROM campaigns WHERE status = 'active'"

        print("Query: SELECT * FROM campaigns WHERE status = 'active'")
        time1 = self.analyze_query_performance(query1, "Without index optimization")

        # Check if index exists
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT indexname
                       FROM pg_indexes
                       WHERE tablename = 'campaigns'
                         AND indexdef LIKE '%status%'
                       """)

        if not cursor.fetchall():
            print("\n⚠️  No index on status column!")
            print("Creating index...")
            cursor.execute("CREATE INDEX CONCURRENTLY idx_campaigns_status_demo ON campaigns (status)")
            conn.commit()
            print("✅ Index created")
        else:
            print("\n✅ Index on status column exists")

        conn.close()

        # Test query with index
        time2 = self.analyze_query_performance(query1, "With index optimization")

        if time2 > 0:
            improvement = (time1 - time2) / time1 * 100
            print(".1f"

    def demonstrate_join_optimization(self):
        """Demonstrate JOIN query optimization."""
        print("\n🔗 JOIN Optimization")
        print("=" * 60)

        # Query with JOIN
        join_query = """
                     SELECT c.name,
                            c.status,
                            COUNT(e.id)       as event_count,
                            MAX(e.created_at) as last_event
                     FROM campaigns c
                              LEFT JOIN events e ON c.id = e.click_id
                     WHERE c.status = 'active'
                     GROUP BY c.id, c.name, c.status
                     ORDER BY event_count DESC LIMIT 5 \
                     """

        print("JOIN Query Analysis:")
        self.analyze_query_performance(join_query, "Campaign events JOIN query")

        # Check indexes on JOIN columns
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        print("\nChecking indexes for JOIN optimization:")
        cursor.execute("""
                       SELECT indexname, indexdef
                       FROM pg_indexes
                       WHERE tablename IN ('campaigns', 'events')
                         AND (indexdef LIKE '%id%' OR indexdef LIKE '%click_id%')
                       """)

        indexes = cursor.fetchall()
        if indexes:
            print("✅ JOIN indexes found:")
            for name, definition in indexes:
                print(f"  {name}: {definition}")
        else:
            print("⚠️  No indexes on JOIN columns!")
            print("Consider adding:")
            print("  CREATE INDEX ON campaigns (id);")
            print("  CREATE INDEX ON events (click_id);")

        conn.close()

    def demonstrate_order_by_optimization(self):
        """Demonstrate ORDER BY optimization."""
        print("\n📈 ORDER BY Optimization")
        print("=" * 60)

        # Query with ORDER BY
        order_query = """
                      SELECT id, name, created_at, status
                      FROM campaigns
                      WHERE status = 'active'
                      ORDER BY created_at DESC LIMIT 10 \
                      """

        print("ORDER BY Query Analysis:")
        self.analyze_query_performance(order_query, "ORDER BY created_at query")

        # Check if index supports ORDER BY
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT indexname, indexdef
                       FROM pg_indexes
                       WHERE tablename = 'campaigns'
                         AND indexdef LIKE '%created_at%'
                       """)

        if cursor.fetchall():
            print("✅ Index on created_at exists (good for ORDER BY)")
        else:
            print("⚠️  No index on created_at!")
            print("ORDER BY will use slow sort operation")
            print("Consider: CREATE INDEX ON campaigns (created_at DESC);")

        conn.close()

    def demonstrate_selectivity_analysis(self):
        """Analyze query selectivity and index effectiveness."""
        print("\n🎯 Selectivity Analysis")
        print("=" * 60)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Analyze column selectivity
        cursor.execute("""
                       SELECT column_name,
                              n_distinct,
                              CASE
                                  WHEN n_distinct > 0 THEN
                                      ROUND((n_distinct::float / (SELECT COUNT(*) FROM campaigns)) * 100, 2)
                                  ELSE 0 END as selectivity_percent
                       FROM information_schema.columns c
                                JOIN pg_stats s ON s.tablename = c.table_name AND s.attname = c.column_name
                       WHERE c.table_name = 'campaigns'
                         AND c.column_name IN ('status', 'cost_model', 'created_at')
                       ORDER BY selectivity_percent DESC
                       """)

        print("Column selectivity analysis:")
        print("Column".ljust(15), "Distinct Values", "Selectivity %")
        print("-" * 45)

        for row in cursor.fetchall():
            col, distinct, selectivity = row
            print(f"{col:<15} {distinct:<15} {selectivity}%")

        print("\n💡 Selectivity Guidelines:")
        print("• High selectivity (>10%): Usually good for indexes")
        print("• Low selectivity (<1%): Index might not help")
        print("• Very low: Consider partial indexes or different approaches")

        conn.close()

    def cleanup_test_data(self):
        """Clean up test data."""
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM events WHERE id LIKE 'opt_event_%'")
        cursor.execute("DELETE FROM campaigns WHERE id LIKE 'opt_campaign_%'")

        # Optionally drop demo index
        try:
            cursor.execute("DROP INDEX IF EXISTS idx_campaigns_status_demo")
        except:
            pass

        conn.commit()
        conn.close()
        print("✅ Test data cleaned up")

    def run_optimization_analysis(self):
        """Run complete query optimization analysis."""
        print("🚀 PostgreSQL Query Optimization Analysis")
        print("=" * 60)
        print(f"Started: {datetime.now()}")

        try:
            self.create_test_data()
            self.demonstrate_index_impact()
            self.demonstrate_join_optimization()
            self.demonstrate_order_by_optimization()
            self.demonstrate_selectivity_analysis()

        except Exception as e:
            print(f"❌ Analysis failed: {e}")

        finally:
            self.cleanup_test_data()

        print(f"\n✅ Optimization analysis completed: {datetime.now()}")

        print("\n🎯 Optimization Best Practices:")
        print("1. Always EXPLAIN ANALYZE before optimizing")
        print("2. Index WHERE, JOIN, and ORDER BY columns")
        print("3. Consider selectivity when choosing indexes")
        print("4. Monitor index usage with pg_stat_user_indexes")
        print("5. Balance read performance vs write overhead")
        print("6. Use partial indexes for selective conditions")
        print("7. Consider composite indexes for multi-column queries")


def main():
    optimizer = QueryOptimizerDemo()
    optimizer.run_optimization_analysis()


if __name__ == "__main__":
    main()
