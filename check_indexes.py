
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:28
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Check indexes in the system.
"""

import sys
import os
import logging
from typing import List, Tuple, Optional
from contextlib import contextmanager

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.container import Container
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed")
    sys.exit(1)


class IndexChecker:
    """Handles database index checking and analysis."""

    def __init__(self):
        self.container = Container()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for index checking."""
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

    def get_index_statistics(self, connection) -> List[Tuple[str, str, int, int, int, str]]:
        """Get statistics for all indexes in the public schema."""
        cursor = connection.cursor()
        try:
            cursor.execute('''
                SELECT
                    schemaname,
                    indexrelname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY indexrelname
            ''')
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_specific_index_info(self, connection, index_name: str) -> Optional[Tuple[str, str, int, str, str]]:
        """Get detailed information about a specific index."""
        cursor = connection.cursor()
        try:
            cursor.execute('''
                SELECT
                    ui.schemaname,
                    ui.indexrelname,
                    ui.idx_scan,
                    pg_size_pretty(pg_relation_size(ui.indexrelid)) as size,
                    CASE WHEN i.indisprimary THEN 'PRIMARY KEY'
                         WHEN i.indisunique THEN 'UNIQUE'
                         ELSE 'REGULAR' END as index_type
                FROM pg_stat_user_indexes ui
                JOIN pg_index i ON ui.indexrelid = i.indexrelid
                WHERE ui.indexrelname = %s
            ''', (index_name,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def analyze_indexes(self) -> None:
        """Analyze database indexes and provide recommendations."""
        self.logger.info("INDEX SYSTEM ANALYSIS")
        self.logger.info("=" * 50)

        try:
            with self.get_database_connection() as connection:
                # Get index statistics
                stats = self.get_index_statistics(connection)
                self.logger.info("INDEX USAGE STATISTICS:")

                unused_indexes = []

                for schema, index, scans, tup_read, tup_fetch, size in stats:
                    status = 'USED' if scans > 0 else 'UNUSED'
                    self.logger.info(f"  • {schema}.{index}: {status}")
                    self.logger.info(f"    Scans: {scans}, tuples read: {tup_read}, size: {size}")

                    if scans == 0:
                        unused_indexes.append(index)

                self.logger.info(f"UNUSED INDEXES: {len(unused_indexes)} total")
                for idx in unused_indexes:
                    self.logger.info(f"   - {idx}")

                # Check specific test index
                self.logger.info("TEST INDEX ANALYSIS:")
                test_index = self.get_specific_index_info(connection, 'idx_test_unused')

                if test_index:
                    schema, name, scans, size, idx_type = test_index
                    self.logger.info(f"   Name: {schema}.{name}")
                    self.logger.info(f"   Type: {idx_type}")
                    self.logger.info(f"   Scans: {scans}")
                    self.logger.info(f"   Size: {size}")
                    if scans == 0:
                        self.logger.info("   Status: READY FOR REMOVAL")
                    else:
                        self.logger.info("   Status: IN USE")
                else:
                    self.logger.info("   Test index not found")

                # Summary and recommendations
                self._provide_index_analysis_summary(stats, unused_indexes)

        except Exception as e:
            self.logger.error(f"Error during index analysis: {str(e)}")
            raise

    def _provide_index_analysis_summary(self, stats: List[Tuple], unused_indexes: List[str]) -> None:
        """Provide summary and recommendations for index analysis."""
        self.logger.info("=" * 50)
        self.logger.info("ANALYSIS SUMMARY:")
        self.logger.info(f"   • Total indexes: {len(stats)}")
        self.logger.info(f"   • Unused indexes: {len(unused_indexes)}")
        self.logger.info("   • Auto-deletion: DISABLED (dry_run_mode: true)")

        if unused_indexes:
            self.logger.info("RECOMMENDATIONS:")
            self.logger.info("   • Enable auto_delete_unused_indexes: true for automatic removal")
            self.logger.info("   • Start with dry_run_mode: true for testing")
            self.logger.info("   • Check index age (>30 days before removal)")
        else:
            self.logger.info("All indexes are currently in use - no action needed")


def main() -> None:
    """Main entry point for index checking."""
    try:
        checker = IndexChecker()
        checker.analyze_indexes()
    except Exception as e:
        print(f"Failed to check indexes: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
