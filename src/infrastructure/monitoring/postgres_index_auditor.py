"""PostgreSQL index auditor for automatic index optimization recommendations."""

import psycopg2
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class IndexRecommendation:
    """Recommendation for index creation."""
    table: str
    columns: List[str]
    index_type: str  # 'btree', 'hash', 'gin', 'gist', 'partial', 'expression'
    reason: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    estimated_impact: str
    ddl_statement: str


@dataclass
class IndexAuditResult:
    """Result of index audit."""
    table_name: str
    existing_indexes: List[Dict]
    missing_indexes: List[IndexRecommendation]
    unused_indexes: List[Dict]
    bloated_indexes: List[Dict]
    recommendations: List[str]


class PostgresIndexAuditor:
    """Automatic auditor for PostgreSQL indexes."""

    def __init__(self, connection):
        self.connection = connection

    def audit_all_tables(self) -> Dict[str, IndexAuditResult]:
        """Audit indexes for all tables in the database."""
        try:
            with self.connection.cursor() as cursor:
                # Get all user tables
                cursor.execute("""
                    SELECT schemaname, tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)

                results = {}
                for schema, table in cursor.fetchall():
                    results[table] = self.audit_table_indexes(table)

                return results

        except Exception as e:
            logger.error(f"Failed to audit all tables: {e}")
            return {}

    def audit_table_indexes(self, table_name: str) -> IndexAuditResult:
        """Audit indexes for a specific table."""
        try:
            existing_indexes = self._get_existing_indexes(table_name)
            query_patterns = self._analyze_query_patterns(table_name)
            missing_indexes = self._find_missing_indexes(table_name, existing_indexes, query_patterns)
            unused_indexes = self._find_unused_indexes(table_name)
            bloated_indexes = self._find_bloated_indexes(table_name)

            recommendations = self._generate_recommendations(missing_indexes, unused_indexes, bloated_indexes)

            return IndexAuditResult(
                table_name=table_name,
                existing_indexes=existing_indexes,
                missing_indexes=missing_indexes,
                unused_indexes=unused_indexes,
                bloated_indexes=bloated_indexes,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Failed to audit table {table_name}: {e}")
            return IndexAuditResult(
                table_name=table_name,
                existing_indexes=[],
                missing_indexes=[],
                unused_indexes=[],
                bloated_indexes=[],
                recommendations=[f"Audit failed: {str(e)}"]
            )

    def _get_existing_indexes(self, table_name: str) -> List[Dict]:
        """Get existing indexes for a table."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        i.indexname,
                        i.indexdef,
                        pg_size_pretty(pg_relation_size(i.indexname::regclass)) as size,
                        idx_scan as usage_count,
                        pg_stat_get_last_autoanalyze_time(c.oid) as last_analyze
                    FROM pg_indexes i
                    LEFT JOIN pg_stat_user_indexes ui ON i.indexname = ui.indexname
                    LEFT JOIN pg_class c ON c.relname = i.tablename
                    WHERE i.tablename = %s
                    ORDER BY i.indexname
                """, (table_name,))

                indexes = []
                for row in cursor.fetchall():
                    indexes.append({
                        'name': row[0],
                        'definition': row[1],
                        'size': row[2],
                        'usage_count': row[3] or 0,
                        'last_analyze': row[4]
                    })

                return indexes

        except Exception as e:
            logger.error(f"Failed to get existing indexes for {table_name}: {e}")
            return []

    def _analyze_query_patterns(self, table_name: str) -> Dict[str, Set[str]]:
        """Analyze query patterns that access this table."""
        patterns = {
            'where_columns': set(),
            'join_columns': set(),
            'order_columns': set(),
            'group_columns': set()
        }

        try:
            # Get query patterns from pg_stat_statements
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT query, calls
                    FROM pg_stat_statements
                    WHERE query ILIKE %s
                    ORDER BY calls DESC
                    LIMIT 50
                """, (f'%{table_name}%',))

                for row in cursor.fetchall():
                    query = row[0]
                    calls = row[1]

                    # Analyze query for column usage patterns
                    where_cols = self._extract_columns_from_where(query, table_name)
                    join_cols = self._extract_columns_from_joins(query, table_name)
                    order_cols = self._extract_columns_from_order(query, table_name)
                    group_cols = self._extract_columns_from_group(query, table_name)

                    # Weight by call frequency
                    weight = min(calls // 10, 10)  # Max weight of 10

                    for _ in range(weight):
                        patterns['where_columns'].update(where_cols)
                        patterns['join_columns'].update(join_cols)
                        patterns['order_columns'].update(order_cols)
                        patterns['group_columns'].update(group_cols)

        except Exception as e:
            logger.error(f"Failed to analyze query patterns for {table_name}: {e}")

        return patterns

    def _extract_columns_from_where(self, query: str, table_name: str) -> Set[str]:
        """Extract column names from WHERE clauses."""
        columns = set()
        query_lower = query.lower()

        # Simple regex-based extraction
        where_match = re.search(r'where\s+(.+?)(?:group|order|limit|$)', query_lower, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            # Find column references (simplified)
            col_matches = re.findall(r'\b(\w+)\s*[=<>!]+\s*[%\'\w]+', where_clause)
            columns.update(col_matches)

        return columns

    def _extract_columns_from_joins(self, query: str, table_name: str) -> Set[str]:
        """Extract column names from JOIN conditions."""
        columns = set()
        query_lower = query.lower()

        # Look for JOIN ... ON conditions
        join_matches = re.findall(r'join\s+\w+\s+on\s+(.+?)(?:join|where|group|order|$)', query_lower, re.IGNORECASE)
        for join_condition in join_matches:
            # Extract column references
            col_matches = re.findall(r'\b(\w+)\s*=\s*\w+\.\w+', join_condition)
            columns.update(col_matches)

        return columns

    def _extract_columns_from_order(self, query: str, table_name: str) -> Set[str]:
        """Extract column names from ORDER BY clauses."""
        columns = set()
        query_lower = query.lower()

        order_match = re.search(r'order\s+by\s+(.+?)(?:limit|$)', query_lower, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            # Extract column names
            col_matches = re.findall(r'\b(\w+)\s*(?:asc|desc)?(?:,|$)', order_clause, re.IGNORECASE)
            columns.update([col.strip().split()[0] for col in col_matches if col.strip()])

        return columns

    def _extract_columns_from_group(self, query: str, table_name: str) -> Set[str]:
        """Extract column names from GROUP BY clauses."""
        columns = set()
        query_lower = query.lower()

        group_match = re.search(r'group\s+by\s+(.+?)(?:order|having|$)', query_lower, re.IGNORECASE)
        if group_match:
            group_clause = group_match.group(1)
            # Extract column names
            col_matches = re.findall(r'\b(\w+)\s*(?:,|$)', group_clause)
            columns.update([col.strip() for col in col_matches if col.strip()])

        return columns

    def _find_missing_indexes(self, table_name: str, existing_indexes: List[Dict],
                            query_patterns: Dict[str, Set[str]]) -> List[IndexRecommendation]:
        """Find missing indexes based on query patterns."""
        recommendations = []

        # Get table column info
        table_columns = self._get_table_columns(table_name)

        # Analyze WHERE columns
        where_columns = list(query_patterns['where_columns'])
        if where_columns:
            for col in where_columns[:3]:  # Top 3 most used
                if col in table_columns and not self._index_exists(existing_indexes, [col]):
                    recommendations.append(IndexRecommendation(
                        table=table_name,
                        columns=[col],
                        index_type='btree',
                        reason=f"WHERE clause uses column '{col}'",
                        priority=self._calculate_priority(col, query_patterns),
                        estimated_impact="High",
                        ddl_statement=f"CREATE INDEX CONCURRENTLY ON {table_name} ({col})"
                    ))

        # Analyze JOIN columns
        join_columns = list(query_patterns['join_columns'])
        if join_columns:
            for col in join_columns[:2]:  # Top 2 most used
                if col in table_columns and not self._index_exists(existing_indexes, [col]):
                    recommendations.append(IndexRecommendation(
                        table=table_name,
                        columns=[col],
                        index_type='btree',
                        reason=f"JOIN condition uses column '{col}'",
                        priority="high",
                        estimated_impact="Critical",
                        ddl_statement=f"CREATE INDEX CONCURRENTLY ON {table_name} ({col})"
                    ))

        # Analyze composite indexes for WHERE + ORDER BY
        order_columns = list(query_patterns['order_columns'])
        if where_columns and order_columns:
            for where_col in where_columns[:2]:
                for order_col in order_columns[:2]:
                    if where_col != order_col and not self._index_exists(existing_indexes, [where_col, order_col]):
                        recommendations.append(IndexRecommendation(
                            table=table_name,
                            columns=[where_col, order_col],
                            index_type='btree',
                            reason=f"WHERE + ORDER BY on columns '{where_col}', '{order_col}'",
                            priority="medium",
                            estimated_impact="Medium",
                            ddl_statement=f"CREATE INDEX CONCURRENTLY ON {table_name} ({where_col}, {order_col})"
                        ))

        return recommendations

    def _index_exists(self, existing_indexes: List[Dict], columns: List[str]) -> bool:
        """Check if an index exists for the given columns."""
        for index in existing_indexes:
            index_def = index['definition'].lower()
            # Check if all columns are in the index definition
            if all(col.lower() in index_def for col in columns):
                return True
        return False

    def _get_table_columns(self, table_name: str) -> Set[str]:
        """Get column names for a table."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY column_name
                """, (table_name,))

                return {row[0] for row in cursor.fetchall()}

        except Exception as e:
            logger.error(f"Failed to get columns for table {table_name}: {e}")
            return set()

    def _calculate_priority(self, column: str, patterns: Dict[str, Set[str]]) -> str:
        """Calculate priority for index recommendation."""
        usage_count = 0

        # Count usage across all patterns
        for pattern_cols in patterns.values():
            if column in pattern_cols:
                usage_count += 1

        if usage_count >= 3:
            return "high"
        elif usage_count >= 2:
            return "medium"
        else:
            return "low"

    def _find_unused_indexes(self, table_name: str) -> List[Dict]:
        """Find indexes that haven't been used recently."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        indexname,
                        idx_scan as usage_count,
                        pg_size_pretty(pg_relation_size(indexname::regclass)) as size,
                        pg_stat_get_last_idx_scan_time(indexrelid) as last_used
                    FROM pg_stat_user_indexes
                    WHERE tablename = %s
                    AND idx_scan = 0
                    AND schemaname = 'public'
                """, (table_name,))

                unused = []
                for row in cursor.fetchall():
                    unused.append({
                        'name': row[0],
                        'usage_count': row[1] or 0,
                        'size': row[2],
                        'last_used': row[3]
                    })

                return unused

        except Exception as e:
            logger.error(f"Failed to find unused indexes for {table_name}: {e}")
            return []

    def _find_bloated_indexes(self, table_name: str) -> List[Dict]:
        """Find bloated indexes that need rebuilding."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        indexname,
                        pg_size_pretty(pg_relation_size(indexname::regclass)) as size,
                        n_tup_ins, n_tup_upd, n_tup_del,
                        (n_tup_ins + n_tup_upd + n_tup_del) as total_operations
                    FROM pg_stat_user_indexes
                    WHERE tablename = %s
                    AND (n_tup_ins + n_tup_upd + n_tup_del) > 10000
                    ORDER BY total_operations DESC
                """, (table_name,))

                bloated = []
                for row in cursor.fetchall():
                    bloated.append({
                        'name': row[0],
                        'size': row[1],
                        'inserts': row[2],
                        'updates': row[3],
                        'deletes': row[4],
                        'total_operations': row[5]
                    })

                return bloated

        except Exception as e:
            logger.error(f"Failed to find bloated indexes for {table_name}: {e}")
            return []

    def _generate_recommendations(self, missing: List[IndexRecommendation],
                                unused: List[Dict], bloated: List[Dict]) -> List[str]:
        """Generate human-readable recommendations."""
        recommendations = []

        if missing:
            recommendations.append(f"📈 Missing {len(missing)} indexes - will improve query performance")

        if unused:
            recommendations.append(f"🗑️ {len(unused)} unused indexes - consider dropping to save space")

        if bloated:
            recommendations.append(f"🔄 {len(bloated)} bloated indexes - consider REINDEX CONCURRENTLY")

        if not any([missing, unused, bloated]):
            recommendations.append("✅ Index configuration looks optimal")

        return recommendations

    def apply_recommendations(self, recommendations: List[IndexRecommendation],
                            dry_run: bool = True) -> List[str]:
        """Apply index recommendations."""
        applied = []

        for rec in recommendations:
            if rec.priority in ['high', 'critical']:
                if dry_run:
                    applied.append(f"DRY RUN: Would create {rec.ddl_statement}")
                else:
                    try:
                        with self.connection.cursor() as cursor:
                            cursor.execute(rec.ddl_statement)
                            self.connection.commit()
                        applied.append(f"✅ Created index: {rec.ddl_statement}")
                    except Exception as e:
                        applied.append(f"❌ Failed to create index: {e}")

        return applied
