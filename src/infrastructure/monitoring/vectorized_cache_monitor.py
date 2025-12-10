"""Vectorized cache monitoring with high-performance analytics."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
import threading
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class VectorizedCacheMetrics:
    """Vectorized cache performance metrics."""
    heap_hit_ratio: np.ndarray  # Array of hit ratios over time
    index_hit_ratio: np.ndarray
    shared_buffer_usage: np.ndarray
    temp_files_created: np.ndarray
    temp_bytes_written: np.ndarray
    timestamps: np.ndarray
    trend_analysis: Dict[str, float]  # Trend coefficients

@dataclass
class CacheAlert:
    """Cache performance alert."""
    alert_type: str
    severity: str
    message: str
    recommendations: List[str]
    timestamp: datetime
    metrics: Dict[str, float]

class VectorizedCacheMonitor:
    """High-performance cache monitoring using vectorized operations."""

    def __init__(self, connection_pool, alert_thresholds: Optional[Dict[str, float]] = None):
        self.connection_pool = connection_pool
        self.alert_thresholds = alert_thresholds or {
            'heap_hit_ratio_min': 0.95,
            'index_hit_ratio_min': 0.90,
            'shared_buffer_usage_max': 0.90,
            'temp_files_max': 100,
            'temp_bytes_max': 1_000_000_000,
        }

        self.alert_handlers: List[Callable[[CacheAlert], None]] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Vectorized data storage
        self.metrics_history = []
        self.alerts_history = []

        # Thread pool for parallel analysis
        self.executor = ThreadPoolExecutor(max_workers=2)

    def start_monitoring(self, interval_seconds: int = 300) -> None:
        """Start background cache monitoring with vectorized analysis."""
        if self.monitoring_active:
            logger.warning("Cache monitoring already active")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._vectorized_monitoring_loop,
            args=(interval_seconds,),
            daemon=True,
            name="VectorizedCacheMonitor"
        )
        self.monitor_thread.start()
        logger.info(f"Started vectorized cache monitoring with {interval_seconds}s interval")

    def stop_monitoring(self) -> None:
        """Stop background cache monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("Stopped vectorized cache monitoring")

    def add_alert_handler(self, handler: Callable[[CacheAlert], None]) -> None:
        """Add alert handler function."""
        self.alert_handlers.append(handler)

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current cache metrics."""
        try:
            conn = self.connection_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    return self._execute_vectorized_cache_queries(cursor)
            finally:
                self.connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {}

    def _vectorized_monitoring_loop(self, interval_seconds: int) -> None:
        """Vectorized monitoring loop with parallel analysis."""
        while self.monitoring_active:
            try:
                start_time = time.time()

                # Get metrics (blocking DB operation)
                current_metrics = self.get_current_metrics()
                if not current_metrics:
                    time.sleep(interval_seconds)
                    continue

                # Parallel analysis using thread pool
                analysis_future = self.executor.submit(
                    self._parallel_cache_analysis,
                    current_metrics
                )

                # Convert to vectorized format and store
                vectorized_metrics = self._convert_to_vectorized(current_metrics)
                self.metrics_history.append(vectorized_metrics)

                # Keep only last 100 measurements for trend analysis
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]

                # Get analysis results
                alerts = analysis_future.result(timeout=10)

                # Process alerts
                for alert in alerts:
                    self.alerts_history.append(alert)
                    self._notify_alert_handlers(alert)

                # Calculate processing time
                processing_time = time.time() - start_time
                logger.debug(".2f")

                # Sleep for remaining interval
                sleep_time = max(0, interval_seconds - processing_time)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval_seconds)

    def _execute_vectorized_cache_queries(self, cursor) -> Dict[str, float]:
        """Execute cache queries optimized for vectorization."""
        try:
            # Get basic cache statistics
            cursor.execute("""
                SELECT
                    sum(heap_blks_hit) * 1.0 / (sum(heap_blks_hit) + sum(heap_blks_read)) as heap_hit_ratio,
                    sum(idx_blks_hit) * 1.0 / (sum(idx_blks_hit) + sum(idx_blks_read)) as index_hit_ratio,
                    sum(buffers_backend) * 8192.0 / (SELECT setting::float * 1024*1024 FROM pg_settings WHERE name = 'shared_buffers') as shared_buffer_usage,
                    sum(temp_files) as temp_files_created,
                    sum(temp_bytes) as temp_bytes_written
                FROM pg_stat_database
                WHERE datname = current_database()
            """)

            result = cursor.fetchone()
            if not result:
                return {}

            heap_hit_ratio, index_hit_ratio, shared_buffer_usage, temp_files, temp_bytes = result

            # Handle null values
            metrics = {
                'heap_hit_ratio': float(heap_hit_ratio or 0),
                'index_hit_ratio': float(index_hit_ratio or 0),
                'shared_buffer_usage': float(shared_buffer_usage or 0),
                'temp_files_created': int(temp_files or 0),
                'temp_bytes_written': int(temp_bytes or 0),
                'timestamp': time.time()
            }

            return metrics

        except Exception as e:
            logger.error(f"Cache query execution failed: {e}")
            return {}

    def _convert_to_vectorized(self, metrics: Dict[str, float]) -> VectorizedCacheMetrics:
        """Convert scalar metrics to vectorized format."""
        return VectorizedCacheMetrics(
            heap_hit_ratio=np.array([metrics['heap_hit_ratio']]),
            index_hit_ratio=np.array([metrics['index_hit_ratio']]),
            shared_buffer_usage=np.array([metrics['shared_buffer_usage']]),
            temp_files_created=np.array([metrics['temp_files_created']]),
            temp_bytes_written=np.array([metrics['temp_bytes_written']]),
            timestamps=np.array([metrics['timestamp']]),
            trend_analysis={}
        )

    def _parallel_cache_analysis(self, current_metrics: Dict[str, float]) -> List[CacheAlert]:
        """Parallel analysis of cache metrics using vectorization."""
        alerts = []

        # Vectorized threshold checking
        heap_ratio = current_metrics['heap_hit_ratio']
        index_ratio = current_metrics['index_hit_ratio']
        buffer_usage = current_metrics['shared_buffer_usage']
        temp_files = current_metrics['temp_files_created']
        temp_bytes = current_metrics['temp_bytes_written']

        # Vectorized alert detection
        alert_conditions = np.array([
            heap_ratio < self.alert_thresholds['heap_hit_ratio_min'],
            index_ratio < self.alert_thresholds['index_hit_ratio_min'],
            buffer_usage > self.alert_thresholds['shared_buffer_usage_max'],
            temp_files > self.alert_thresholds['temp_files_max'],
            temp_bytes > self.alert_thresholds['temp_bytes_max']
        ])

        alert_types = [
            'low_heap_hit_ratio',
            'low_index_hit_ratio',
            'high_buffer_usage',
            'high_temp_files',
            'high_temp_bytes'
        ]

        # Generate alerts for triggered conditions
        for i, triggered in enumerate(alert_conditions):
            if triggered:
                alert = self._create_alert(alert_types[i], current_metrics)
                alerts.append(alert)

        return alerts

    def _create_alert(self, alert_type: str, metrics: Dict[str, float]) -> CacheAlert:
        """Create alert with recommendations using vectorized logic."""
        alert_configs = {
            'low_heap_hit_ratio': {
                'severity': 'high',
                'message': f"Heap cache hit ratio is {metrics['heap_hit_ratio']:.1%} (threshold: {self.alert_thresholds['heap_hit_ratio_min']:.1%})",
                'recommendations': [
                    "Increase shared_buffers",
                    "Review frequently accessed tables for proper indexing",
                    "Consider table partitioning for large tables",
                    "Run ANALYZE on tables with stale statistics"
                ]
            },
            'low_index_hit_ratio': {
                'severity': 'medium',
                'message': f"Index cache hit ratio is {metrics['index_hit_ratio']:.1%} (threshold: {self.alert_thresholds['index_hit_ratio_min']:.1%})",
                'recommendations': [
                    "Review index usage and remove unused indexes",
                    "Consider covering indexes for frequently queried columns",
                    "Optimize index bloat with REINDEX",
                    "Consider increasing effective_cache_size"
                ]
            },
            'high_buffer_usage': {
                'severity': 'medium',
                'message': f"Shared buffer usage is {metrics['shared_buffer_usage']:.1%} (threshold: {self.alert_thresholds['shared_buffer_usage_max']:.1%})",
                'recommendations': [
                    "Monitor for memory pressure",
                    "Consider increasing shared_buffers if RAM allows",
                    "Review connection pooling settings",
                    "Consider work_mem optimization"
                ]
            },
            'high_temp_files': {
                'severity': 'medium',
                'message': f"High temp file creation: {metrics['temp_files_created']} files/hour",
                'recommendations': [
                    "Increase work_mem to reduce temp file usage",
                    "Review queries with large sorts/grouping operations",
                    "Consider adding indexes for ORDER BY operations",
                    "Monitor for query optimization opportunities"
                ]
            },
            'high_temp_bytes': {
                'severity': 'high',
                'message': ".1f",
                'recommendations': [
                    "Increase work_mem significantly",
                    "Optimize queries with large intermediate results",
                    "Consider query rewriting for better memory usage",
                    "Review hash join vs sort performance"
                ]
            }
        }

        config = alert_configs.get(alert_type, {
            'severity': 'low',
            'message': f"Cache alert: {alert_type}",
            'recommendations': ["Review cache configuration"]
        })

        return CacheAlert(
            alert_type=alert_type,
            severity=config['severity'],
            message=config['message'],
            recommendations=config['recommendations'],
            timestamp=datetime.now(),
            metrics=metrics
        )

    def get_trend_analysis(self) -> Dict[str, float]:
        """Get trend analysis using vectorized operations."""
        if len(self.metrics_history) < 2:
            return {}

        try:
            # Combine all historical data into arrays
            all_heap_ratios = np.concatenate([m.heap_hit_ratio for m in self.metrics_history])
            all_index_ratios = np.concatenate([m.index_hit_ratio for m in self.metrics_history])
            all_timestamps = np.concatenate([m.timestamps for m in self.metrics_history])

            # Calculate trends using numpy polyfit
            time_range = all_timestamps - all_timestamps[0]

            heap_trend = np.polyfit(time_range, all_heap_ratios, 1)[0]
            index_trend = np.polyfit(time_range, all_index_ratios, 1)[0]

            return {
                'heap_hit_ratio_trend': float(heap_trend),
                'index_hit_ratio_trend': float(index_trend),
                'data_points': len(all_timestamps)
            }

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {}

    def _notify_alert_handlers(self, alert: CacheAlert) -> None:
        """Notify all alert handlers."""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
