
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Simple PostgreSQL Query Analysis Tool."""

import psycopg2
import json


def analyze_database_performance():
    """Analyze database performance and provide recommendations."""

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='supreme_octosuccotash_db',
            user='app_user',
            password='app_password'
        )
        cursor = conn.cursor()

        print("🔍 PostgreSQL Database Performance Analysis")
        print("=" * 50)

        # 1. Check table sizes and row counts
        print("\n📊 Table Statistics:")
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)

        tables = cursor.fetchall()
        for table in tables:
            print(f"\n{table[1]}:")
            print(f"  Total size: {table[2]}")
            print(f"  Table size: {table[3]}")
            print(f"  Live rows: {table[7]:,}")
            print(f"  Dead rows: {table[8]:,}")
            print(f"  Inserts: {table[4]:,}")
            print(f"  Updates: {table[5]:,}")
            print(f"  Deletes: {table[6]:,}")

        # 2. Check indexes
        print("\n📋 Index Analysis:")
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as size,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
            ORDER BY pg_relation_size(indexrelid) DESC;
        """)

        indexes = cursor.fetchall()
        if indexes:
            print("Existing indexes:")
            for index in indexes:
                print(f"  {index[2]} on {index[1]}: {index[3]} (scans: {index[4]:,})")
        else:
            print("❌ No indexes found!")
            print("  Recommendation: Add indexes on frequently queried columns")

        # 3. Check for missing indexes on foreign keys
        print("\n🔗 Foreign Key Analysis:")
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public';
        """)

        fks = cursor.fetchall()
        if fks:
            print("Foreign keys found:")
            for fk in fks:
                print(f"  {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")

                # Check if index exists on FK column
                cursor.execute("""
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND tablename = %s
                      AND indexdef LIKE %s;
                """, (fk[0], f'%{fk[1]}%'))

                has_index = cursor.fetchone()
                if not has_index:
                    print(f"    ⚠️  Missing index on FK column: {fk[0]}.{fk[1]}")
        else:
            print("No foreign keys found")

        # 4. Simple EXPLAIN for common query patterns
        print("\n⚡ Query Performance Analysis:")

        # Test some basic queries
        test_queries = [
            ("SELECT COUNT(*) FROM clicks", "Count all clicks"),
            ("SELECT COUNT(*) FROM events", "Count all events"),
            ("SELECT COUNT(*) FROM conversions", "Count all conversions"),
        ]

        for query, description in test_queries:
            try:
                print(f"\nAnalyzing: {description}")

                # Get row count first
                cursor.execute(query)
                count = cursor.fetchone()[0]
                print(f"  Row count: {count:,}")

                # EXPLAIN the query
                cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                explain = cursor.fetchone()[0]

                if explain and len(explain) > 0:
                    plan = explain[0]['Plan']
                    total_cost = plan.get('Total Cost', 'N/A')
                    print(".2f")

            except Exception as e:
                print(f"  Error: {e}")

        # 5. Recommendations
        print("\n💡 Performance Recommendations:")
        print("=" * 30)

        recommendations = []

        # Check if we have data
        if tables and any(t[7] > 0 for t in tables):  # Check live rows
            recommendations.append("✅ Database has data - good for analysis")

        # Index recommendations
        if not indexes:
            recommendations.append("🔴 CRITICAL: No indexes found! Add indexes on:")
            recommendations.append("   - clicks.campaign_id")
            recommendations.append("   - clicks.created_at")
            recommendations.append("   - events.click_id")
            recommendations.append("   - events.created_at")
            recommendations.append("   - conversions.click_id")
            recommendations.append("   - conversions.created_at")

        # Check for dead rows (needing VACUUM)
        dead_rows_total = sum(t[8] for t in tables)
        if dead_rows_total > 1000:
            recommendations.append(f"🧹 High dead rows ({dead_rows_total:,}) - consider VACUUM")

        # Connection pool
        recommendations.append("🔧 Connection pool: Increased to 100 connections")

        # Monitoring
        recommendations.append("📊 Enable monitoring:")
        recommendations.append("   - pg_stat_statements (requires superuser)")
        recommendations.append("   - auto_explain for slow queries")

        for rec in recommendations:
            print(f"  {rec}")

        conn.close()

    except Exception as e:
        print(f"❌ Analysis failed: {e}")


def create_performance_indexes():
    """Create recommended performance indexes."""

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='supreme_octosuccotash_db',
            user='app_user',
            password='app_password'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("\n🔧 Creating Performance Indexes...")

        indexes_to_create = [
            ("idx_clicks_campaign_created", "clicks", "campaign_id, created_at DESC"),
            ("idx_clicks_created_at", "clicks", "created_at DESC"),
            ("idx_events_click_created", "events", "click_id, created_at DESC"),
            ("idx_events_created_at", "events", "created_at DESC"),
            ("idx_conversions_click", "conversions", "click_id"),
            ("idx_conversions_created", "conversions", "created_at DESC"),
            ("idx_campaigns_status", "campaigns", "status"),
        ]

        for index_name, table_name, columns in indexes_to_create:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns});")
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"❌ Failed to create {index_name}: {e}")

        conn.close()
        print("\n✅ Index creation completed!")

    except Exception as e:
        print(f"❌ Failed to create indexes: {e}")


if __name__ == "__main__":
    analyze_database_performance()

    print("\n" + "="*50)
    response = input("Create recommended performance indexes? (y/n): ")
    if response.lower() == 'y':
        create_performance_indexes()
    else:
        print("Index creation skipped")

    print("\n📄 Analysis complete! Check recommendations above.")
