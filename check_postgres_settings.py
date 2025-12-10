#!/usr/bin/env python3
"""
Check PostgreSQL settings and database state.
"""

import sys
import os
import logging
from typing import List, Tuple, Optional
from contextlib import contextmanager

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import psycopg2
    from psycopg2 import pool
    from src.container import Container
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed")
    sys.exit(1)


class PostgreSQLChecker:
    """Handles PostgreSQL settings and database state checking."""

    def __init__(self):
        self.container = Container()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for PostgreSQL checking."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    @contextmanager
    def get_database_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = self.container.get_db_connection()
            yield connection
        finally:
            if connection:
                connection.close()

    def get_database_size(self, connection) -> str:
        """Get the size of the current database."""
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as db_size")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def get_table_record_counts(self, connection, tables: List[str]) -> List[Tuple[str, int]]:
        """Get record counts for specified tables."""
        cursor = connection.cursor()
        results = []

        try:
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    results.append((table, count))
                except Exception as e:
                    self.logger.warning(f"Error counting records in {table}: {str(e)}")
                    results.append((table, -1))  # -1 indicates error
        finally:
            cursor.close()

        return results

    def get_postgresql_settings(self, connection) -> List[Tuple[str, str, Optional[str]]]:
        """Get PostgreSQL cache-related settings."""
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT name, setting, unit
                FROM pg_settings
                WHERE name IN ('shared_buffers', 'work_mem', 'maintenance_work_mem', 'effective_cache_size', 'shared_preload_libraries')
                ORDER BY name
            """)
            return cursor.fetchall()
        finally:
            cursor.close()

    def check_extension(self, connection, extension_name: str) -> bool:
        """Check if a PostgreSQL extension is installed."""
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = %s", (extension_name,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def analyze_cache_settings(self) -> None:
        """Analyze PostgreSQL cache settings and provide recommendations."""
        self.logger.info("PostgreSQL Cache Hit Ratio Analysis")
        self.logger.info("=" * 50)

        try:
            with self.get_database_connection() as connection:
                # Database size
                db_size = self.get_database_size(connection)
                self.logger.info(f"Database size: {db_size}")

                # Table records
                tables = ['campaigns', 'clicks', 'events', 'conversions', 'landing_pages', 'offers']
                table_counts = self.get_table_record_counts(connection, tables)

                total_records = 0
                self.logger.info("Table records:")
                for table, count in table_counts:
                    if count >= 0:
                        self.logger.info(f"  {table}: {count} records")
                        total_records += count
                    else:
                        self.logger.info(f"  {table}: error retrieving count")

                self.logger.info(f"Total records: {total_records}")

                # PostgreSQL settings
                settings = self.get_postgresql_settings(connection)
                self.logger.info("PostgreSQL Cache Settings:")
                for name, setting, unit in settings:
                    unit_str = f" {unit}" if unit else ""
                    self.logger.info(f"  {name}: {setting}{unit_str}")

                # Extension checks
                buffercache_installed = self.check_extension(connection, 'pg_buffercache')
                stat_statements_installed = self.check_extension(connection, 'pg_stat_statements')

                if buffercache_installed:
                    self.logger.info("pg_buffercache extension: INSTALLED")
                else:
                    self.logger.warning("pg_buffercache extension: NOT INSTALLED")
                    self.logger.warning("This may cause inaccurate cache hit ratio measurements")

                if stat_statements_installed:
                    self.logger.info("pg_stat_statements extension: INSTALLED")
                else:
                    self.logger.warning("pg_stat_statements extension: NOT INSTALLED")
                    self.logger.warning("This may cause missing query performance data")

                # Diagnosis
                self._provide_diagnosis(db_size, total_records, settings)

        except Exception as e:
            self.logger.error(f"Error during PostgreSQL analysis: {str(e)}")
            raise

    def _provide_diagnosis(self, db_size: str, total_records: int, settings: List[Tuple[str, str, Optional[str]]]) -> None:
        """Provide diagnosis and recommendations based on analysis."""
        self.logger.info("DIAGNOSIS:")

        issues_found = False

        if total_records == 0:
            self.logger.error("PROBLEM: Database is empty (0 records)")
            self.logger.info("  Solution: Load test data for cache testing")
            issues_found = True

        if db_size.endswith('kB') and int(db_size[:-2]) < 10000:
            self.logger.error("PROBLEM: Database is too small for effective caching")
            self.logger.info(f"  Current size: {db_size}")
            self.logger.info("  Solution: Increase data volume")
            issues_found = True

        # Check shared_buffers
        shared_buffers_setting = next((setting for name, setting, unit in settings if name == 'shared_buffers'), None)
        if shared_buffers_setting:
            shared_buffers_kb = int(shared_buffers_setting)
            if shared_buffers_kb < 128 * 1024:  # less than 128MB
                self.logger.error("PROBLEM: shared_buffers is too small")
                self.logger.info(f"  Current: {shared_buffers_kb // 1024} MB")
                self.logger.info("  Recommendation: 25-40% of system memory")
                issues_found = True

        self.logger.info("RECOMMENDATIONS:")
        if issues_found:
            self.logger.info("1. Load test data: python load_test_db.py --small")
            self.logger.info("2. Increase shared_buffers in postgresql.conf")
            self.logger.info("3. Install pg_buffercache for accurate measurements")
            self.logger.info("4. Conduct load testing")
        else:
            self.logger.info("Database configuration appears optimal for caching")


def main() -> None:
    """Main entry point for PostgreSQL checking."""
    try:
        checker = PostgreSQLChecker()
        checker.analyze_cache_settings()
    except Exception as e:
        print(f"Failed to check PostgreSQL settings: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
