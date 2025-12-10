"""PostgreSQL query optimizer using pg_stat_statements for automatic optimization recommendations."""

import psycopg2
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceIssue:
    """Performance issue found in a query."""
    query_id: str
    query_text: str
    issue_type: str  # 'slow_query', 'missing_index', 'sequential_scan', 'inefficient_join'
    severity: str  # 'low', 'medium', 'high', 'critical'
    metrics: Dict[str, Any]
    recommendations: List[str]
    estimated_impact: str
    fix_complexity: str  # 'easy', 'medium', 'hard'


@dataclass
class OptimizationAction:
    """Action to optimize a query."""
    action_type: str  # 'create_index', 'drop_index', 'rewrite_query', 'partition_table'
    description: str
    sql_commands: List[str]
    rollback_commands: List[str]
    estimated_benefit: str
    risk_level: str  # 'low', 'medium', 'high'


class PostgresQueryOptimizer:
    """Automatic query optimizer using pg_stat_statements."""

    def __init__(self, connection):
        self.connection = connection

    def _get_cursor(self):
        """Get cursor, handling both connection pools and direct connections."""
        if hasattr(self.connection, 'getconn'):
            # It's a connection pool
            conn = self.connection.getconn()
            cursor = conn.cursor()
            # Return both connection and cursor for proper cleanup
            return conn, cursor
        else:
            # It's a direct connection
            return None, self.connection.cursor()

    def _close_cursor(self, conn, cursor):
        """Close cursor and return connection to pool if needed."""
        cursor.close()
        if conn is not None:
            # Return connection to pool
            self.connection.putconn(conn)

    def analyze_slow_queries(self, min_avg_time: float = 100,
                           min_calls: int = 10) -> List[QueryPerformanceIssue]:
        """Analyze slow queries and identify performance issues."""
        import time
        logger.info("🐌 START: analyze_slow_queries()")

        try:
            logger.info("🐌 Getting database cursor")
            cursor_start = time.time()
            conn, cursor = self._get_cursor()
            cursor_time = time.time() - cursor_start
            logger.info(".3f")       
            try:
                # Get slow queries from pg_stat_statements
                logger.info("🐌 Executing slow queries analysis query")
                query_start = time.time()
                cursor.execute("""
                    SELECT
                        queryid,
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        shared_blks_hit,
                        shared_blks_read,
                        temp_blks_read,
                        temp_blks_written
                    FROM pg_stat_statements
                    WHERE mean_time >= %s
                    AND calls >= %s
                    AND query NOT LIKE '%%pg_stat%%'
                    ORDER BY mean_time DESC
                    LIMIT 50
                """, (min_avg_time, min_calls))
                query_time = time.time() - query_start
                logger.info(".3f")
                logger.info("🐌 Fetching query results")
                fetch_start = time.time()
                rows = cursor.fetchall()
                fetch_time = time.time() - fetch_start
                logger.info(".3f")
                logger.info(f"🐌 Found {len(rows)} slow queries")

                issues = []
                for row in rows:
                    issue = self._analyze_single_query(row)
                    if issue:
                        issues.append(issue)

                return issues
            finally:
                self._close_cursor(conn, cursor)

        except Exception as e:
            logger.error(f"Failed to analyze slow queries: {e}")
            return []

    def _analyze_single_query(self, query_data: tuple) -> Optional[QueryPerformanceIssue]:
        """Analyze a single query for performance issues."""
        queryid, query, calls, total_time, mean_time, rows, shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written = query_data

        # Clean up query text (remove extra whitespace)
        query = ' '.join(query.split())

        metrics = {
            'calls': calls,
            'total_time': total_time,
            'mean_time': mean_time,
            'rows': rows,
            'cache_hit_ratio': (shared_blks_hit / (shared_blks_hit + shared_blks_read)) * 100 if (shared_blks_hit + shared_blks_read) > 0 else 100,
            'temp_blocks_read': temp_blks_read,
            'temp_blocks_written': temp_blks_written
        }

        # Analyze different types of issues
        issues = []

        # 1. Sequential scan detection
        if self._detects_sequential_scan(query):
            issues.append(self._create_sequential_scan_issue(query, queryid, metrics))

        # 2. Missing index detection
        missing_index_issue = self._detect_missing_indexes(query, metrics)
        if missing_index_issue:
            issues.append(missing_index_issue)

        # 3. Inefficient query patterns
        inefficient_issue = self._detect_inefficient_patterns(query, metrics)
        if inefficient_issue:
            issues.append(inefficient_issue)

        # 4. High temporary file usage
        if temp_blks_read > 1000 or temp_blks_written > 1000:
            issues.append(self._create_temp_file_issue(query, queryid, metrics))

        # Return the most severe issue
        if issues:
            return max(issues, key=lambda x: self._get_severity_score(x.severity))

        return None

    def _detects_sequential_scan(self, query: str) -> bool:
        """Check if query is likely to cause sequential scans."""
        query_lower = query.lower()

        # Look for patterns that often cause sequential scans
        problematic_patterns = [
            r'select\s+.*\s+from\s+\w+\s+where\s+\w+\s+like\s+',  # LIKE without index
            r'select\s+.*\s+from\s+\w+\s+where\s+.*\s+or\s+',     # OR conditions
            r'select\s+.*\s+from\s+\w+\s+where\s+.*\s+not\s+',    # NOT conditions
            r'select\s+.*\s+from\s+\w+\s+where\s+.*\s+in\s+\(',   # Large IN clauses
        ]

        for pattern in problematic_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True

        return False

    def _detect_missing_indexes(self, query: str, metrics: Dict) -> Optional[QueryPerformanceIssue]:
        """Detect missing indexes based on query analysis."""
        query_lower = query.lower()

        # Extract table and column information
        table_columns = self._extract_query_columns(query)

        if not table_columns:
            return None

        missing_indexes = []
        recommendations = []

        for table, columns in table_columns.items():
            # Check WHERE conditions
            where_cols = columns.get('where', [])
            for col in where_cols:
                if not self._index_exists(table, [col]):
                    missing_indexes.append(f"{table}.{col}")
                    recommendations.append(f"CREATE INDEX ON {table} ({col})")

            # Check JOIN conditions
            join_cols = columns.get('join', [])
            for col in join_cols:
                if not self._index_exists(table, [col]):
                    missing_indexes.append(f"{table}.{col} (JOIN)")
                    recommendations.append(f"CREATE INDEX ON {table} ({col})")

            # Check ORDER BY conditions
            order_cols = columns.get('order_by', [])
            if len(order_cols) > 1 and not self._index_exists(table, order_cols):
                compound_index = f"CREATE INDEX ON {table} ({', '.join(order_cols)})"
                recommendations.append(compound_index)

        if missing_indexes:
            return QueryPerformanceIssue(
                query_id=f"missing_index_{hash(query) % 10000}",
                query_text=query[:200] + '...' if len(query) > 200 else query,
                issue_type='missing_index',
                severity='high' if metrics['mean_time'] > 1000 else 'medium',
                metrics=metrics,
                recommendations=recommendations,
                estimated_impact=f"Potentially {int(metrics['mean_time'] * 0.7)}ms faster",
                fix_complexity='easy'
            )

        return None

    def _detect_inefficient_patterns(self, query: str, metrics: Dict) -> Optional[QueryPerformanceIssue]:
        """Detect inefficient query patterns."""
        issues = []

        # Check for SELECT *
        if re.search(r'select\s+\*', query, re.IGNORECASE):
            issues.append("SELECT * detected - specify only needed columns")

        # Check for unnecessary DISTINCT
        if 'distinct' in query.lower() and 'group by' not in query.lower():
            issues.append("Consider if DISTINCT is necessary - it can be expensive")

        # Check for large LIMIT without ORDER BY
        if re.search(r'limit\s+\d+', query, re.IGNORECASE) and 'order by' not in query.lower():
            issues.append("Large LIMIT without ORDER BY can return unpredictable results")

        # Check for multiple table scans
        table_count = len(re.findall(r'\bfrom\b|\bjoin\b', query, re.IGNORECASE))
        if table_count > 5 and metrics['mean_time'] > 500:
            issues.append("Complex query with many joins - consider denormalization or query splitting")

        if issues:
            return QueryPerformanceIssue(
                query_id=f"inefficient_{hash(query) % 10000}",
                query_text=query[:200] + '...' if len(query) > 200 else query,
                issue_type='inefficient_pattern',
                severity='medium',
                metrics=metrics,
                recommendations=issues,
                estimated_impact="10-50% performance improvement",
                fix_complexity='easy'
            )

        return None

    def _create_sequential_scan_issue(self, query: str, queryid: str, metrics: Dict) -> QueryPerformanceIssue:
        """Create issue for sequential scan."""
        return QueryPerformanceIssue(
            query_id=f"seq_scan_{queryid}",
            query_text=query[:200] + '...' if len(query) > 200 else query,
            issue_type='sequential_scan',
            severity='critical' if metrics['mean_time'] > 5000 else 'high',
            metrics=metrics,
            recommendations=[
                "Add appropriate indexes for WHERE conditions",
                "Consider query rewriting to use indexed columns",
                "Review table partitioning for large datasets"
            ],
            estimated_impact="5-20x performance improvement",
            fix_complexity='medium'
        )

    def _create_temp_file_issue(self, query: str, queryid: str, metrics: Dict) -> QueryPerformanceIssue:
        """Create issue for high temporary file usage."""
        return QueryPerformanceIssue(
            query_id=f"temp_files_{queryid}",
            query_text=query[:200] + '...' if len(query) > 200 else query,
            issue_type='high_temp_usage',
            severity='high',
            metrics=metrics,
            recommendations=[
                "Add indexes for ORDER BY operations",
                "Increase work_mem setting",
                "Consider query optimization or rewriting",
                "Review if all sorting is necessary"
            ],
            estimated_impact="Reduced I/O and memory usage",
            fix_complexity='medium'
        )

    def _extract_query_columns(self, query: str) -> Dict[str, Dict[str, List[str]]]:
        """Extract table and column information from query."""
        # This is a simplified implementation
        # A full SQL parser would be better but more complex

        result = {}
        query_lower = query.lower()

        # Find table names (simplified)
        from_match = re.search(r'from\s+(\w+)', query_lower)
        if from_match:
            table = from_match.group(1)
            result[table] = {'where': [], 'join': [], 'order_by': []}

            # Extract WHERE columns
            where_match = re.search(r'where\s+(.+?)(?:group|order|limit|$)', query_lower)
            if where_match:
                where_clause = where_match.group(1)
                cols = re.findall(r'(\w+)\s*[=<>!]+\s*[%\'\w]+', where_clause)
                result[table]['where'] = list(set(cols))

            # Extract ORDER BY columns
            order_match = re.search(r'order\s+by\s+(.+?)(?:limit|$)', query_lower)
            if order_match:
                order_clause = order_match.group(1)
                cols = re.findall(r'(\w+)', order_clause)
                result[table]['order_by'] = [col.strip() for col in cols if col.strip() not in ['asc', 'desc']]

        return result

    def _index_exists(self, table: str, columns: List[str]) -> bool:
        """Check if index exists for given table and columns."""
        try:
            conn, cursor = self._get_cursor()
            try:
                cursor.execute("""
                    SELECT indexdef
                    FROM pg_indexes
                    WHERE tablename = %s
                    AND schemaname = 'public'
                """, (table,))

                for row in cursor.fetchall():
                    index_def = row[0].lower()
                    # Check if all columns are in the index definition
                    if all(col.lower() in index_def for col in columns):
                        return True

                return False
            finally:
                self._close_cursor(conn, cursor)

        except Exception as e:
            logger.error(f"Failed to check index existence: {e}")
            return False

    def _get_severity_score(self, severity: str) -> int:
        """Get numeric score for severity."""
        scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        return scores.get(severity, 0)

    def generate_optimization_plan(self, issues: List[QueryPerformanceIssue]) -> List[OptimizationAction]:
        """Generate optimization actions based on identified issues."""
        actions = []

        for issue in issues:
            if issue.issue_type == 'missing_index' and issue.severity in ['high', 'critical']:
                for rec in issue.recommendations:
                    if rec.startswith('CREATE INDEX'):
                        actions.append(OptimizationAction(
                            action_type='create_index',
                            description=f"Create missing index for slow query",
                            sql_commands=[rec],
                            rollback_commands=[f"DROP INDEX IF EXISTS {rec.split('(')[1].split(')')[0].replace(',', '_').strip()}_idx"],
                            estimated_benefit=issue.estimated_impact,
                            risk_level='low'
                        ))

            elif issue.issue_type == 'sequential_scan':
                # Suggest query rewriting or table partitioning
                actions.append(OptimizationAction(
                    action_type='rewrite_query',
                    description=f"Optimize query to avoid sequential scan",
                    sql_commands=[],  # Would need specific query rewrite
                    rollback_commands=[],
                    estimated_benefit=issue.estimated_impact,
                    risk_level='medium'
                ))

        # Remove duplicates and sort by benefit
        unique_actions = []
        seen = set()
        for action in actions:
            action_key = (action.action_type, tuple(action.sql_commands))
            if action_key not in seen:
                unique_actions.append(action)
                seen.add(action_key)

        return unique_actions

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard."""
        import time
        logger.info("🔍 START: get_performance_dashboard()")

        try:
            logger.info("🔍 Analyzing slow queries...")
            analyze_start = time.time()
            issues = self.analyze_slow_queries()
            analyze_time = time.time() - analyze_start
            logger.info(".3f")

            # Group issues by type and severity
            issue_stats = {}
            for issue in issues:
                key = f"{issue.issue_type}_{issue.severity}"
                issue_stats[key] = issue_stats.get(key, 0) + 1

            # Get top slow queries
            top_queries = sorted(issues, key=lambda x: x.metrics['mean_time'], reverse=True)[:10]

            # Generate optimization plan
            optimization_plan = self.generate_optimization_plan(issues)

            return {
                'total_issues': len(issues),
                'issue_breakdown': issue_stats,
                'top_slow_queries': [
                    {
                        'query': q.query_text,
                        'mean_time': q.metrics['mean_time'],
                        'calls': q.metrics['calls'],
                        'issue_type': q.issue_type,
                        'severity': q.severity
                    }
                    for q in top_queries
                ],
                'optimization_plan': [
                    {
                        'type': a.action_type,
                        'description': a.description,
                        'commands': a.sql_commands,
                        'benefit': a.estimated_benefit,
                        'risk': a.risk_level
                    }
                    for a in optimization_plan
                ],
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate performance dashboard: {e}")
            return {"error": str(e)}

    def apply_optimization(self, action: OptimizationAction, dry_run: bool = True) -> Dict[str, Any]:
        """Apply a specific optimization action."""
        result = {
            'action_type': action.action_type,
            'description': action.description,
            'success': False,
            'dry_run': dry_run,
            'executed_commands': [],
            'errors': []
        }

        if dry_run:
            result['executed_commands'] = action.sql_commands
            result['success'] = True
            return result

        try:
            conn, cursor = self._get_cursor()
            try:
                for cmd in action.sql_commands:
                    cursor.execute(cmd)
                    result['executed_commands'].append(cmd)

                # Commit changes
                if conn:
                    conn.commit()  # For connection pool
                else:
                    self.connection.commit()  # For direct connection
                result['success'] = True
            finally:
                self._close_cursor(conn, cursor)

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Failed to apply optimization: {e}")

        return result
