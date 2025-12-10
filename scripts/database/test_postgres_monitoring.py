#!/usr/bin/env python3
"""Test PostgreSQL monitoring setup."""

import psycopg2
import time


def test_postgres_monitoring():
    """Test that PostgreSQL monitoring is working."""

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='supreme_octosuccotash_db',
            user='app_user',
            password='app_password'
        )
        cursor = conn.cursor()

        print("🔍 Testing PostgreSQL Query Monitoring")
        print("=" * 40)

        # 1. Test pg_stat_statements extension
        try:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements';")
            if cursor.fetchone():
                print("✅ pg_stat_statements extension is ENABLED")

                # Test query statistics
                cursor.execute("""
                    SELECT count(*) as total_queries,
                           avg(mean_time) as avg_query_time,
                           max(mean_time) as slowest_query_time
                    FROM pg_stat_statements
                    WHERE mean_time > 0;
                """)

                stats = cursor.fetchone()
                if stats and stats[0] > 0:
                    print(f"📊 Query Statistics:")
                    print(f"   Total tracked queries: {stats[0]}")
                    print(f"   Average query time: {stats[1]:.2f}ms")
                    print(f"   Slowest query: {stats[2]:.2f}ms")
                else:
                    print("📊 No query statistics available yet (run some queries first)")

            else:
                print("❌ pg_stat_statements extension not found")
                print("   Run: CREATE EXTENSION pg_stat_statements;")

        except Exception as e:
            print(f"❌ pg_stat_statements test failed: {e}")

        # 2. Test EXPLAIN functionality
        print("\n⚡ Testing EXPLAIN functionality:")
        try:
            cursor.execute("EXPLAIN SELECT COUNT(*) FROM clicks;")
            explain_result = cursor.fetchone()
            if explain_result:
                print("✅ EXPLAIN is working")
                print(f"   Sample plan: {explain_result[0][:100]}...")
            else:
                print("❌ EXPLAIN not working")
        except Exception as e:
            print(f"❌ EXPLAIN test failed: {e}")

        # 3. Generate some test queries to populate statistics
        print("\n🔄 Generating test queries for statistics...")
        try:
            # Run some queries to populate pg_stat_statements
            test_queries = [
                "SELECT COUNT(*) FROM clicks LIMIT 1;",
                "SELECT COUNT(*) FROM events LIMIT 1;",
                "SELECT COUNT(*) FROM conversions LIMIT 1;",
                "SELECT * FROM campaigns LIMIT 1;",
            ]

            for query in test_queries:
                cursor.execute(query)
                time.sleep(0.1)  # Small delay

            print("✅ Test queries executed")

            # Check if they appear in statistics
            cursor.execute("""
                SELECT query, calls, total_time
                FROM pg_stat_statements
                WHERE query LIKE '%SELECT COUNT(*) FROM%'
                ORDER BY total_time DESC
                LIMIT 3;
            """)

            recent_queries = cursor.fetchall()
            if recent_queries:
                print("📊 Recent query statistics:")
                for query, calls, total_time in recent_queries:
                    print(f"   {calls} calls, {total_time:.2f}ms total: {query[:60]}...")

        except Exception as e:
            print(f"❌ Test query generation failed: {e}")

        # 4. Check auto_explain configuration
        print("\n🔧 Checking auto_explain configuration:")
        try:
            cursor.execute("""
                SELECT name, setting
                FROM pg_settings
                WHERE name LIKE 'auto_explain.%'
                ORDER BY name;
            """)

            auto_settings = cursor.fetchall()
            if auto_settings:
                print("✅ auto_explain is configured:")
                for name, setting in auto_settings:
                    print(f"   {name}: {setting}")
            else:
                print("❌ auto_explain not configured")

        except Exception as e:
            print(f"❌ auto_explain check failed: {e}")

        conn.close()

        print("\n" + "="*40)
        print("🎯 PostgreSQL Monitoring Test Complete!")
        print("\n💡 Tips:")
        print("- Check PostgreSQL logs for auto_explain output")
        print("- Use pg_stat_statements for query performance analysis")
        print("- Monitor slow queries with log_min_duration_statement")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_postgres_monitoring()
