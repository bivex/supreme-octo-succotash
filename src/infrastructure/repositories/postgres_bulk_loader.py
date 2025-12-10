"""PostgreSQL bulk loader with automatic COPY optimization for large datasets."""

import psycopg2
import csv
import io
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)


@dataclass
class BulkLoadResult:
    """Result of bulk load operation."""
    table_name: str
    method_used: str  # 'copy' or 'insert'
    records_loaded: int
    execution_time: float
    success: bool
    error_message: Optional[str] = None


class PostgresBulkLoader:
    """Automatic bulk loader that chooses optimal method based on data size."""

    def __init__(self, connection, batch_size_threshold: int = 1000):
        self.connection = connection
        self.batch_size_threshold = batch_size_threshold

    def bulk_insert(self, table_name: str, records: List[Dict[str, Any]],
                   conflict_resolution: str = 'none') -> BulkLoadResult:
        """Automatically choose between COPY and individual INSERTs based on data size."""
        start_time = time.time()

        try:
            if len(records) >= self.batch_size_threshold:
                # Use COPY for large datasets
                return self._bulk_copy(table_name, records, start_time)
            else:
                # Use individual INSERTs for small datasets
                return self._bulk_insert(table_name, records, conflict_resolution, start_time)

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Bulk insert failed for table {table_name}: {e}")
            return BulkLoadResult(
                table_name=table_name,
                method_used='failed',
                records_loaded=0,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )

    def _bulk_copy(self, table_name: str, records: List[Dict[str, Any]], start_time: float) -> BulkLoadResult:
        """Load data using COPY command."""
        try:
            # Get column names from first record
            if not records:
                return BulkLoadResult(
                    table_name=table_name,
                    method_used='copy',
                    records_loaded=0,
                    execution_time=time.time() - start_time,
                    success=True
                )

            columns = list(records[0].keys())

            # Create CSV data in memory
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer, quoting=csv.QUOTE_MINIMAL)

            # Write data rows
            for record in records:
                row = [record.get(col, '') for col in columns]
                writer.writerow(row)

            csv_data = csv_buffer.getvalue()
            csv_buffer.close()

            # Execute COPY command
            copy_query = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH CSV"

            with self.connection.cursor() as cursor:
                cursor.copy_expert(copy_query, io.StringIO(csv_data))
                self.connection.commit()

            execution_time = time.time() - start_time
            logger.info(f"Successfully loaded {len(records)} records into {table_name} using COPY")

            return BulkLoadResult(
                table_name=table_name,
                method_used='copy',
                records_loaded=len(records),
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            logger.error(f"COPY bulk load failed for {table_name}: {e}")
            raise

    def _bulk_insert(self, table_name: str, records: List[Dict[str, Any]],
                    conflict_resolution: str, start_time: float) -> BulkLoadResult:
        """Load data using individual INSERT statements."""
        try:
            if not records:
                return BulkLoadResult(
                    table_name=table_name,
                    method_used='insert',
                    records_loaded=0,
                    execution_time=time.time() - start_time,
                    success=True
                )

            columns = list(records[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)

            # Build conflict resolution clause
            conflict_clause = self._build_conflict_clause(conflict_resolution, columns)

            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) {conflict_clause}"

            with self.connection.cursor() as cursor:
                # Use executemany for batch processing
                values = [[record.get(col) for col in columns] for record in records]
                cursor.executemany(query, values)
                self.connection.commit()

            execution_time = time.time() - start_time
            logger.info(f"Successfully loaded {len(records)} records into {table_name} using INSERT")

            return BulkLoadResult(
                table_name=table_name,
                method_used='insert',
                records_loaded=len(records),
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            logger.error(f"INSERT bulk load failed for {table_name}: {e}")
            raise

    def _build_conflict_clause(self, conflict_resolution: str, columns: List[str]) -> str:
        """Build ON CONFLICT clause for INSERT statements."""
        if conflict_resolution == 'none':
            return ''
        elif conflict_resolution == 'update':
            # ON CONFLICT DO UPDATE SET
            update_parts = [f"{col} = EXCLUDED.{col}" for col in columns if col != 'id']
            return f"ON CONFLICT (id) DO UPDATE SET {', '.join(update_parts)}"
        elif conflict_resolution == 'ignore':
            return "ON CONFLICT DO NOTHING"
        else:
            return ''

    def bulk_insert_clicks(self, clicks: List[Dict[str, Any]]) -> BulkLoadResult:
        """Optimized bulk insert for click data."""
        # Ensure required fields are present
        required_fields = ['id', 'campaign_id', 'ip_address', 'user_agent', 'created_at']

        for click in clicks:
            for field in required_fields:
                if field not in click:
                    click[field] = None

        return self.bulk_insert('clicks', clicks, conflict_resolution='ignore')

    def bulk_insert_conversions(self, conversions: List[Dict[str, Any]]) -> BulkLoadResult:
        """Optimized bulk insert for conversion data."""
        required_fields = ['id', 'click_id', 'goal_id', 'amount', 'currency', 'created_at']

        for conv in conversions:
            for field in required_fields:
                if field not in conv:
                    conv[field] = None

        return self.bulk_insert('conversions', conversions, conflict_resolution='ignore')

    def bulk_insert_events(self, events: List[Dict[str, Any]]) -> BulkLoadResult:
        """Optimized bulk insert for event data."""
        required_fields = ['id', 'click_id', 'event_type', 'event_data', 'created_at']

        for event in events:
            for field in required_fields:
                if field not in event:
                    event[field] = None

        return self.bulk_insert('events', events, conflict_resolution='ignore')


class BulkOperationOptimizer:
    """Optimizer for bulk operations with automatic performance monitoring."""

    def __init__(self, connection):
        self.connection = connection
        self.loader = PostgresBulkLoader(connection)
        self.performance_stats = {}

    def optimize_bulk_operation(self, table_name: str, records: List[Dict[str, Any]],
                               operation_type: str = 'generic') -> BulkLoadResult:
        """Optimize bulk operation based on table type and data characteristics."""
        # Analyze data characteristics
        data_size = len(records)
        avg_record_size = self._estimate_record_size(records[0]) if records else 0

        # Choose optimal method based on heuristics
        if operation_type == 'clicks':
            result = self.loader.bulk_insert_clicks(records)
        elif operation_type == 'conversions':
            result = self.loader.bulk_insert_conversions(records)
        elif operation_type == 'events':
            result = self.loader.bulk_insert_events(records)
        else:
            # Generic bulk insert with conflict resolution
            conflict_resolution = 'update' if table_name in ['campaigns', 'offers'] else 'ignore'
            result = self.loader.bulk_insert(table_name, records, conflict_resolution)

        # Record performance stats
        self._record_performance_stats(table_name, result, data_size, avg_record_size)

        return result

    def _estimate_record_size(self, record: Dict[str, Any]) -> int:
        """Estimate size of a record in bytes."""
        size = 0
        for value in record.values():
            if isinstance(value, str):
                size += len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                size += 8  # Rough estimate
            elif value is None:
                size += 1  # NULL indicator
            else:
                size += len(str(value).encode('utf-8'))
        return size

    def _record_performance_stats(self, table_name: str, result: BulkLoadResult,
                                data_size: int, avg_record_size: int):
        """Record performance statistics for analysis."""
        if table_name not in self.performance_stats:
            self.performance_stats[table_name] = []

        stats = {
            'timestamp': time.time(),
            'method': result.method_used,
            'records': result.records_loaded,
            'execution_time': result.execution_time,
            'records_per_second': result.records_loaded / result.execution_time if result.execution_time > 0 else 0,
            'avg_record_size': avg_record_size,
            'success': result.success
        }

        self.performance_stats[table_name].append(stats)

        # Keep only last 100 entries per table
        if len(self.performance_stats[table_name]) > 100:
            self.performance_stats[table_name] = self.performance_stats[table_name][-100:]

    def get_performance_report(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance report for bulk operations."""
        if table_name:
            stats = self.performance_stats.get(table_name, [])
        else:
            stats = []
            for table_stats in self.performance_stats.values():
                stats.extend(table_stats)

        if not stats:
            return {"message": "No performance data available"}

        # Calculate averages
        total_records = sum(s['records'] for s in stats)
        total_time = sum(s['execution_time'] for s in stats)
        avg_rps = total_records / total_time if total_time > 0 else 0

        copy_stats = [s for s in stats if s['method'] == 'copy']
        insert_stats = [s for s in stats if s['method'] == 'insert']

        return {
            'total_operations': len(stats),
            'total_records': total_records,
            'avg_records_per_second': avg_rps,
            'copy_operations': len(copy_stats),
            'insert_operations': len(insert_stats),
            'copy_avg_rps': sum(s['records_per_second'] for s in copy_stats) / len(copy_stats) if copy_stats else 0,
            'insert_avg_rps': sum(s['records_per_second'] for s in insert_stats) / len(insert_stats) if insert_stats else 0,
            'recommendations': self._generate_performance_recommendations(stats)
        }

    def _generate_performance_recommendations(self, stats: List[Dict]) -> List[str]:
        """Generate performance recommendations based on stats."""
        recommendations = []

        copy_ops = [s for s in stats if s['method'] == 'copy']
        insert_ops = [s for s in stats if s['method'] == 'insert']

        if copy_ops and insert_ops:
            copy_avg = sum(s['records_per_second'] for s in copy_ops) / len(copy_ops)
            insert_avg = sum(s['records_per_second'] for s in insert_ops) / len(insert_ops)

            if copy_avg > insert_avg * 2:  # COPY is significantly faster
                recommendations.append("🚀 COPY method is significantly faster than INSERT. Consider using COPY for all bulk operations > 100 records.")

        # Check for performance degradation
        if len(stats) >= 10:
            recent_stats = stats[-10:]
            older_stats = stats[-20:-10] if len(stats) >= 20 else stats[:10]

            recent_avg = sum(s['records_per_second'] for s in recent_stats) / len(recent_stats)
            older_avg = sum(s['records_per_second'] for s in older_stats) / len(older_stats)

            if recent_avg < older_avg * 0.8:  # 20% degradation
                recommendations.append("📉 Performance degradation detected. Consider database maintenance or index optimization.")

        return recommendations


class SmartBulkRepositoryMixin:
    """Mixin to add smart bulk loading capabilities to repositories."""

    def __init__(self, container):
        super().__init__(container)
        self.bulk_optimizer = BulkOperationOptimizer(self._get_connection())

    def smart_bulk_insert(self, records: List[Dict[str, Any]], operation_type: str = 'generic') -> BulkLoadResult:
        """Smart bulk insert with automatic optimization."""
        table_name = self._get_table_name()
        return self.bulk_optimizer.optimize_bulk_operation(table_name, records, operation_type)

    def _get_table_name(self) -> str:
        """Get table name for this repository (override in subclasses)."""
        # Default implementation - extract from class name
        class_name = self.__class__.__name__
        if 'Repository' in class_name:
            return class_name.replace('Repository', '').lower()
        return 'unknown_table'

    def get_bulk_performance_stats(self) -> Dict[str, Any]:
        """Get bulk operation performance statistics."""
        table_name = self._get_table_name()
        return self.bulk_optimizer.get_performance_report(table_name)
