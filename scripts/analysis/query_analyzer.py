#!/usr/bin/env python3
"""Advanced PostgreSQL Query Analysis Tool."""

import psycopg2
import uuid
import time
from typing import List, Dict, Any


class QueryAnalyzer:
    """PostgreSQL query analyzer using EXPLAIN and basic profiling."""

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

    def explain_query(self, query: str, analyze: bool = True) -> Dict[str, Any]:
        """Get EXPLAIN output for a query."""
        try:
            cursor = self.conn.cursor()

            explain_cmd = "EXPLAIN (ANALYZE, VERBOSE, COSTS, BUFFERS, TIMING, FORMAT JSON)" if analyze else "EXPLAIN (FORMAT JSON)"
            full_query = f"{explain_cmd} {query}"

            start_time = time.time()
            cursor.execute(full_query)
            end_time = time.time()

            result = cursor.fetchone()
            cursor.close()

            return {
                'query': query,
                'explain': result[0] if result else None,
                'execution_time': end_time - start_time,
                'success': True
            }

        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'execution_time': 0,
                'success': False
            }

    def get_table_info(self) -> Dict[str, Any]:
        """Get information about database tables and indexes."""
        try:
            cursor = self.conn.cursor()

            # Get table sizes
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY size_bytes DESC;
            """)

            tables = cursor.fetchall()

            # Get index information
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                ORDER BY pg_relation_size(indexrelid) DESC;
            """)

            indexes = cursor.fetchall()

            cursor.close()

            return {
                'tables': tables,
                'indexes': indexes
            }

        except Exception as e:
            print(f"Error getting table info: {e}")
            return {'tables': [], 'indexes': []}

    def analyze_application_queries(self) -> List[Dict[str, Any]]:
        """Analyze common queries used by the application."""
        queries_to_analyze = [
            # Click queries
            "SELECT * FROM clicks WHERE id = %s",
            "SELECT COUNT(*) FROM clicks WHERE campaign_id = %s",
            "SELECT * FROM clicks WHERE created_at > %s ORDER BY created_at DESC LIMIT 100",

            # Event queries
            "SELECT * FROM events WHERE click_id = %s ORDER BY created_at DESC",
            "SELECT COUNT(*) FROM events WHERE campaign_id = %s",

            # Conversion queries
            "SELECT * FROM conversions WHERE click_id = %s",
            "SELECT COUNT(*) FROM conversions WHERE campaign_id = %s AND created_at > %s",

            # Campaign queries
            "SELECT * FROM campaigns WHERE id = %s",
            "SELECT * FROM campaigns WHERE status = 'active'",

            # Analytics queries (potentially slow)
            "SELECT COUNT(*) FROM clicks WHERE campaign_id = %s AND created_at BETWEEN %s AND %s",
            "SELECT campaign_id, COUNT(*) as clicks FROM clicks GROUP BY campaign_id ORDER BY clicks DESC LIMIT 10",
        ]

        results = []

        # Get sample UUIDs for parameterized queries
        try:
            cursor = self.conn.cursor()

            # Get sample IDs
            cursor.execute("SELECT id FROM campaigns LIMIT 1")
            campaign_id = cursor.fetchone()
            campaign_id = campaign_id[0] if campaign_id else str(uuid.uuid4())

            cursor.execute("SELECT id FROM clicks LIMIT 1")
            click_id = cursor.fetchone()
            click_id = click_id[0] if click_id else str(uuid.uuid4())

            cursor.close()

            # Replace parameters with actual values
            param_map = {
                '%s': [campaign_id, click_id, '2024-01-01', '2024-12-31']
            }

            for query_template in queries_to_analyze:
                # Simple parameter replacement for analysis
                query = query_template.replace('%s', f"'{campaign_id}'")

                print(f"\n🔍 Analyzing: {query[:80]}...")
                result = self.explain_query(query, analyze=False)  # Skip ANALYZE for speed
                results.append(result)

                if result['success'] and result['explain']:
                    # Parse basic cost information
                    try:
                        plan = result['explain'][0] if result['explain'] else {}
                        if 'Plan' in plan:
                            cost = plan['Plan'].get('Total Cost', 'N/A')
                            print(".2f")
                    except:
                        pass

        except Exception as e:
            print(f"Error during query analysis: {e}")

        return results

    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate a performance report."""
        report = []
        report.append("🔍 PostgreSQL Query Analysis Report")
        report.append("=" * 50)

        successful_queries = [r for r in results if r['success']]
        failed_queries = [r for r in results if not r['success']]

        report.append(f"\n📊 Summary:")
        report.append(f"   Total queries analyzed: {len(results)}")
        report.append(f"   Successful: {len(successful_queries)}")
        report.append(f"   Failed: {len(failed_queries)}")

        if failed_queries:
            report.append(f"\n❌ Failed Queries:")
            for query in failed_queries:
                report.append(f"   - {query['query'][:60]}...: {query['error']}")

        # Table information
        table_info = self.get_table_info()
        report.append(f"\n📋 Database Tables ({len(table_info['tables'])}):")
        for table in table_info['tables']:
            report.append(f"   - {table[1]}: {table[2]}")

        report.append(f"\n📋 Database Indexes ({len(table_info['indexes'])}):")
        for index in table_info['indexes'][:10]:  # Show top 10
            report.append(f"   - {index[2]} on {index[1]}: {index[3]}")

        # Recommendations
        report.append(f"\n💡 Recommendations:")
        if not table_info['indexes']:
            report.append("   - Add indexes on frequently queried columns (campaign_id, click_id, created_at)")
        report.append("   - Consider partitioning large tables by date")
        report.append("   - Monitor slow queries with pg_stat_statements (requires superuser)")
        report.append("   - Enable auto_explain for automatic query plan logging")

        return "\n".join(report)


def main():
    """Main analysis function."""
    analyzer = QueryAnalyzer()

    print("🚀 Starting PostgreSQL Query Analysis...")
    print("This may take a few minutes...\n")

    # Analyze queries
    results = analyzer.analyze_application_queries()

    # Generate report
    report = analyzer.generate_report(results)

    print("\n" + report)

    # Save detailed results
    with open('query_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
        f.write("\n\n=== Detailed Results ===\n")
        for result in results:
            f.write(f"\nQuery: {result['query']}\n")
            if result['success']:
                f.write(f"Status: SUCCESS\n")
                if result['explain']:
                    f.write(f"Explain: {result['explain']}\n")
            else:
                f.write(f"Status: FAILED - {result['error']}\n")
            f.write("-" * 50 + "\n")

    print("\n📄 Detailed report saved to: query_analysis_report.txt")

    analyzer.conn.close()


if __name__ == "__main__":
    main()
