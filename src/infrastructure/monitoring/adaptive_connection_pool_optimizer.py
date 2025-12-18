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

"""Adaptive PostgreSQL connection pool optimizer with real-time monitoring and optimization."""

import psycopg2
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
import logging
import time
import threading
from datetime import datetime, timedelta
from collections import deque
import statistics
from enum import Enum

logger = logging.getLogger(__name__)


class PoolOptimizationAction(Enum):
    """Types of pool optimization actions."""
    INCREASE_MAX = "increase_max_connections"
    DECREASE_MAX = "decrease_max_connections"
    INCREASE_MIN = "increase_min_connections"
    DECREASE_MIN = "decrease_min_connections"
    SCALE_UP = "scale_up_pool"
    SCALE_DOWN = "scale_down_pool"
    MAINTAIN = "maintain_current"


@dataclass
class PoolMetrics:
    """Real-time connection pool metrics."""
    timestamp: datetime
    used_connections: int
    available_connections: int
    total_connections: int
    min_connections: int
    max_connections: int
    connection_wait_time: float = 0.0
    query_queue_length: int = 0
    connection_errors: int = 0
    avg_query_time: float = 0.0

    @property
    def utilization_rate(self) -> float:
        """Calculate current pool utilization rate."""
        return (self.used_connections / self.max_connections) * 100 if self.max_connections > 0 else 0

    @property
    def efficiency_score(self) -> float:
        """Calculate pool efficiency score (0-100)."""
        utilization = self.utilization_rate

        # Optimal utilization is 60-80%
        if 60 <= utilization <= 80:
            return 100.0
        elif 40 <= utilization < 60:
            return 85.0
        elif 80 < utilization <= 90:
            return 70.0
        elif 30 <= utilization < 40:
            return 60.0
        elif 90 < utilization <= 95:
            return 40.0
        else:
            return 20.0


@dataclass
class PoolOptimizationRecommendation:
    """Recommendation for pool optimization."""
    action: PoolOptimizationAction
    reason: str
    current_value: int
    recommended_value: int
    confidence_score: float  # 0-100
    expected_impact: str
    risk_level: str  # 'low', 'medium', 'high'
    implementation_complexity: str  # 'easy', 'medium', 'hard'


@dataclass
class PoolLoadPattern:
    """Analysis of connection pool load patterns."""
    peak_hours: List[int] = field(default_factory=list)  # Hours with high load
    low_hours: List[int] = field(default_factory=list)   # Hours with low load
    avg_utilization_by_hour: Dict[int, float] = field(default_factory=dict)
    peak_utilization: float = 0.0
    low_utilization: float = 0.0
    recommended_min_conn: int = 5
    recommended_max_conn: int = 32
    scaling_events: int = 0
    last_scaling_time: Optional[datetime] = None


