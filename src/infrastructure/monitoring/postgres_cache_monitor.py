"""PostgreSQL cache monitoring with automatic alerts and optimization recommendations."""

import psycopg2
from typing import Dict, List, Any, Optional, Callable
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import json

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    heap_hit_ratio: float
    index_hit_ratio: float
    shared_buffer_usage: float
    temp_files_created: int
    temp_bytes_written: int
    timestamp: datetime


@dataclass
class CacheAlert:
    """Cache performance alert."""
    alert_type: str  # 'low_hit_ratio', 'high_temp_usage', 'buffer_pressure'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    recommendations: List[str]
    timestamp: datetime
    metrics: CacheMetrics


class PostgresCacheMonitor:
    """Automatic PostgreSQL cache monitoring and alerting system."""

    def __init__(self, connection, alert_thresholds: Optional[Dict[str, float]] = None):
        self.connection = connection
        self.alert_thresholds = alert_thresholds or {
            'heap_hit_ratio_min': 0.95,      # 95%
            'index_hit_ratio_min': 0.90,     # 90%
            'shared_buffer_usage_max': 0.90, # 90%
            'temp_files_max': 100,           # per hour
            'temp_bytes_max': 1_000_000_000  # 1GB per hour
        }

        self.alert_handlers: List[Callable[[CacheAlert], None]] = []
        self.metrics_history: List[CacheMetrics] = []
        self.alerts_history: List[CacheAlert] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self, interval_seconds: int = 300) -> None:
        """Start background cache monitoring."""
        if self.monitoring_active:
            logger.warning("Cache monitoring already active")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started cache monitoring with {interval_seconds}s interval")

    def stop_monitoring(self) -> None:
        """Stop background cache monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped cache monitoring")

    def add_alert_handler(self, handler: Callable[[CacheAlert], None]) -> None:
        """Add alert handler function."""
        self.alert_handlers.append(handler)

    def get_current_metrics(self) -> CacheMetrics:
        """Get current cache metrics."""
        try:
            # Get connection from pool if it's a pool, otherwise use directly
            if hasattr(self.connection, 'getconn'):
                # It's a connection pool
                conn = self.connection.getconn()
                try:
                    cursor = conn.cursor()
                    result = self._execute_cache_queries(cursor)
                    cursor.close()
                    return result
                finally:
                    self.connection.putconn(conn)
            else:
                # It's a direct connection
                with self.connection.cursor() as cursor:
                    return self._execute_cache_queries(cursor)
                # Get cache hit ratios
                cursor.execute("""
                    SELECT
                        sum(heap_blks_hit) * 100.0 / (sum(heap_blks_hit) + sum(heap_blks_read)) as heap_hit_ratio,
                        sum(idx_blks_hit) * 100.0 / (sum(idx_blks_hit) + sum(idx_blks_read)) as index_hit_ratio
                    FROM pg_statio_user_tables
                    WHERE heap_blks_hit + heap_blks_read > 0
                """)

                heap_ratio, index_ratio = cursor.fetchone()
                heap_ratio = heap_ratio or 0
                index_ratio = index_ratio or 0

                # Get shared buffer usage
                cursor.execute("""
                    SELECT
                        sum(CASE WHEN bufferid IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / setting::float as buffer_usage
                    FROM pg_buffercache b
                    CROSS JOIN pg_settings s
                    WHERE s.name = 'shared_buffers'
                """)

                buffer_usage_row = cursor.fetchone()
                buffer_usage = buffer_usage_row[0] if buffer_usage_row else 0

                # Get temporary file statistics (last hour)
                cursor.execute("""
                    SELECT
                        count(*) as temp_files,
                        sum(bytes) as temp_bytes
                    FROM pg_stat_database
                    WHERE temp_files > 0
                """)

                temp_row = cursor.fetchone()
                temp_files = temp_row[0] if temp_row else 0
                temp_bytes = temp_row[1] if temp_row else 0

                return CacheMetrics(
                    heap_hit_ratio=heap_ratio,
                    index_hit_ratio=index_ratio,
                    shared_buffer_usage=buffer_usage,
                    temp_files_created=temp_files,
                    temp_bytes_written=temp_bytes,
                    timestamp=datetime.now()
                )

        except Exception as e:
            logger.error(f"Failed to get cache metrics: {e}")
            return CacheMetrics(
                heap_hit_ratio=0,
                index_hit_ratio=0,
                shared_buffer_usage=0,
                temp_files_created=0,
                temp_bytes_written=0,
                timestamp=datetime.now()
            )

    def _execute_cache_queries(self, cursor) -> CacheMetrics:
        """Execute cache-related queries and return metrics."""
        # Get cache hit ratios
        cursor.execute("""
            SELECT
                sum(heap_blks_hit) * 100.0 / (sum(heap_blks_hit) + sum(heap_blks_read)) as heap_hit_ratio,
                sum(idx_blks_hit) * 100.0 / (sum(idx_blks_hit) + sum(idx_blks_read)) as index_hit_ratio
            FROM pg_statio_user_tables
            WHERE heap_blks_hit + heap_blks_read > 0
        """)

        heap_ratio, index_ratio = cursor.fetchone()
        heap_ratio = heap_ratio or 0
        index_ratio = index_ratio or 0

        # Get shared buffer usage
        cursor.execute("""
            SELECT
                sum(CASE WHEN bufferid IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / setting::float as buffer_usage
            FROM pg_buffercache b
            CROSS JOIN pg_settings s
            WHERE s.name = 'shared_buffers'
        """)

        buffer_usage_row = cursor.fetchone()
        buffer_usage = buffer_usage_row[0] if buffer_usage_row else 0

        # Get temporary file statistics (last hour)
        cursor.execute("""
            SELECT
                count(*) as temp_files,
                sum(bytes) as temp_bytes
            FROM pg_stat_database
            WHERE temp_files > 0
        """)

        temp_row = cursor.fetchone()
        temp_files = temp_row[0] if temp_row else 0
        temp_bytes = temp_row[1] if temp_row else 0

        return CacheMetrics(
            heap_hit_ratio=heap_ratio,
            index_hit_ratio=index_ratio,
            shared_buffer_usage=buffer_usage,
            temp_files_created=temp_files,
            temp_bytes_written=temp_bytes,
            timestamp=datetime.now()
        )

    def check_alerts(self, metrics: CacheMetrics) -> List[CacheAlert]:
        """Check for cache performance alerts."""
        alerts = []

        # Check heap hit ratio
        if metrics.heap_hit_ratio < self.alert_thresholds['heap_hit_ratio_min'] * 100:
            severity = 'high' if metrics.heap_hit_ratio < 90 else 'medium'
            alerts.append(CacheAlert(
                alert_type='low_heap_hit_ratio',
                severity=severity,
                message=f"Heap cache hit ratio is {metrics.heap_hit_ratio:.1f}% (threshold: {self.alert_thresholds['heap_hit_ratio_min']*100:.1f}%)",
                recommendations=[
                    "Consider increasing shared_buffers",
                    "Review frequently accessed tables for proper indexing",
                    "Consider table partitioning for large tables",
                    "Run ANALYZE on tables with stale statistics"
                ],
                timestamp=datetime.now(),
                metrics=metrics
            ))

        # Check index hit ratio
        if metrics.index_hit_ratio < self.alert_thresholds['index_hit_ratio_min'] * 100:
            severity = 'high' if metrics.index_hit_ratio < 80 else 'medium'
            alerts.append(CacheAlert(
                alert_type='low_index_hit_ratio',
                severity=severity,
                message=f"Index cache hit ratio is {metrics.index_hit_ratio:.1f}% (threshold: {self.alert_thresholds['index_hit_ratio_min']*100:.1f}%)",
                recommendations=[
                    "Review index usage - drop unused indexes",
                    "Consider covering indexes for frequent query patterns",
                    "Check for index bloat and rebuild if necessary",
                    "Consider increasing shared_buffers"
                ],
                timestamp=datetime.now(),
                metrics=metrics
            ))

        # Check shared buffer usage
        if metrics.shared_buffer_usage > self.alert_thresholds['shared_buffer_usage_max'] * 100:
            alerts.append(CacheAlert(
                alert_type='high_buffer_usage',
                severity='medium',
                message=f"Shared buffer usage is {metrics.shared_buffer_usage:.1f}% (threshold: {self.alert_thresholds['shared_buffer_usage_max']*100:.1f}%)",
                recommendations=[
                    "Consider increasing shared_buffers in postgresql.conf",
                    "Review and optimize frequently accessed data",
                    "Consider read replicas for heavy read workloads"
                ],
                timestamp=datetime.now(),
                metrics=metrics
            ))

        # Check temporary file creation
        if metrics.temp_files_created > self.alert_thresholds['temp_files_max']:
            alerts.append(CacheAlert(
                alert_type='high_temp_file_creation',
                severity='medium',
                message=f"High temporary file creation: {metrics.temp_files_created} files (threshold: {self.alert_thresholds['temp_files_max']})",
                recommendations=[
                    "Review queries causing temporary file creation",
                    "Consider increasing work_mem",
                    "Add missing indexes for ORDER BY / DISTINCT operations",
                    "Consider query optimization or partitioning"
                ],
                timestamp=datetime.now(),
                metrics=metrics
            ))

        return alerts

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get comprehensive cache optimization recommendations."""
        try:
            recommendations = {
                'immediate_actions': [],
                'configuration_changes': [],
                'monitoring_improvements': [],
                'query_optimizations': []
            }

            current_metrics = self.get_current_metrics()

            # Immediate actions based on current metrics
            if current_metrics.heap_hit_ratio < 95:
                recommendations['immediate_actions'].extend([
                    "Run ANALYZE on all tables to update statistics",
                    "Consider increasing shared_buffers by 25-50%",
                    "Review and optimize top N queries by total_time from pg_stat_statements"
                ])

            if current_metrics.index_hit_ratio < 90:
                recommendations['immediate_actions'].extend([
                    "Audit unused indexes and drop them",
                    "Rebuild bloated indexes with REINDEX CONCURRENTLY",
                    "Consider covering indexes for frequent query patterns"
                ])

            # Configuration recommendations
            recommendations['configuration_changes'] = self._get_config_recommendations()

            # Monitoring improvements
            recommendations['monitoring_improvements'] = [
                "Enable pg_stat_statements extension",
                "Set up monitoring for cache hit ratios",
                "Monitor temporary file creation trends",
                "Set up alerts for performance degradation"
            ]

            # Query optimization suggestions
            recommendations['query_optimizations'] = self._get_query_optimization_suggestions()

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return {"error": str(e)}

    def _get_config_recommendations(self) -> List[str]:
        """Get PostgreSQL configuration recommendations."""
        try:
            with self.connection.cursor() as cursor:
                # Get current configuration
                cursor.execute("""
                    SELECT name, setting, unit
                    FROM pg_settings
                    WHERE name IN ('shared_buffers', 'work_mem', 'maintenance_work_mem', 'effective_cache_size')
                """)

                config = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

                recommendations = []

                # Shared buffers recommendation
                shared_buffers = config.get('shared_buffers', ('0', None))[0]
                if shared_buffers:
                    try:
                        # Parse size (could be with units like MB, GB)
                        size_mb = self._parse_size(shared_buffers)
                        total_ram_mb = self._get_system_memory_mb()

                        if total_ram_mb and size_mb < total_ram_mb * 0.25:  # Less than 25% of RAM
                            recommendations.append(f"Increase shared_buffers from {shared_buffers} to {int(total_ram_mb * 0.25)}MB (25% of RAM)")
                    except:
                        pass

                # Work mem recommendation
                work_mem = config.get('work_mem', ('0', None))[0]
                if work_mem:
                    try:
                        work_mem_mb = self._parse_size(work_mem)
                        max_connections = self._get_max_connections()

                        if max_connections and work_mem_mb * max_connections > 1000:  # Over 1GB total
                            recommendations.append(f"Consider reducing work_mem from {work_mem} or reducing max_connections")
                    except:
                        pass

                return recommendations

        except Exception as e:
            logger.error(f"Failed to get config recommendations: {e}")
            return []

    def _get_query_optimization_suggestions(self) -> List[str]:
        """Get query optimization suggestions based on pg_stat_statements."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT query, calls, total_time, mean_time, rows
                    FROM pg_stat_statements
                    WHERE mean_time > 100  -- Queries taking > 100ms on average
                    ORDER BY mean_time DESC
                    LIMIT 10
                """)

                suggestions = []
                for row in cursor.fetchall():
                    query = row[0][:100] + '...' if len(row[0]) > 100 else row[0]
                    mean_time = row[3]

                    if 'seq scan' in query.lower() or 'Seq Scan' in query:
                        suggestions.append(f"Query with sequential scan taking {mean_time:.1f}ms - add indexes")
                    elif mean_time > 1000:  # Over 1 second
                        suggestions.append(f"Very slow query ({mean_time:.1f}ms) - needs optimization")
                    else:
                        suggestions.append(f"Slow query ({mean_time:.1f}ms) - consider optimization")

                return suggestions

        except Exception as e:
            logger.error(f"Failed to get query optimization suggestions: {e}")
            return []

    def _parse_size(self, size_str: str) -> float:
        """Parse PostgreSQL size string (e.g., '128MB') to MB."""
        size_str = size_str.lower().strip()

        if size_str.endswith('gb'):
            return float(size_str[:-2]) * 1024
        elif size_str.endswith('mb'):
            return float(size_str[:-2])
        elif size_str.endswith('kb'):
            return float(size_str[:-2]) / 1024
        else:
            # Assume MB if no unit
            return float(size_str)

    def _get_system_memory_mb(self) -> Optional[float]:
        """Get system memory in MB (simplified)."""
        # In production, you'd use system monitoring or pg_settings
        return None  # Placeholder

    def _get_max_connections(self) -> Optional[int]:
        """Get max_connections setting."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT setting FROM pg_settings WHERE name = 'max_connections'")
                return int(cursor.fetchone()[0])
        except:
            return None

    def _monitoring_loop(self, interval_seconds: int) -> None:
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)

                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                # Check for alerts
                alerts = self.check_alerts(metrics)
                for alert in alerts:
                    self.alerts_history.append(alert)
                    # Notify handlers
                    for handler in self.alert_handlers:
                        try:
                            handler(alert)
                        except Exception as e:
                            logger.error(f"Alert handler failed: {e}")

                # Keep only last 100 alerts
                if len(self.alerts_history) > 100:
                    self.alerts_history = self.alerts_history[-100:]

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

            time.sleep(interval_seconds)

    def get_monitoring_report(self) -> Dict[str, Any]:
        """Get comprehensive monitoring report."""
        if not self.metrics_history:
            return {"message": "No monitoring data available"}

        # Calculate trends
        recent_metrics = self.metrics_history[-10:] if len(self.metrics_history) >= 10 else self.metrics_history

        avg_heap_ratio = sum(m.heap_hit_ratio for m in recent_metrics) / len(recent_metrics)
        avg_index_ratio = sum(m.index_hit_ratio for m in recent_metrics) / len(recent_metrics)

        # Get recent alerts
        recent_alerts = [a for a in self.alerts_history if (datetime.now() - a.timestamp).seconds < 3600]  # Last hour

        return {
            'current_metrics': self.metrics_history[-1] if self.metrics_history else None,
            'average_metrics': {
                'heap_hit_ratio': avg_heap_ratio,
                'index_hit_ratio': avg_index_ratio
            },
            'alerts_count': len(recent_alerts),
            'recent_alerts': [a.message for a in recent_alerts[-5:]],  # Last 5 alerts
            'monitoring_active': self.monitoring_active,
            'metrics_collected': len(self.metrics_history)
        }


def create_default_cache_monitor(connection) -> PostgresCacheMonitor:
    """Create cache monitor with default settings."""
    monitor = PostgresCacheMonitor(connection)

    # Add default alert handler (logs alerts)
    def log_alert_handler(alert: CacheAlert):
        level = logging.WARNING if alert.severity in ['medium', 'high'] else logging.ERROR
        logger.log(level, f"Cache Alert [{alert.severity.upper()}]: {alert.message}")
        if alert.recommendations:
            logger.log(level, f"Recommendations: {', '.join(alert.recommendations)}")

    monitor.add_alert_handler(log_alert_handler)

    return monitor
