# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:33
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Analyze PostgreSQL query plans to understand index usage.
"""

import psycopg2


def analyze_query_plans():
    """Analyze query execution plans."""

    conn = psycopg2.connect(
        'dbname=supreme_octosuccotash_db user=app_user password=app_password host=localhost port=5432'
    )
    cur = conn.cursor()

    try:
        print("🔍 QUERY PLAN ANALYSIS")
        print("=" * 50)

        # Check table sizes
        tables = ['campaigns', 'clicks', 'analytics_cache', 'events']
        print("📊 Table Sizes:")
        for table in tables:
            cur.execute(f'SELECT COUNT(*) FROM {table}')
            count = cur.fetchone()[0]
            print(f"   {table}: {count} rows")

        print("\n📋 Query Plan Analysis:")

        # Test campaign query
        print("\n1. Campaign lookup by ID:")
        cur.execute("EXPLAIN ANALYZE SELECT * FROM campaigns WHERE id = 'camp_000'")
        plan = cur.fetchall()
        for line in plan:
            print(f"   {line[0]}")

        # Test clicks query by campaign_id
        print("\n2. Clicks lookup by campaign_id:")
        cur.execute("EXPLAIN ANALYZE SELECT * FROM clicks WHERE campaign_id = 'camp_000'")
        plan = cur.fetchall()
        for line in plan:
            print(f"   {line[0]}")

        # Test analytics query
        print("\n3. Analytics lookup by campaign_id:")
        cur.execute("EXPLAIN ANALYZE SELECT * FROM analytics_cache WHERE campaign_id = 'camp_000'")
        plan = cur.fetchall()
        for line in plan:
            print(f"   {line[0]}")

        # Test analytics by cache_key
        print("\n4. Analytics lookup by cache_key:")
        cur.execute("EXPLAIN ANALYZE SELECT * FROM analytics_cache WHERE cache_key = 'test_metric_0'")
        plan = cur.fetchall()
        for line in plan:
            print(f"   {line[0]}")

        # Check PostgreSQL settings that affect index usage
        print("\n⚙️ PostgreSQL Index Settings:")
        settings_to_check = [
            'random_page_cost',
            'seq_page_cost',
            'cpu_tuple_cost',
            'cpu_index_tuple_cost',
            'effective_cache_size'
        ]

        for setting in settings_to_check:
            cur.execute(f"SHOW {setting}")
            value = cur.fetchone()[0]
            print(f"   {setting}: {value}")

        # Check if indexes exist
        print("\n📊 Index Existence Check:")
        cur.execute("""
                    SELECT schemaname, tablename, indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname LIKE 'idx_%'
                    ORDER BY indexname
                    """)

        indexes = cur.fetchall()
        for schema, table, index, definition in indexes:
            print(f"   ✓ {schema}.{index} on {table}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    analyze_query_plans()
