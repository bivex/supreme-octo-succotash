# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:18
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Comprehensive PostgreSQL performance audit script.
Checks cache hit ratio, slow queries, index usage, and provides optimization recommendations.
"""

from datetime import datetime

import psycopg2


class DatabaseAuditor:
    def __init__(self):
        self.conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'supreme_octosuccotash_db',
            'user': 'app_user',
            'password': 'app_password'
        }

    def connect(self):
        """Establish database connection."""
        try:
            return psycopg2.connect(**self.conn_params)
        except psycopg2.Error as e:
            print(f"❌ Connection failed: {e}")
            return None

    def check_postgres_config(self):
        """Check PostgreSQL configuration settings."""
        print("🔧 PostgreSQL Configuration Audit")
        print("=" * 50)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT name, setting, unit, context
                           FROM pg_settings
                           WHERE name IN (
                                          'shared_buffers', 'effective_cache_size', 'work_mem',
                                          'maintenance_work_mem', 'checkpoint_completion_target',
                                          'wal_buffers', 'default_statistics_target', 'random_page_cost',
                                          'effective_io_concurrency', 'max_connections'
                               )
                           ORDER BY name
                           """)

            print("Current PostgreSQL settings:")
            for row in cursor.fetchall():
                name, setting, unit, context = row
                unit_str = f" {unit}" if unit else ""
                print(f"  {name:30} = {setting:>8}{unit_str} ({context})")

            # Recommendations
            print("\n📋 Recommendations:")
            cursor.execute("SELECT setting FROM pg_settings WHERE name = 'shared_buffers'")
            shared_buffers = int(cursor.fetchone()[0])

            if shared_buffers < 131072:  # Less than 1GB (131072 * 8KB)
                print("  ⚠️  shared_buffers is low (< 1GB). Consider increasing to 25-40% of RAM")

            cursor.execute("SELECT setting FROM pg_settings WHERE name = 'effective_cache_size'")
            cache_size = int(cursor.fetchone()[0])

            if cache_size < shared_buffers * 4:
                print("  ⚠️  effective_cache_size should be 3-4x shared_buffers")

        finally:
            conn.close()

    def check_cache_hit_ratio(self):
        """Check cache hit ratio for all tables."""
        print("\n💾 Cache Hit Ratio Analysis")
        print("=" * 50)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT relname        as table_name,
                                  heap_blks_read,
                                  heap_blks_hit,
                                  idx_blks_read,
                                  idx_blks_hit,
                                  CASE
                                      WHEN (heap_blks_hit + heap_blks_read) > 0
                                          THEN ROUND((heap_blks_hit::numeric / (heap_blks_hit + heap_blks_read)) * 100, 2)
                                      ELSE 0 END as heap_hit_ratio,
                                  CASE
                                      WHEN (idx_blks_hit + idx_blks_read) > 0
                                          THEN ROUND((idx_blks_hit::numeric / (idx_blks_hit + idx_blks_read)) * 100, 2)
                                      ELSE 0 END as idx_hit_ratio
                           FROM pg_statio_user_tables
                           WHERE heap_blks_hit + heap_blks_read + idx_blks_hit + idx_blks_read > 0
                           ORDER BY heap_blks_hit + heap_blks_read + idx_blks_hit + idx_blks_read DESC LIMIT 15
                           """)

            results = cursor.fetchall()

            if not results:
                print("No table access statistics available yet.")
                return

            print("Top 15 tables by cache access:")
            print(f"{'Table':<25} {'Heap Hit %':>12} {'Index Hit %':>12} {'Heap Reads':>12} {'Index Reads':>12}")
            print("-" * 75)

            total_heap_reads = 0
            total_heap_hits = 0
            total_idx_reads = 0
            total_idx_hits = 0

            for row in results:
                table_name, heap_reads, heap_hits, idx_reads, idx_hits, heap_ratio, idx_ratio = row
                print(f"{table_name:<25} {heap_ratio:>12.1f} {idx_ratio:>12.1f} {heap_reads:>12} {idx_reads:>12}")

                total_heap_reads += heap_reads
                total_heap_hits += heap_hits
                total_idx_reads += idx_reads
                total_idx_hits += idx_hits

            # Overall cache hit ratio
            overall_heap_ratio = (total_heap_hits / (total_heap_hits + total_heap_reads) * 100) if (
                                                                                                               total_heap_hits + total_heap_reads) > 0 else 0
            overall_idx_ratio = (total_idx_hits / (total_idx_hits + total_idx_reads) * 100) if (
                                                                                                           total_idx_hits + total_idx_reads) > 0 else 0

            print("-" * 75)
            print(f"{'OVERALL':<25} {overall_heap_ratio:>12.1f} {overall_idx_ratio:>12.1f}")

            # Recommendations
            print("\n📋 Cache Hit Ratio Recommendations:")
            if overall_heap_ratio < 99:
                print("  ⚠️  Heap cache hit ratio < 99%. Consider increasing shared_buffers")
            else:
                print("  ✅ Heap cache hit ratio is excellent")

            if overall_idx_ratio < 99:
                print("  ⚠️  Index cache hit ratio < 99%. Consider increasing shared_buffers or effective_cache_size")
            else:
                print("  ✅ Index cache hit ratio is excellent")

        finally:
            conn.close()

    def check_pg_stat_statements(self):
        """Check if pg_stat_statements is enabled."""
        print("\n📊 pg_stat_statements Extension Check")
        print("=" * 50)

        # Try to connect as postgres to check extensions
        postgres_conn_params = self.conn_params.copy()
        postgres_conn_params['user'] = 'postgres'
        postgres_conn_params['password'] = 'postgres'
        postgres_conn_params['database'] = 'postgres'

        try:
            conn = psycopg2.connect(**postgres_conn_params)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name, installed_version FROM pg_available_extensions WHERE name = 'pg_stat_statements'")
            result = cursor.fetchone()

            if result:
                name, version = result
                if version:
                    print(f"✅ pg_stat_statements is installed (version {version})")

                    # Check if it's in shared_preload_libraries
                    cursor.execute("SELECT setting FROM pg_settings WHERE name = 'shared_preload_libraries'")
                    preload = cursor.fetchone()[0]

                    if 'pg_stat_statements' in preload:
                        print("✅ pg_stat_statements is in shared_preload_libraries")
                    else:
                        print("❌ pg_stat_statements is NOT in shared_preload_libraries")
                        print("   Add 'pg_stat_statements' to shared_preload_libraries in postgresql.conf")

                    # Check if extension is created in the database
                    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements'")
                    if cursor.fetchone():
                        print("✅ pg_stat_statements extension is created in database")
                    else:
                        print("❌ pg_stat_statements extension is NOT created in database")
                        print("   Run: CREATE EXTENSION pg_stat_statements;")

                else:
                    print("❌ pg_stat_statements is available but not installed")
                    print("   To install: CREATE EXTENSION pg_stat_statements;")
            else:
                print("❌ pg_stat_statements extension is not available")

            conn.close()

        except psycopg2.Error as e:
            print(f"❌ Cannot check extensions as postgres user: {e}")
            print("   Make sure postgres user password is 'postgres' or check permissions")

    def analyze_query_performance(self):
        """Analyze query performance using pg_stat_statements."""
        print("\n🐌 Slow Query Analysis")
        print("=" * 50)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Check if pg_stat_statements is available
            cursor.execute("""
                           SELECT EXISTS (SELECT 1
                                          FROM information_schema.tables
                                          WHERE table_schema = 'public'
                                            AND table_name = 'pg_stat_statements')
                           """)

            if not cursor.fetchone()[0]:
                print("❌ pg_stat_statements is not available in this database")
                print("   To enable: CREATE EXTENSION pg_stat_statements;")
                return

            # Get slow queries
            cursor.execute("""
                           SELECT query,
                                  calls,
                                  total_exec_time,
                                  mean_exec_time, rows, shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written
                           FROM pg_stat_statements
                           WHERE mean_exec_time > 10 -- queries taking more than 10ms on average
                           ORDER BY mean_exec_time DESC
                               LIMIT 10
                           """)

            slow_queries = cursor.fetchall()

            if not slow_queries:
                print("✅ No slow queries found (>10ms average)")
                return

            print("Top 10 slowest queries (>10ms average):")
            print(f"{'Calls':<8} {'Mean Time':<12} {'Total Time':<12} {'Rows':<8} {'Query':<50}")
            print("-" * 100)

            for query, calls, total_exec_time, mean_exec_time, rows, blk_hit, blk_read, temp_read, temp_written in slow_queries:
                # Truncate query for display
                short_query = query.replace('\n', ' ').strip()[:47] + '...' if len(query) > 50 else query.replace('\n',
                                                                                                                  ' ').strip()
                print(f"{calls:<8} {mean_exec_time:<12.2f} {total_exec_time:<12.2f} {rows:<8} {short_query}")

            print("\n📋 Slow Query Recommendations:")
            print("  🔍 Review queries taking >100ms and consider:")
            print("     - Adding missing indexes")
            print("     - Rewriting complex queries")
            print("     - Using query result caching")
            print("     - Optimizing JOIN operations")

        finally:
            conn.close()

    def check_index_usage(self):
        """Check index usage and identify unused indexes."""
        print("\n📈 Index Usage Analysis")
        print("=" * 50)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Get index usage statistics
            cursor.execute("""
                           SELECT schemaname,
                                  relname                                      as table_name,
                                  indexrelname                                 as index_name,
                                  idx_scan,
                                  idx_tup_read,
                                  idx_tup_fetch,
                                  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                           FROM pg_stat_user_indexes
                           ORDER BY idx_scan DESC, pg_relation_size(indexrelid) DESC
                           """)

            indexes = cursor.fetchall()

            if not indexes:
                print("No index statistics available")
                return

            # Used indexes (scanned at least once)
            used_indexes = [idx for idx in indexes if idx[3] > 0]
            unused_indexes = [idx for idx in indexes if idx[3] == 0]

            print(f"📊 Index Statistics: {len(used_indexes)} used, {len(unused_indexes)} unused")
            print()

            if used_indexes:
                print("Most used indexes:")
                print(f"{'Table':<20} {'Index':<30} {'Scans':<8} {'Size':<10}")
                print("-" * 70)

                for schema, table, index, scans, tup_read, tup_fetch, size in used_indexes[:10]:
                    print(f"{table:<20} {index:<30} {scans:<8} {size:<10}")

            if unused_indexes:
                print("\n⚠️  Potentially unused indexes:")
                print(f"{'Table':<20} {'Index':<30} {'Size':<10}")
                print("-" * 60)

                total_unused_size = 0
                for schema, table, index, scans, tup_read, tup_fetch, size in unused_indexes:
                    print(f"{table:<20} {index:<30} {size:<10}")
                    # Estimate size for recommendations
                    if 'MB' in size:
                        total_unused_size += float(size.replace(' MB', '')) * 1024 * 1024
                    elif 'kB' in size:
                        total_unused_size += float(size.replace(' kB', '')) * 1024
                    elif 'bytes' in size:
                        total_unused_size += float(size.replace(' bytes', ''))

                print(f"\nTotal unused index size: ~{total_unused_size / (1024 * 1024):.1f} MB")

                print("\n📋 Index Recommendations:")
                print("  🗑️  Consider removing unused indexes to:")
                print("     - Reduce INSERT/UPDATE overhead")
                print("     - Save disk space")
                print("     - Speed up VACUUM operations")
                print("  ⚠️  Monitor index usage after removal for at least 1-2 weeks")

        finally:
            conn.close()

    def generate_report(self):
        """Generate complete performance audit report."""
        print("🚀 PostgreSQL Performance Audit Report")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        self.check_postgres_config()
        self.check_cache_hit_ratio()
        self.check_pg_stat_statements()
        self.analyze_query_performance()
        self.check_index_usage()

        print("\n🎯 Next Steps & Recommendations")
        print("=" * 60)
        print("1. 🔧 Configuration Tuning:")
        print("   - Increase shared_buffers if cache hit ratio < 99%")
        print("   - Adjust work_mem based on query complexity")
        print("   - Consider enabling pg_stat_statements for query monitoring")
        print()
        print("2. 📊 Monitoring Setup:")
        print("   - Enable pg_stat_statements extension")
        print("   - Set up regular monitoring of cache hit ratios")
        print("   - Monitor slow query logs")
        print()
        print("3. 🔍 Query Optimization:")
        print("   - Review slow queries (>100ms)")
        print("   - Add indexes for frequently filtered columns")
        print("   - Consider query rewriting for complex operations")
        print()
        print("4. 📈 Index Management:")
        print("   - Remove unused indexes")
        print("   - Monitor index bloat")
        print("   - Add indexes for JOIN operations")
        print()
        print("5. 🔄 Regular Audits:")
        print("   - Repeat this audit every 2-6 months")
        print("   - Run after significant schema changes")
        print("   - Monitor after application updates")


def main():
    auditor = DatabaseAuditor()
    auditor.generate_report()


if __name__ == "__main__":
    main()
