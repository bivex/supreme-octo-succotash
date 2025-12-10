#!/usr/bin/env python3
"""Check PostgreSQL configuration for query analysis."""

import psycopg2
import json


def check_postgres_config():
    """Check PostgreSQL configuration and extensions."""
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

        print('=== PostgreSQL Configuration Check ===')

        # Check if pg_stat_statements is available
        cursor.execute("""
            SELECT name, setting, unit, context
            FROM pg_settings
            WHERE name LIKE '%stat%' OR name LIKE '%explain%' OR name LIKE '%log_%'
            ORDER BY name;
        """)

        settings = cursor.fetchall()
        print(f'\nFound {len(settings)} relevant settings:')
        for setting in settings:
            print(f'{setting[0]}: {setting[1]} {setting[2] or ""} (context: {setting[3]})')

        # Check if pg_stat_statements extension exists
        cursor.execute("""
            SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements';
        """)

        if cursor.fetchone():
            print('\n✅ pg_stat_statements extension is ENABLED')

            # Show top queries if extension is enabled
            print('\n=== Top 10 Slowest Queries (pg_stat_statements) ===')
            try:
                cursor.execute("""
                    SELECT
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT 10;
                """)

                queries = cursor.fetchall()
                if queries:
                    for i, query in enumerate(queries, 1):
                        print(f'\n{i}. Query: {query[0][:100]}...')
                        print('.2f')
                        print(f'   Mean time: {query[3]:.2f}ms')
                        print(f'   Rows returned: {query[4]}')
                else:
                    print('No query statistics available yet')
            except Exception as e:
                print(f'Error getting query stats: {e}')

        else:
            print('\n❌ pg_stat_statements extension is NOT enabled')
            print('To enable: CREATE EXTENSION pg_stat_statements;')

        # Check auto_explain settings
        print('\n=== Auto Explain Configuration ===')
        cursor.execute("""
            SELECT name, setting
            FROM pg_settings
            WHERE name LIKE 'auto_explain.%'
            ORDER BY name;
        """)

        auto_explain_settings = cursor.fetchall()
        if auto_explain_settings:
            print('Auto explain settings:')
            for setting in auto_explain_settings:
                print(f'  {setting[0]}: {setting[1]}')
        else:
            print('Auto explain not configured')

        conn.close()

    except Exception as e:
        print(f'Connection error: {e}')


def enable_query_monitoring():
    """Enable query monitoring extensions and settings."""
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

        print('=== Enabling Query Monitoring ===')

        # Enable pg_stat_statements
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
            print('✅ pg_stat_statements extension enabled')
        except Exception as e:
            print(f'❌ Failed to enable pg_stat_statements: {e}')

        # Configure auto_explain (requires restart)
        print('\n📝 To enable auto_explain, add to postgresql.conf:')
        print('  shared_preload_libraries = \'pg_stat_statements,auto_explain\'')
        print('  auto_explain.log_min_duration = \'100ms\'')
        print('  auto_explain.log_analyze = on')
        print('  auto_explain.log_verbose = on')
        print('  auto_explain.log_format = text')

        conn.close()

    except Exception as e:
        print(f'Connection error: {e}')


def analyze_sample_queries():
    """Analyze some sample queries from the application."""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='supreme_octosuccotash_db',
            user='app_user',
            password='app_password'
        )
        cursor = conn.cursor()

        print('\n=== Sample Query Analysis ===')

        # Sample queries that might be slow
        sample_queries = [
            "SELECT * FROM clicks WHERE campaign_id = 1 LIMIT 10;",
            "SELECT COUNT(*) FROM events WHERE created_at > NOW() - INTERVAL '1 hour';",
            "SELECT * FROM conversions ORDER BY created_at DESC LIMIT 5;",
        ]

        for query in sample_queries:
            print(f'\nAnalyzing: {query}')

            try:
                # Get EXPLAIN output
                cursor.execute(f"EXPLAIN ANALYZE {query}")
                explain_result = cursor.fetchall()

                print('EXPLAIN ANALYZE output:')
                for line in explain_result:
                    print(f'  {line[0]}')

            except Exception as e:
                print(f'  Error analyzing query: {e}')

        conn.close()

    except Exception as e:
        print(f'Connection error: {e}')


if __name__ == "__main__":
    check_postgres_config()
    enable_query_monitoring()
    analyze_sample_queries()
