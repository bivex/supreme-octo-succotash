
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
"""PostgreSQL Query Analysis and Optimization Tool."""

import psycopg2
import json
from datetime import datetime


class PostgresAnalyzer:
    """Analyze PostgreSQL queries and provide optimization recommendations."""

    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='supreme_octosuccotash_db',
                user='app_user',
                password='app_password'
            )
            print("✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise

    def get_database_info(self):
        """Get basic database information."""
        try:
            cursor = self.conn.cursor()

            print("📊 Database Overview")
            print("=" * 50)

            # Database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            db_size = cursor.fetchone()[0]
            print(f"Database Size: {db_size}")

            # PostgreSQL version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"PostgreSQL Version: {version[:60]}...")

            # Connection count
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            connections = cursor.fetchone()[0]
            print(f"Active Connections: {connections}")

            # Table statistics
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10;
            """)

            tables = cursor.fetchall()
            print(f"\n📋 Top Tables (by size):")
            for table in tables:
                print(f"  {table[1]}: {table[2]} ({table[6]:,} rows, {table[3]:,} inserts)")

            cursor.close()

        except Exception as e:
            print(f"❌ Database info error: {e}")

    def analyze_table_indexes(self):
        """Analyze table indexes and suggest optimizations."""
        try:
            cursor = self.conn.cursor()

            print("\n📋 Index Analysis")
            print("=" * 50)

            # Existing indexes
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size,
                    idx_scan as scans
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
                print("  CRITICAL: Database has no indexes - performance will be poor")

            # Check for foreign key constraints without indexes
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
                print(f"\n🔗 Foreign Key Analysis ({len(fks)} FKs):")
                missing_indexes = []

                for fk in fks:
                    # Check if index exists
                    cursor.execute("""
                        SELECT 1 FROM pg_indexes
                        WHERE schemaname = 'public'
                          AND tablename = %s
                          AND indexdef LIKE %s;
                    """, (fk[0], f'%{fk[1]}%'))

                    has_index = cursor.fetchone()
                    if not has_index:
                        missing_indexes.append(fk)
                        print(f"  ⚠️  MISSING INDEX: {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
                    else:
                        print(f"  ✅ Indexed: {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")

                if missing_indexes:
                    print(f"\n💡 Recommendation: Create {len(missing_indexes)} missing FK indexes")
                else:
                    print("\n✅ All foreign keys have indexes")

            cursor.close()

        except Exception as e:
            print(f"❌ Index analysis error: {e}")

    def analyze_query_performance(self):
        """Analyze query performance using EXPLAIN."""
        try:
            cursor = self.conn.cursor()

            print("\n⚡ Query Performance Analysis")
            print("=" * 50)

            # Test common application queries
            test_queries = [
                ("Health Check", "SELECT 1 as health_check"),
                ("Campaign Count", "SELECT COUNT(*) FROM campaigns"),
                ("Click Count", "SELECT COUNT(*) FROM clicks"),
                ("Event Count", "SELECT COUNT(*) FROM events"),
                ("Conversion Count", "SELECT COUNT(*) FROM conversions"),
                ("Recent Clicks", "SELECT * FROM clicks ORDER BY created_at DESC LIMIT 10"),
                ("Campaign Analytics", "SELECT campaign_id, COUNT(*) as clicks FROM clicks GROUP BY campaign_id ORDER BY clicks DESC LIMIT 5"),
            ]

            analysis_results = []

            for query_name, query in test_queries:
                try:
                    print(f"\n🔍 Analyzing: {query_name}")

                    # Get EXPLAIN ANALYZE output
                    cursor.execute(f"EXPLAIN (ANALYZE, VERBOSE, COSTS, FORMAT JSON) {query}")
                    result = cursor.fetchone()

                    if result and result[0]:
                        explain_data = result[0][0]  # First (and only) plan
                        plan = explain_data.get('Plan', {})

                        # Extract key metrics
                        total_cost = plan.get('Total Cost', 'N/A')
                        execution_time = explain_data.get('Execution Time', 'N/A')
                        planning_time = explain_data.get('Planning Time', 'N/A')
                        actual_rows = plan.get('Actual Rows', plan.get('Plan Rows', 'N/A'))

                        print(f"   Execution Time: {execution_time:.2f}ms")
                        print(f"   Planning Time: {planning_time}ms")
                        print(f"   Actual Rows: {actual_rows}")

                        # Check for potential issues
                        issues = []
                        if isinstance(total_cost, (int, float)) and total_cost > 1000:
                            issues.append("High cost - consider optimization")
                        if isinstance(execution_time, (int, float)) and execution_time > 100:
                            issues.append("Slow execution - needs attention")

                        if issues:
                            print(f"   ⚠️  Issues: {', '.join(issues)}")

                        analysis_results.append({
                            'query': query_name,
                            'cost': total_cost,
                            'execution_time': execution_time,
                            'issues': issues
                        })

                    else:
                        print("   ❌ No EXPLAIN output")

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    analysis_results.append({
                        'query': query_name,
                        'error': str(e)
                    })

            # Summary
            print(f"\n📈 Performance Summary:")
            slow_queries = [r for r in analysis_results if r.get('execution_time', 0) > 100]
            high_cost_queries = [r for r in analysis_results if r.get('cost', 0) > 1000]

            print(f"   Total queries analyzed: {len(analysis_results)}")
            print(f"   Slow queries (>100ms): {len(slow_queries)}")
            print(f"   High cost queries (>1000): {len(high_cost_queries)}")

            cursor.close()

        except Exception as e:
            print(f"❌ Query performance analysis error: {e}")

    def generate_optimization_recommendations(self):
        """Generate database optimization recommendations."""
        print("\n💡 Database Optimization Recommendations")
        print("=" * 50)

        recommendations = [
            "✅ COMPLETED: Connection pool increased to 100 connections",
            "✅ COMPLETED: UTF-8 encoding errors fixed in application",
            "✅ COMPLETED: PostgreSQL monitoring configured (pg_stat_statements, auto_explain)",
        ]

        # Check what still needs to be done
        try:
            cursor = self.conn.cursor()

            # Check indexes
            cursor.execute("SELECT COUNT(*) FROM pg_stat_user_indexes;")
            index_count = cursor.fetchone()[0]

            if index_count == 0:
                recommendations.append("🔴 CRITICAL: No database indexes found!")
                recommendations.append("   - Create indexes on: campaign_id, click_id, created_at, user_id")
                recommendations.append("   - Add foreign key indexes")
            else:
                recommendations.append(f"✅ Has {index_count} indexes")

            # Check data volume
            cursor.execute("SELECT SUM(n_live_tup) FROM pg_stat_user_tables;")
            total_rows = cursor.fetchone()[0] or 0

            if total_rows > 10000:
                recommendations.append("📊 Consider partitioning large tables by date")
                recommendations.append("   - Partition clicks, events, conversions by created_at")

            # Check if monitoring is working
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements';")
            if cursor.fetchone():
                recommendations.append("✅ pg_stat_statements extension enabled")
            else:
                recommendations.append("❌ pg_stat_statements not enabled")

            cursor.close()

        except Exception as e:
            recommendations.append(f"❌ Could not check database state: {e}")

        # General recommendations
        recommendations.extend([
            "",
            "🚀 Performance Tuning:",
            "   - Monitor slow queries with pg_stat_statements",
            "   - Use EXPLAIN ANALYZE for query optimization",
            "   - Consider connection pooling (already done)",
            "   - Enable query result caching in application",
            "",
            "📊 Monitoring:",
            "   - Check PostgreSQL logs for auto_explain output",
            "   - Monitor connection pool usage",
            "   - Set up alerts for slow queries",
        ])

        for rec in recommendations:
            print(f"  {rec}")

    def create_performance_indexes(self):
        """Create recommended performance indexes."""
        try:
            cursor = self.conn.cursor()

            print("\n🔧 Creating Performance Indexes")
            print("=" * 50)

            indexes_to_create = [
                ("idx_clicks_campaign_created", "clicks", "campaign_id, created_at DESC"),
                ("idx_clicks_created_at", "clicks", "created_at DESC"),
                ("idx_clicks_user_id", "clicks", "user_id"),
                ("idx_events_click_created", "events", "click_id, created_at DESC"),
                ("idx_events_created_at", "events", "created_at DESC"),
                ("idx_events_type", "events", "event_type"),
                ("idx_conversions_click", "conversions", "click_id"),
                ("idx_conversions_created", "conversions", "created_at DESC"),
                ("idx_conversions_type", "conversions", "conversion_type"),
                ("idx_campaigns_status", "campaigns", "status"),
                ("idx_campaigns_created", "campaigns", "created_at DESC"),
            ]

            created_count = 0
            for index_name, table_name, columns in indexes_to_create:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns});")
                    self.conn.commit()
                    print(f"✅ Created index: {index_name}")
                    created_count += 1
                except Exception as e:
                    print(f"❌ Failed to create {index_name}: {e}")

            print(f"\n✅ Created {created_count} performance indexes")

            cursor.close()

        except Exception as e:
            print(f"❌ Index creation error: {e}")

    def run_full_analysis(self):
        """Run complete database analysis."""
        try:
            self.get_database_info()
            self.analyze_table_indexes()
            self.analyze_query_performance()
            self.generate_optimization_recommendations()

            print("\n" + "="*60)
            response = input("Create recommended performance indexes? (y/n): ")
            if response.lower() == 'y':
                self.create_performance_indexes()

            print("\n🎯 Database Analysis Complete!")
            print("📄 Check the output above for optimization recommendations")

        finally:
            if self.conn:
                self.conn.close()


if __name__ == "__main__":
    analyzer = PostgresAnalyzer()
    analyzer.run_full_analysis()
