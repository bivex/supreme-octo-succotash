
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:27
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Clean all database tables by truncating them.
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


class DatabaseCleaner:
    """Handles database table cleaning operations."""

    def __init__(self):
        self.container = Container()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for cleaning process."""
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

    def get_table_names(self, connection) -> List[str]:
        """Get all table names from the public schema."""
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = cursor.fetchall()
            return [table_name for (table_name,) in tables]
        finally:
            cursor.close()

    def truncate_table(self, connection, table_name: str) -> bool:
        """Truncate a single table."""
        cursor = connection.cursor()
        try:
            cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE')
            self.logger.info(f"Successfully truncated table: {table_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to truncate table {table_name}: {str(e)}")
            return False
        finally:
            cursor.close()

    def clean_all_tables(self) -> int:
        """Clean all tables and return count of successfully truncated tables."""
        self.logger.info("Starting database table cleaning")
        self.logger.info("=" * 40)

        try:
            with self.get_database_connection() as connection:
                table_names = self.get_table_names(connection)

                if not table_names:
                    self.logger.warning("No tables found in database")
                    return 0

                self.logger.info(f"Found {len(table_names)} tables to clean")
                truncated_count = 0

                for table_name in table_names:
                    if self.truncate_table(connection, table_name):
                        truncated_count += 1

                connection.commit()
                self.logger.info(f"Successfully cleaned {truncated_count} tables")
                return truncated_count

        except Exception as e:
            self.logger.error(f"Critical error during table cleaning: {str(e)}")
            raise


def main() -> None:
    """Main entry point for database cleaning."""
    try:
        cleaner = DatabaseCleaner()
        truncated_count = cleaner.clean_all_tables()

        if truncated_count > 0:
            print(f"Database cleaning complete. {truncated_count} tables were truncated.")
        else:
            print("No tables were found or cleaned.")
            sys.exit(1)

    except Exception as e:
        print(f"Failed to clean database: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL service is running")
        print("2. Check database connection parameters")
        print("3. Verify user permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()
