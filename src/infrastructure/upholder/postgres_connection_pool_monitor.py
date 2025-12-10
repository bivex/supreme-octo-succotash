"""PostgreSQL connection pool monitoring and optimization for Auto Upholder."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..monitoring.adaptive_connection_pool_optimizer import (
    AdaptiveConnectionPoolOptimizer,
    PoolOptimizationRecommendation,
    PoolOptimizationAction
)

logger = logging.getLogger(__name__)


class PostgresConnectionPoolMonitor:
    """Connection pool monitor for PostgreSQL Auto Upholder integration."""

    def __init__(self, connection_pool):
        """
        Initialize connection pool monitor.

        Args:
            connection_pool: AdvancedConnectionPool instance
        """
        self.connection_pool = connection_pool
        self.optimizer = AdaptiveConnectionPoolOptimizer(connection_pool)
        self.is_monitoring = False

        # Integration with upholder alerts
        self._setup_alert_handlers()

    def _setup_alert_handlers(self) -> None:
        """Setup alert handlers for integration with upholder system."""

        def pool_alert_handler(alert_type: str, message: str, metrics_data) -> None:
            """Handle pool alerts and forward to upholder system."""
            # This will be called by the optimizer when alerts occur
            # The actual alert forwarding happens through upholder's alert handlers
            logger.warning(f"Connection Pool Alert [{alert_type}]: {message}")

        def optimization_handler(recommendation: PoolOptimizationRecommendation) -> None:
            """Handle optimization recommendations."""
            logger.info(f"Connection Pool Optimization: {recommendation.action.value} "
                       f"({recommendation.confidence_score:.1f}% confidence) - {recommendation.reason}")

        self.optimizer.add_alert_handler(pool_alert_handler)
        self.optimizer.add_optimization_handler(optimization_handler)

    def start_monitoring(self) -> None:
        """Start connection pool monitoring."""
        if self.is_monitoring:
            logger.warning("Connection pool monitoring already active")
            return

        try:
            self.optimizer.start_monitoring()
            self.is_monitoring = True
            logger.info("Connection pool monitoring started")
        except Exception as e:
            logger.error(f"Failed to start connection pool monitoring: {e}")

    def stop_monitoring(self) -> None:
        """Stop connection pool monitoring."""
        if not self.is_monitoring:
            logger.info("Connection pool monitoring already stopped")
            return

        try:
            self.optimizer.stop_monitoring()
            self.is_monitoring = False
            logger.info("Connection pool monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping connection pool monitoring: {e}")

    def get_pool_status(self) -> Dict[str, Any]:
        """Get comprehensive connection pool status."""
        try:
            performance_report = self.optimizer.get_performance_report()

            return {
                'is_monitoring': self.is_monitoring,
                'pool_metrics': performance_report.get('current_metrics', {}),
                'performance_trends': performance_report.get('recent_trends', {}),
                'load_analysis': performance_report.get('load_pattern_analysis', {}),
                'optimization_recommendations': performance_report.get('optimization_recommendations', []),
                'health_status': performance_report.get('pool_health_status', 'UNKNOWN'),
                'raw_pool_stats': self.connection_pool.get_stats(),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {
                'error': str(e),
                'is_monitoring': self.is_monitoring,
                'last_updated': datetime.now().isoformat()
            }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get current optimization suggestions for the connection pool."""
        try:
            recommendations = self.optimizer.get_optimization_recommendations()

            return [
                {
                    'action': rec.action.value,
                    'reason': rec.reason,
                    'current_value': rec.current_value,
                    'recommended_value': rec.recommended_value,
                    'confidence_score': round(rec.confidence_score, 1),
                    'expected_impact': rec.expected_impact,
                    'risk_level': rec.risk_level,
                    'complexity': rec.implementation_complexity,
                    'priority': self._calculate_priority(rec)
                }
                for rec in recommendations
            ]

        except Exception as e:
            logger.error(f"Failed to get optimization suggestions: {e}")
            return []

    def _calculate_priority(self, recommendation: PoolOptimizationRecommendation) -> str:
        """Calculate priority level for a recommendation."""
        # High priority for critical situations
        if recommendation.confidence_score >= 90:
            return "CRITICAL"
        elif recommendation.confidence_score >= 80:
            return "HIGH"
        elif recommendation.confidence_score >= 70:
            return "MEDIUM"
        else:
            return "LOW"

    def apply_optimization(self, action: str, dry_run: bool = True) -> Dict[str, Any]:
        """Apply a specific optimization action."""
        try:
            # Find the recommendation for this action
            recommendations = self.optimizer.get_optimization_recommendations()
            matching_rec = None

            for rec in recommendations:
                if rec.action.value == action:
                    matching_rec = rec
                    break

            if not matching_rec:
                return {
                    'success': False,
                    'error': f'No recommendation found for action: {action}'
                }

            # Apply the optimization
            result = self.optimizer.apply_optimization(matching_rec, dry_run=dry_run)

            return {
                'success': result['success'],
                'action': result['action'],
                'old_value': result['old_value'],
                'new_value': result['new_value'],
                'dry_run': result['dry_run'],
                'error': result.get('error'),
                'applied_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to apply optimization {action}: {e}")
            return {
                'success': False,
                'error': str(e),
                'action': action,
                'applied_at': datetime.now().isoformat()
            }

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            'is_monitoring': self.is_monitoring,
            'metrics_collected': len(self.optimizer.metrics_history),
            'monitoring_interval_seconds': self.optimizer.monitoring_interval,
            'optimization_cooldown_minutes': self.optimizer.optimization_cooldown.total_seconds() / 60,
            'alerts_configured': len(self.optimizer.alert_handlers),
            'optimization_handlers': len(self.optimizer.optimization_handlers),
            'thresholds': self.optimizer.thresholds
        }

    def reset_monitoring_data(self) -> bool:
        """Reset monitoring data and patterns."""
        try:
            self.optimizer.reset_metrics_history()
            logger.info("Connection pool monitoring data reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset monitoring data: {e}")
            return False

    def analyze_pool_performance(self) -> Dict[str, Any]:
        """Analyze overall pool performance and provide insights."""
        try:
            status = self.get_pool_status()
            suggestions = self.get_optimization_suggestions()

            # Calculate performance score
            health_status = status.get('health_status', 'UNKNOWN')
            metrics = status.get('pool_metrics', {})
            efficiency = metrics.get('efficiency_score', 0)

            # Performance scoring
            performance_score = 0
            if health_status == 'HEALTHY':
                performance_score = 90
            elif health_status == 'SUBOPTIMAL':
                performance_score = 70
            elif health_status == 'WARNING':
                performance_score = 50
            elif health_status == 'CRITICAL':
                performance_score = 20
            else:
                performance_score = 0

            # Adjust based on efficiency
            performance_score = min(100, performance_score + (efficiency - 50) / 2)

            insights = []

            # Generate insights based on data
            if efficiency >= 80:
                insights.append("Connection pool is highly efficient")
            elif efficiency >= 60:
                insights.append("Connection pool performance is good")
            elif efficiency >= 40:
                insights.append("Connection pool needs optimization")
            else:
                insights.append("Connection pool performance is poor - immediate action required")

            if metrics.get('utilization_rate', 0) > 85:
                insights.append("High connection utilization - consider increasing max connections")
            elif metrics.get('utilization_rate', 0) < 30:
                insights.append("Low connection utilization - consider reducing max connections")

            if metrics.get('connection_errors', 0) > 0:
                insights.append(f"Connection errors detected: {metrics.get('connection_errors', 0)}")

            return {
                'performance_score': round(performance_score, 1),
                'health_status': health_status,
                'insights': insights,
                'critical_actions_needed': len([s for s in suggestions if s['priority'] == 'CRITICAL']),
                'recommended_actions': len(suggestions),
                'analyzed_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to analyze pool performance: {e}")
            return {
                'error': str(e),
                'performance_score': 0,
                'analyzed_at': datetime.now().isoformat()
            }
