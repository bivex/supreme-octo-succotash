#!/usr/bin/env python3
"""Setup PostgreSQL monitoring and query analysis tools."""

import os
import re
from pathlib import Path


def setup_postgresql_monitoring():
    """Configure PostgreSQL for advanced query analysis."""

    config_path = Path(r"C:\Program Files\PostgreSQL\18\data\postgresql.conf")

    if not config_path.exists():
        print(f"❌ PostgreSQL config file not found: {config_path}")
        return False

    print("🔧 Setting up PostgreSQL Query Monitoring")
    print("=" * 50)

    try:
        # Read current config
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Backup original config
        backup_path = config_path.with_suffix('.conf.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup created: {backup_path}")

        # 1. Enable shared_preload_libraries
        if "shared_preload_libraries" not in content:
            # Add the setting if it doesn't exist
            content = content.replace(
                "#shared_preload_libraries = ''",
                "shared_preload_libraries = 'pg_stat_statements,auto_explain'"
            )
        else:
            # Update existing setting
            content = re.sub(
                r"shared_preload_libraries\s*=\s*'.*?'",
                "shared_preload_libraries = 'pg_stat_statements,auto_explain'",
                content
            )
        print("✅ Enabled shared_preload_libraries: pg_stat_statements,auto_explain")

        # 2. Configure pg_stat_statements
        pg_stat_config = """
# pg_stat_statements configuration
pg_stat_statements.max = 10000
pg_stat_statements.track = all
pg_stat_statements.track_utility = on
pg_stat_statements.save = on
"""

        if "pg_stat_statements.max" not in content:
            # Find a good place to add pg_stat_statements config (after shared_preload_libraries)
            content = content.replace(
                "shared_preload_libraries = 'pg_stat_statements,auto_explain'",
                "shared_preload_libraries = 'pg_stat_statements,auto_explain'\n\n# pg_stat_statements configuration\npg_stat_statements.max = 10000\npg_stat_statements.track = all\npg_stat_statements.track_utility = on\npg_stat_statements.save = on"
            )
        print("✅ Configured pg_stat_statements")

        # 3. Configure auto_explain
        auto_explain_config = """
# auto_explain configuration
auto_explain.log_min_duration = '100ms'
auto_explain.log_analyze = on
auto_explain.log_verbose = on
auto_explain.log_buffers = on
auto_explain.log_format = text
auto_explain.log_nested_statements = on
"""

        if "auto_explain.log_min_duration" not in content:
            # Add after pg_stat_statements config
            content = content.replace(
                "pg_stat_statements.save = on",
                "pg_stat_statements.save = on\n\n# auto_explain configuration\nauto_explain.log_min_duration = '100ms'\nauto_explain.log_analyze = on\nauto_explain.log_verbose = on\nauto_explain.log_buffers = on\nauto_explain.log_format = text\nauto_explain.log_nested_statements = on"
            )
        print("✅ Configured auto_explain")

        # 4. Enable additional logging for slow queries
        if "#log_min_duration_statement" in content:
            content = content.replace(
                "#log_min_duration_statement = -1",
                "log_min_duration_statement = '1s'  # Log queries taking more than 1 second"
            )
            print("✅ Enabled slow query logging")

        # Write updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("\n✅ PostgreSQL configuration updated successfully!")
        print("\n🔄 NEXT STEPS:")
        print("1. Restart PostgreSQL service:")
        print('   - Run: net stop postgresql-x64-18')
        print('   - Run: net start postgresql-x64-18')
        print("   OR use pgAdmin: Server > Reload Configuration")
        print("\n2. Enable pg_stat_statements extension:")
        print("   psql -U postgres -d supreme_octosuccotash_db -c 'CREATE EXTENSION IF NOT EXISTS pg_stat_statements;'")
        print("\n3. Test the configuration:")
        print("   python test_postgres_monitoring.py")

        return True

    except Exception as e:
        print(f"❌ Failed to update PostgreSQL config: {e}")
        return False


def create_test_script():
    """Create a test script for PostgreSQL monitoring."""

    test_script = '''#!/usr/bin/env python3
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
'''

    with open('test_postgres_monitoring.py', 'w', encoding='utf-8') as f:
        f.write(test_script)

    print("✅ Created test script: test_postgres_monitoring.py")


if __name__ == "__main__":
    success = setup_postgresql_monitoring()
    if success:
        create_test_script()
        print("\n🚀 PostgreSQL monitoring setup complete!")
        print("📋 Next: Restart PostgreSQL and run: python test_postgres_monitoring.py")