class AdaptiveConnectionPoolOptimizer:
    """Adaptive optimizer for PostgreSQL connection pools."""

    def __init__(self, pool, monitoring_interval: int = 30):
        """
        Initialize the adaptive pool optimizer.

        Args:
            pool: Connection pool instance (AdvancedConnectionPool)
            monitoring_interval: Monitoring interval in seconds
        """
        self.pool = pool
        self.monitoring_interval = monitoring_interval

        # Metrics storage (keep last 24 hours of data)
        self.metrics_history: deque[PoolMetrics] = deque(maxlen=2880)  # 24h * 60min * 2 samples/min

        # Load pattern analysis
        self.load_pattern = PoolLoadPattern()

        # Optimization state
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.last_optimization_time: Optional[datetime] = None
        self.optimization_cooldown = timedelta(minutes=15)  # Don't optimize too frequently

        # Optimization thresholds
        self.thresholds = {
            'high_utilization': 85.0,      # % - trigger scale up
            'low_utilization': 30.0,       # % - trigger scale down consideration
            'critical_utilization': 95.0,  # % - emergency scale up
            'min_efficiency': 60.0,        # Minimum efficiency score
            'max_connection_errors': 5,    # Max errors per monitoring cycle
            'scaling_confidence': 70.0     # Minimum confidence for auto-scaling
        }

        # Callbacks
        self.optimization_handlers: List[Callable[[PoolOptimizationRecommendation], None]] = []
        self.alert_handlers: List[Callable[[str, str, Any], None]] = []

        logger.info("Adaptive Connection Pool Optimizer initialized")

    def start_monitoring(self) -> None:
        """Start background monitoring and optimization."""
        if self.is_monitoring:
            logger.warning("Pool monitoring already active")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="PoolOptimizer-Monitor"
        )
        self.monitoring_thread.start()

        logger.info(f"Started adaptive pool monitoring (interval: {self.monitoring_interval}s)")

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        if not self.is_monitoring:
            logger.info("Pool monitoring already stopped")
            return

        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)

        logger.info("Stopped adaptive pool monitoring")

    def get_current_metrics(self) -> PoolMetrics:
        """Get current pool metrics."""
        try:
            # Get pool stats from AdvancedConnectionPool
            pool_stats = self.pool.get_stats()

            return PoolMetrics(
                timestamp=datetime.now(),
                used_connections=pool_stats.get('used', 0),
                available_connections=pool_stats.get('available', 0),
                total_connections=pool_stats.get('used', 0) + pool_stats.get('available', 0),
                min_connections=pool_stats.get('minconn', 0),
                max_connections=pool_stats.get('maxconn', 0),
                connection_errors=pool_stats.get('errors', 0),
                avg_query_time=pool_stats.get('avg_query_time_ms', 0) / 1000  # Convert to seconds
            )

        except Exception as e:
            logger.error(f"Failed to get pool metrics: {e}")
            return PoolMetrics(
                timestamp=datetime.now(),
                used_connections=0,
                available_connections=0,
                total_connections=0,
                min_connections=0,
                max_connections=0
            )

    def analyze_load_patterns(self) -> PoolLoadPattern:
        """Analyze historical load patterns to optimize pool sizing."""
        if len(self.metrics_history) < 10:
            logger.warning("Insufficient metrics data for pattern analysis")
            return self.load_pattern

        try:
            # Group metrics by hour
            hourly_stats: Dict[int, List[float]] = {}
            for metric in self.metrics_history:
                hour = metric.timestamp.hour
                if hour not in hourly_stats:
                    hourly_stats[hour] = []
                hourly_stats[hour].append(metric.utilization_rate)

            # Calculate average utilization by hour
            avg_by_hour = {}
            peak_hours = []
            low_hours = []

            for hour, utilizations in hourly_stats.items():
                avg_util = statistics.mean(utilizations)
                avg_by_hour[hour] = avg_util

                if avg_util >= 70:
                    peak_hours.append(hour)
                elif avg_util <= 40:
                    low_hours.append(hour)

            # Calculate recommended pool sizes
            peak_utilization = max(avg_by_hour.values()) if avg_by_hour else 0
            low_utilization = min(avg_by_hour.values()) if avg_by_hour else 0

            # Base recommendations on utilization patterns
            current_max = self.load_pattern.recommended_max_conn
            current_min = self.load_pattern.recommended_min_conn

            # For peak hours, ensure we can handle 80% utilization
            if peak_utilization > 0:
                recommended_max = max(current_max, int((peak_utilization / 80) * current_max * 1.2))
                recommended_max = min(recommended_max, 200)  # Cap at reasonable limit
            else:
                recommended_max = current_max

            # For low hours, we can reduce min connections
            if low_utilization < 30:
                recommended_min = max(2, int(current_min * 0.7))
            else:
                recommended_min = current_min

            # Update load pattern
            self.load_pattern.peak_hours = peak_hours
            self.load_pattern.low_hours = low_hours
            self.load_pattern.avg_utilization_by_hour = avg_by_hour
            self.load_pattern.peak_utilization = peak_utilization
            self.load_pattern.low_utilization = low_utilization
            self.load_pattern.recommended_min_conn = recommended_min
            self.load_pattern.recommended_max_conn = recommended_max

            logger.info(f"Load pattern analysis complete: peak_hours={peak_hours}, "
                       f"recommended_min={recommended_min}, recommended_max={recommended_max}")

            return self.load_pattern

        except Exception as e:
            logger.error(f"Failed to analyze load patterns: {e}")
            return self.load_pattern

    def get_optimization_recommendations(self) -> List[PoolOptimizationRecommendation]:
        """Get optimization recommendations based on current metrics and patterns."""
        recommendations = []
        current_metrics = self.get_current_metrics()

        # Analyze current utilization
        utilization = current_metrics.utilization_rate
        efficiency = current_metrics.efficiency_score

        # Critical utilization - emergency scaling
        if utilization >= self.thresholds['critical_utilization']:
            recommendations.append(PoolOptimizationRecommendation(
                action=PoolOptimizationAction.SCALE_UP,
                reason=f"Pool utilization is {utilization:.1f}% (threshold: {self.thresholds['critical_utilization']*100:.1f}%)",
                current_value=current_metrics.max_connections,
                recommended_value=min(current_metrics.max_connections + 10, 200),
                confidence_score=95.0,
                expected_impact="Immediate relief from connection pressure",
                risk_level="low",
                implementation_complexity="easy"
            ))

        # High utilization - gradual scaling
        elif utilization >= self.thresholds['high_utilization']:
            recommendations.append(PoolOptimizationRecommendation(
                action=PoolOptimizationAction.INCREASE_MAX,
                reason=f"Pool utilization is {utilization:.1f}% (threshold: {self.thresholds['high_utilization']*100:.1f}%)",
                current_value=current_metrics.max_connections,
                recommended_value=min(current_metrics.max_connections + 5, 150),
                confidence_score=85.0,
                expected_impact="Better handling of concurrent requests",
                risk_level="low",
                implementation_complexity="easy"
            ))

        # Low utilization - consider scaling down
        elif utilization <= self.thresholds['low_utilization'] and current_metrics.max_connections > 20:
            recommendations.append(PoolOptimizationRecommendation(
                action=PoolOptimizationAction.DECREASE_MAX,
                reason=f"Pool utilization is {utilization:.1f}% (threshold: {self.thresholds['low_utilization']*100:.1f}%)",
                current_value=current_metrics.max_connections,
                recommended_value=max(current_metrics.max_connections - 5, 10),
                confidence_score=70.0,
                expected_impact="Reduced resource usage",
                risk_level="medium",
                implementation_complexity="easy"
            ))

        # Low efficiency - analyze patterns
        if efficiency < self.thresholds['min_efficiency']:
            load_pattern = self.analyze_load_patterns()

            # Pattern-based optimization
            if load_pattern.recommended_max_conn > current_metrics.max_connections:
                recommendations.append(PoolOptimizationRecommendation(
                    action=PoolOptimizationAction.SCALE_UP,
                    reason=f"Load pattern analysis suggests higher max connections (peak hours: {load_pattern.peak_hours})",
                    current_value=current_metrics.max_connections,
                    recommended_value=load_pattern.recommended_max_conn,
                    confidence_score=80.0,
                    expected_impact="Optimized for peak load patterns",
                    risk_level="low",
                    implementation_complexity="medium"
                ))

            elif load_pattern.recommended_min_conn < current_metrics.min_connections:
                recommendations.append(PoolOptimizationRecommendation(
                    action=PoolOptimizationAction.DECREASE_MIN,
                    reason=f"Low baseline utilization allows reducing min connections",
                    current_value=current_metrics.min_connections,
                    recommended_value=load_pattern.recommended_min_conn,
                    confidence_score=75.0,
                    expected_impact="Reduced idle connection overhead",
                    risk_level="medium",
                    implementation_complexity="easy"
                ))

        # Connection errors - investigate pool health
        if current_metrics.connection_errors > self.thresholds['max_connection_errors']:
            recommendations.append(PoolOptimizationRecommendation(
                action=PoolOptimizationAction.MAINTAIN,
                reason=f"High connection errors ({current_metrics.connection_errors}) - investigate pool health",
                current_value=current_metrics.max_connections,
                recommended_value=current_metrics.max_connections,
                confidence_score=90.0,
                expected_impact="Pool health investigation needed",
                risk_level="high",
                implementation_complexity="hard"
            ))

        return recommendations

    def apply_optimization(self, recommendation: PoolOptimizationRecommendation,
                          dry_run: bool = True) -> Dict[str, Any]:
        """Apply a pool optimization recommendation."""
        result = {
            'success': False,
            'action': recommendation.action.value,
            'old_value': recommendation.current_value,
            'new_value': recommendation.recommended_value,
            'dry_run': dry_run,
            'error': None
        }

        if dry_run:
            result['success'] = True
            logger.info(f"DRY RUN: Would apply {recommendation.action.value}: "
                       f"{recommendation.current_value} -> {recommendation.recommended_value}")
            return result

        try:
            # Note: In a real implementation, you'd need to modify the pool's min/max settings
            # This would require pool recreation or dynamic reconfiguration
            # For now, we'll log the recommendation and suggest manual implementation

            logger.warning(f"Automatic pool reconfiguration not implemented. "
                          f"Manual action required: {recommendation.action.value} "
                          f"from {recommendation.current_value} to {recommendation.recommended_value}")

            result['success'] = False
            result['error'] = "Automatic pool reconfiguration not implemented - manual action required"

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Failed to apply pool optimization: {e}")

        return result

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive pool performance report."""
        current_metrics = self.get_current_metrics()
        recommendations = self.get_optimization_recommendations()
        load_pattern = self.analyze_load_patterns()

        # Calculate trends
        recent_metrics = list(self.metrics_history)[-60:] if self.metrics_history else []  # Last hour

        avg_utilization = statistics.mean([m.utilization_rate for m in recent_metrics]) if recent_metrics else 0
        max_utilization = max([m.utilization_rate for m in recent_metrics]) if recent_metrics else 0
        min_utilization = min([m.utilization_rate for m in recent_metrics]) if recent_metrics else 0

        return {
            'current_metrics': {
                'utilization_rate': round(current_metrics.utilization_rate, 1),
                'efficiency_score': round(current_metrics.efficiency_score, 1),
                'used_connections': current_metrics.used_connections,
                'total_connections': current_metrics.total_connections,
                'connection_errors': current_metrics.connection_errors,
                'avg_query_time_ms': round(current_metrics.avg_query_time * 1000, 2)
            },
            'recent_trends': {
                'avg_utilization_last_hour': round(avg_utilization, 1),
                'max_utilization_last_hour': round(max_utilization, 1),
                'min_utilization_last_hour': round(min_utilization, 1),
                'samples_count': len(recent_metrics)
            },
            'load_pattern_analysis': {
                'peak_hours': load_pattern.peak_hours,
                'low_hours': load_pattern.low_hours,
                'recommended_min_conn': load_pattern.recommended_min_conn,
                'recommended_max_conn': load_pattern.recommended_max_conn,
                'peak_utilization': round(load_pattern.peak_utilization, 1),
                'low_utilization': round(load_pattern.low_utilization, 1)
            },
            'optimization_recommendations': [
                {
                    'action': rec.action.value,
                    'reason': rec.reason,
                    'confidence': round(rec.confidence_score, 1),
                    'risk_level': rec.risk_level,
                    'expected_impact': rec.expected_impact
                }
                for rec in recommendations
            ],
            'pool_health_status': self._assess_pool_health(current_metrics),
            'generated_at': datetime.now().isoformat()
        }

    def _assess_pool_health(self, metrics: PoolMetrics) -> str:
        """Assess overall pool health status."""
        issues = []

        if metrics.utilization_rate > 90:
            issues.append("critical_utilization")
        elif metrics.utilization_rate > 80:
            issues.append("high_utilization")

        if metrics.efficiency_score < 50:
            issues.append("low_efficiency")

        if metrics.connection_errors > 10:
            issues.append("high_errors")

        if not issues:
            return "HEALTHY"
        elif "critical_utilization" in issues:
            return "CRITICAL"
        elif len(issues) > 1:
            return "WARNING"
        else:
            return "SUBOPTIMAL"

    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                # Collect metrics
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)

                # Check for alerts
                self._check_alerts(metrics)

                # Periodic optimization check (every 5 minutes)
                now = datetime.now()
                if (not self.last_optimization_time or
                    now - self.last_optimization_time > self.optimization_cooldown):

                    recommendations = self.get_optimization_recommendations()
                    high_confidence_recs = [r for r in recommendations if r.confidence_score >= 80]

                    if high_confidence_recs:
                        for rec in high_confidence_recs:
                            self._notify_optimization_handlers(rec)

                        self.last_optimization_time = now

                # Analyze load patterns weekly (every 168 monitoring cycles)
                if len(self.metrics_history) % (168 * 2) == 0:  # ~weekly
                    self.analyze_load_patterns()

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            time.sleep(self.monitoring_interval)

    def _check_alerts(self, metrics: PoolMetrics) -> None:
        """Check for pool performance alerts."""
        alerts = []

        if metrics.utilization_rate >= self.thresholds['critical_utilization']:
            alerts.append(("critical_utilization",
                          f"Pool utilization is {metrics.utilization_rate:.1f}% (threshold: {self.thresholds['critical_utilization']*100:.1f}%)",
                          metrics))

        elif metrics.utilization_rate >= self.thresholds['high_utilization']:
            alerts.append(("high_utilization",
                          f"Pool utilization is {metrics.utilization_rate:.1f}% (threshold: {self.thresholds['high_utilization']*100:.1f}%)",
                          metrics))

        if metrics.connection_errors > self.thresholds['max_connection_errors']:
            alerts.append(("connection_errors",
                          f"High connection errors: {metrics.connection_errors}",
                          metrics))

        # Notify alert handlers
        for alert_type, message, metrics_data in alerts:
            for handler in self.alert_handlers:
                try:
                    handler(alert_type, message, metrics_data)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")

    def _notify_optimization_handlers(self, recommendation: PoolOptimizationRecommendation) -> None:
        """Notify optimization handlers."""
        for handler in self.optimization_handlers:
            try:
                handler(recommendation)
            except Exception as e:
                logger.error(f"Optimization handler failed: {e}")

    def add_optimization_handler(self, handler: Callable[[PoolOptimizationRecommendation], None]) -> None:
        """Add optimization recommendation handler."""
        self.optimization_handlers.append(handler)

    def add_alert_handler(self, handler: Callable[[str, str, Any], None]) -> None:
        """Add alert handler."""
        self.alert_handlers.append(handler)

    def reset_metrics_history(self) -> None:
        """Reset metrics history (useful for testing)."""
        self.metrics_history.clear()
        self.load_pattern = PoolLoadPattern()
        logger.info("Pool optimizer metrics history reset")
