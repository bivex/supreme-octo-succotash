# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""PostgreSQL prepared statements manager for automatic query optimization."""

import hashlib
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class PreparedStatementsManager:
    """Manager for PostgreSQL prepared statements with automatic caching and optimization."""

    def __init__(self, connection):
        self.connection = connection
        self._prepared_statements: Dict[str, str] = {}
        self._statement_counter = 0

    def _generate_statement_name(self, query: str) -> str:
        """Generate unique name for prepared statement based on query hash."""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
        return f"stmt_{query_hash}"

    def prepare_statement(self, query: str) -> str:
        """Prepare a statement if not already prepared."""
        if query not in self._prepared_statements:
            statement_name = self._generate_statement_name(query)
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"PREPARE {statement_name} AS {query}")
                self._prepared_statements[query] = statement_name
                logger.debug(f"Prepared statement: {statement_name} for query: {query[:100]}...")
            except Exception as e:
                logger.error(f"Failed to prepare statement: {e}")
                # Fallback to direct execution
                return None
        return self._prepared_statements[query]

    def execute_prepared(self, query: str, params: tuple = None) -> Any:
        """Execute prepared statement or fallback to direct execution."""
        statement_name = self.prepare_statement(query)
        if statement_name:
            try:
                with self.connection.cursor() as cursor:
                    if params:
                        cursor.execute(f"EXECUTE {statement_name} {params}")
                    else:
                        cursor.execute(f"EXECUTE {statement_name}")
                    return cursor
            except Exception as e:
                logger.warning(f"Prepared statement execution failed, falling back: {e}")
                # Fallback to direct execution
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor
        else:
            # Direct execution
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor

    def deallocate_unused(self):
        """Deallocate prepared statements that haven't been used recently."""
        # This could be enhanced with usage tracking
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DEALLOCATE ALL")
            self._prepared_statements.clear()
            logger.info("Deallocated all prepared statements")
        except Exception as e:
            logger.error(f"Failed to deallocate prepared statements: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about prepared statements."""
        return {
            "prepared_statements_count": len(self._prepared_statements),
            "prepared_queries": list(self._prepared_statements.keys())
        }


class AutoPreparedRepositoryMixin:
    """Mixin to add automatic prepared statement support to repositories."""

    def __init__(self, container):
        super().__init__(container)
        self._prepared_manager: Optional[PreparedStatementsManager] = None

    def _get_prepared_manager(self) -> PreparedStatementsManager:
        """Get or create prepared statements manager."""
        if self._prepared_manager is None:
            conn = self._get_connection()
            self._prepared_manager = PreparedStatementsManager(conn)
        return self._prepared_manager

    def execute_optimized(self, query: str, params: tuple = None) -> Any:
        """Execute query with automatic prepared statement optimization."""
        manager = self._get_prepared_manager()
        return manager.execute_prepared(query, params)

    def cleanup_prepared_statements(self):
        """Clean up prepared statements (call on repository destruction)."""
        if self._prepared_manager:
            self._prepared_manager.deallocate_unused()


class QueryAnalyzer:
    """Analyzer for detecting queries that should use prepared statements."""

    @staticmethod
    def should_use_prepared_statement(query: str, execution_count: int = 1) -> bool:
        """Determine if query should use prepared statement."""
        # Simple heuristics for prepared statement candidates
        query_lower = query.lower().strip()

        # Skip DDL statements
        if any(query_lower.startswith(stmt) for stmt in ['create', 'alter', 'drop', 'truncate']):
            return False

        # Good candidates for prepared statements
        if execution_count > 1:
            return True

        # Queries with parameters (indicated by %s placeholders)
        if '%s' in query or '%(' in query:
            return True

        # SELECT queries with WHERE clauses (likely to be reused)
        if query_lower.startswith('select') and 'where' in query_lower:
            return True

        # INSERT/UPDATE with parameters
        if (query_lower.startswith(('insert', 'update', 'delete')) and
                ('%s' in query or '%(' in query)):
            return True

        return False

    @staticmethod
    def analyze_repository_queries(repo_class) -> List[str]:
        """Analyze repository class for optimizable queries."""
        optimizable_queries = []

        # Get all methods that contain SQL execution
        import inspect
        for method_name, method in inspect.getmembers(repo_class, predicate=inspect.isfunction):
            if method_name.startswith('_'):
                continue

            # Get method source
            try:
                source = inspect.getsource(method)
                # Look for cursor.execute calls with SQL
                lines = source.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'cursor.execute(' in line and (
                            'SELECT' in line.upper() or 'INSERT' in line.upper() or 'UPDATE' in line.upper() or 'DELETE' in line.upper()):
                        # Extract query (simplified)
                        if '"""' in line or "'''" in line:
                            # Multi-line query, skip for now
                            continue
                        # Simple single-line extraction
                        start = line.find('"') if '"' in line else line.find("'")
                        if start != -1:
                            optimizable_queries.append(line[start:].strip('"\'"'))
            except:
                continue

        return list(set(optimizable_queries))  # Remove duplicates
