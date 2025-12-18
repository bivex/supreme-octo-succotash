# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""PostgreSQL query analyzer with automatic EXPLAIN ANALYZE and optimization recommendations."""

import psycopg2
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysisResult:
    """Result of query analysis."""
    query: str
    execution_time: float
    planning_time: float
    total_cost: float
    has_sequential_scan: bool
    table_size_mb: float
    recommended_indexes: List[str]
    optimization_suggestions: List[str]
    severity: str  # 'low', 'medium', 'high', 'critical'


class PostgresQueryAnalyzer:
    """Automatic analyzer for PostgreSQL queries using EXPLAIN ANALYZE."""

    def __init__(self, connection):
        self.connection = connection

    def analyze_query(self, query: str, params: tuple = None) -> QueryAnalysisResult:
        """Analyze a query using EXPLAIN ANALYZE."""
        try:
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"

            # Get connection from pool if it's a pool, otherwise use directly
            if hasattr(self.connection, 'getconn'):
                # It's a connection pool
                conn = self.connection.getconn()
                try:
                    cursor = conn.cursor()
                    start_time = datetime.now()
                    cursor.execute(explain_query, params or ())
                    explain_result = cursor.fetchone()[0]
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    cursor.close()
                finally:
                    self.connection.putconn(conn)
            else:
                # It's a direct connection
                with self.connection.cursor() as cursor:
                    start_time = datetime.now()
                    cursor.execute(explain_query, params or ())
                    explain_result = cursor.fetchone()[0]
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return self._parse_explain_result(query, explain_result, execution_time)

        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return QueryAnalysisResult(
                query=query,
                execution_time=0,
                planning_time=0,
                total_cost=0,
                has_sequential_scan=False,
                table_size_mb=0,
                recommended_indexes=[],
                optimization_suggestions=[f"Analysis failed: {str(e)}"],
                severity="unknown"
            )

    def _parse_explain_result(self, query: str, explain_json: List[Dict], execution_time: float) -> QueryAnalysisResult:
        """Parse EXPLAIN ANALYZE JSON result."""
        if not explain_json or len(explain_json) == 0:
            return QueryAnalysisResult(
                query=query,
                execution_time=execution_time,
                planning_time=0,
                total_cost=0,
                has_sequential_scan=False,
                table_size_mb=0,
                recommended_indexes=[],
                optimization_suggestions=["No explain result"],
                severity="unknown"
            )

        plan = explain_json[0]['Plan']
        planning_time = explain_json[0].get('Planning Time', 0)
        execution_time = explain_json[0].get('Execution Time', execution_time)

        # Analyze the plan
        has_sequential_scan = self._check_sequential_scan(plan)
        total_cost = plan.get('Total Cost', 0)
        recommended_indexes = self._analyze_missing_indexes(plan, query)
        table_size_mb = self._estimate_table_size(plan)

        # Generate optimization suggestions
        suggestions = []
        severity = self._calculate_severity(has_sequential_scan, total_cost, table_size_mb, execution_time)

        if has_sequential_scan and table_size_mb > 10:  # > 10MB tables
            suggestions.append(f"⚠️ Sequential scan on large table ({table_size_mb:.1f}MB). Consider adding indexes.")

        if total_cost > 10000:
            suggestions.append(f"🚨 High query cost ({total_cost:.0f}). Query needs optimization.")

        if execution_time > 1000:  # > 1 second
            suggestions.append(f"🐌 Slow execution ({execution_time:.2f}ms). Consider query optimization.")

        return QueryAnalysisResult(
            query=query,
            execution_time=execution_time,
            planning_time=planning_time,
            total_cost=total_cost,
            has_sequential_scan=has_sequential_scan,
            table_size_mb=table_size_mb,
            recommended_indexes=recommended_indexes,
            optimization_suggestions=suggestions,
            severity=severity
        )

    def _check_sequential_scan(self, plan: Dict) -> bool:
        """Check if plan contains sequential scan on large tables."""
        if plan.get('Node Type') == 'Seq Scan':
            return True

        # Check child plans recursively
        for child in plan.get('Plans', []):
            if self._check_sequential_scan(child):
                return True

        return False

    def _analyze_missing_indexes(self, plan: Dict, query: str) -> List[str]:
        """Analyze plan for missing indexes."""
        recommendations = []

        # Extract table and filter conditions from query
        tables, conditions = self._extract_query_info(query)

        # Check for missing indexes on WHERE conditions
        for table, condition_cols in conditions.items():
            for col in condition_cols:
                recommendations.append(f"CREATE INDEX ON {table} ({col})")

        # Check for missing indexes on JOIN conditions
        join_conditions = self._extract_join_conditions(plan)
        for table, cols in join_conditions.items():
            for col in cols:
                recommendations.append(f"CREATE INDEX ON {table} ({col})")

        return recommendations

    def _extract_query_info(self, query: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """Extract table names and WHERE conditions from query."""
        tables = {}
        conditions = {}

        # Simple regex-based extraction (could be enhanced with proper SQL parsing)
        query_lower = query.lower()

        # Find table names
        from_match = re.search(r'from\s+(\w+)', query_lower)
        if from_match:
            table_name = from_match.group(1)
            tables[table_name] = []

        # Find WHERE conditions
        where_match = re.search(r'where\s+(.+?)(?:group|order|limit|$)', query_lower)
        if where_match:
            where_clause = where_match.group(1)
            # Extract column names (simplified)
            col_matches = re.findall(r'(\w+)\s*[=<>!]+\s*[%\'\w]+', where_clause)
            if from_match:
                conditions[from_match.group(1)] = list(set(col_matches))

        return tables, conditions

    def _extract_join_conditions(self, plan: Dict) -> Dict[str, List[str]]:
        """Extract JOIN conditions from execution plan."""
        join_cols = {}

        # Look for Nested Loop joins which might indicate missing indexes
        if plan.get('Node Type') == 'Nested Loop':
            # Check if this is an expensive nested loop
            if plan.get('Total Cost', 0) > 1000:
                # Extract table info from child nodes
                for child in plan.get('Plans', []):
                    if child.get('Node Type') in ['Index Scan', 'Seq Scan']:
                        relation = child.get('Relation Name')
                        if relation:
                            join_cols[relation] = ['id']  # Assume id column for joins

        # Recursively check child plans
        for child in plan.get('Plans', []):
            child_joins = self._extract_join_conditions(child)
            for table, cols in child_joins.items():
                if table not in join_cols:
                    join_cols[table] = []
                join_cols[table].extend(cols)

        return join_cols

    def _estimate_table_size(self, plan: Dict) -> float:
        """Estimate table size from plan statistics."""
        # This is a simplified estimation
        # In production, you'd query pg_stat_user_tables
        if 'Plan Rows' in plan and 'width' in plan:
            estimated_rows = plan['Plan Rows']
            width = plan.get('width', 100)
            # Rough estimation: rows * width / 1MB
            return (estimated_rows * width) / (1024 * 1024)
        return 0

    def _calculate_severity(self, has_seq_scan: bool, cost: float, size_mb: float, exec_time: float) -> str:
        """Calculate optimization severity."""
        score = 0

        if has_seq_scan and size_mb > 50:
            score += 3
        elif has_seq_scan:
            score += 1

        if cost > 50000:
            score += 3
        elif cost > 10000:
            score += 2
        elif cost > 1000:
            score += 1

        if exec_time > 5000:  # 5 seconds
            score += 3
        elif exec_time > 1000:  # 1 second
            score += 2
        elif exec_time > 100:   # 100ms
            score += 1

        if score >= 5:
            return "critical"
        elif score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        else:
            return "low"

    def get_slow_queries_report(self, min_calls: int = 10, min_avg_time: float = 100) -> List[Dict]:
        """Get report of slow queries from pg_stat_statements."""
        try:
            # Get connection from pool if it's a pool, otherwise use directly
            if hasattr(self.connection, 'getconn'):
                # It's a connection pool
                conn = self.connection.getconn()
                try:
                    cursor = conn.cursor()
                    # Check available columns in pg_stat_statements and adapt query
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'pg_stat_statements' AND table_schema = 'public'
                    """)
                    available_columns = {row[0] for row in cursor.fetchall()}

                    # Build query based on available columns
                    select_columns = ['query', 'calls']
                    where_conditions = ['calls >= %s']
                    order_by = 'calls DESC'  # fallback

                    if 'total_exec_time' in available_columns:
                        select_columns.extend(['total_exec_time', 'mean_exec_time'])
                        where_conditions.append('mean_exec_time >= %s')
                        order_by = 'mean_exec_time DESC'
                    elif 'total_time' in available_columns and 'mean_time' in available_columns:
                        select_columns.extend(['total_time', 'mean_time'])
                        where_conditions.append('mean_time >= %s')
                        order_by = 'mean_time DESC'
                    elif 'mean_time' in available_columns:
                        select_columns.append('mean_time')
                        where_conditions.append('mean_time >= %s')
                        order_by = 'mean_time DESC'

                    if 'rows' in available_columns:
                        select_columns.append('rows')

                    query = f"""
                        SELECT {', '.join(select_columns)}
                        FROM pg_stat_statements
                        WHERE {' AND '.join(where_conditions)}
                        ORDER BY {order_by}
                        LIMIT 20
                    """

                    cursor.execute(query, (min_calls, min_avg_time))

                    slow_queries = []
                    for row in cursor.fetchall():
                        query_data = {
                            'query': row[0],
                            'calls': row[1]
                        }

                        # Add available columns dynamically
                        col_idx = 2
                        if 'total_exec_time' in available_columns or 'total_time' in available_columns:
                            query_data['total_time'] = row[col_idx] if col_idx < len(row) else 0
                            col_idx += 1
                        if 'mean_exec_time' in available_columns or 'mean_time' in available_columns:
                            query_data['mean_time'] = row[col_idx] if col_idx < len(row) else 0
                            col_idx += 1
                        if 'rows' in available_columns:
                            query_data['rows'] = row[col_idx] if col_idx < len(row) else 0

                        slow_queries.append(query_data)

                    cursor.close()
                    return slow_queries
                finally:
                    self.connection.putconn(conn)
            else:
                # It's a direct connection
                with self.connection.cursor() as cursor:
                    # Check available columns in pg_stat_statements and adapt query
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'pg_stat_statements' AND table_schema = 'public'
                    """)
                    available_columns = {row[0] for row in cursor.fetchall()}

                    # Build query based on available columns
                    select_columns = ['query', 'calls']
                    where_conditions = ['calls >= %s']
                    order_by = 'calls DESC'  # fallback

                    if 'total_exec_time' in available_columns:
                        select_columns.extend(['total_exec_time', 'mean_exec_time'])
                        where_conditions.append('mean_exec_time >= %s')
                        order_by = 'mean_exec_time DESC'
                    elif 'total_time' in available_columns and 'mean_time' in available_columns:
                        select_columns.extend(['total_time', 'mean_time'])
                        where_conditions.append('mean_time >= %s')
                        order_by = 'mean_time DESC'
                    elif 'mean_time' in available_columns:
                        select_columns.append('mean_time')
                        where_conditions.append('mean_time >= %s')
                        order_by = 'mean_time DESC'

                    if 'rows' in available_columns:
                        select_columns.append('rows')

                    query = f"""
                        SELECT {', '.join(select_columns)}
                        FROM pg_stat_statements
                        WHERE {' AND '.join(where_conditions)}
                        ORDER BY {order_by}
                        LIMIT 20
                    """

                    cursor.execute(query, (min_calls, min_avg_time))

                    slow_queries = []
                    for row in cursor.fetchall():
                        query_data = {
                            'query': row[0],
                            'calls': row[1]
                        }

                        # Add available columns dynamically
                        col_idx = 2
                        if 'total_exec_time' in available_columns or 'total_time' in available_columns:
                            query_data['total_time'] = row[col_idx] if col_idx < len(row) else 0
                            col_idx += 1
                        if 'mean_exec_time' in available_columns or 'mean_time' in available_columns:
                            query_data['mean_time'] = row[col_idx] if col_idx < len(row) else 0
                            col_idx += 1
                        if 'rows' in available_columns:
                            query_data['rows'] = row[col_idx] if col_idx < len(row) else 0

                        slow_queries.append(query_data)

                    return slow_queries

        except Exception as e:
            logger.error(f"Failed to get slow queries report: {e}")
            return []


class QueryOptimizationMonitor:
    """Monitor for automatic query optimization."""

    def __init__(self, connection):
        self.connection = connection
        self.analyzer = PostgresQueryAnalyzer(connection)

    def monitor_and_optimize(self) -> List[Dict]:
        """Monitor queries and provide optimization recommendations."""
        # Get slow queries
        slow_queries = self.analyzer.get_slow_queries_report()

        optimizations = []
        for query_info in slow_queries:
            # Analyze each slow query
            analysis = self.analyzer.analyze_query(query_info['query'])

            if analysis.severity in ['high', 'critical']:
                optimizations.append({
                    'query': query_info['query'][:200] + '...' if len(query_info['query']) > 200 else query_info['query'],
                    'calls': query_info['calls'],
                    'mean_time': query_info['mean_time'],
                    'severity': analysis.severity,
                    'recommendations': analysis.optimization_suggestions,
                    'suggested_indexes': analysis.recommended_indexes
                })

        return optimizations
