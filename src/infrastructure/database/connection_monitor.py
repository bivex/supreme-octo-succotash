"""
Database connection monitoring and health checks.
"""

import logging
import time
import threading
from typing import Dict, List, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConnectionMonitor:
    """
    Monitors database connection health and alerts on issues.
    """

    def __init__(self, container, check_interval: int = 60):
        """
        Initialize connection monitor.

        Args:
            container: Dependency injection container
            check_interval: Health check interval in seconds
        """
        self._container = container
        self._check_interval = check_interval
        self._running = False
        self._thread = None
        self._alerts: List[Callable] = []
        self._last_connection_error = None
        self._error_count = 0
        self._consecutive_errors = 0

    def add_alert_callback(self, callback: Callable):
        """Add callback to be called when connection issues are detected."""
        self._alerts.append(callback)

    def start_monitoring(self):
        """Start the connection monitoring thread."""
        if self._running:
            logger.warning("Connection monitor already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("🔍 Connection monitor started")

    def stop_monitoring(self):
        """Stop the connection monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("🔍 Connection monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                self._perform_health_check()
            except Exception as e:
                logger.error(f"Connection monitor health check failed: {e}")

            time.sleep(self._check_interval)

    def _perform_health_check(self):
        """Perform database connection health check."""
        try:
            # Try to get a connection from the pool
            conn = self._container.get_db_connection()

            # Test the connection with a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()

            # Release connection back to pool
            self._container.release_db_connection(conn)

            # Connection successful - reset error counters
            if self._consecutive_errors > 0:
                logger.info(f"✅ Database connection restored after {self._consecutive_errors} consecutive errors")
                self._consecutive_errors = 0

        except Exception as e:
            self._handle_connection_error(e)

    def _handle_connection_error(self, error: Exception):
        """Handle database connection errors."""
        self._error_count += 1
        self._consecutive_errors += 1
        self._last_connection_error = {
            'error': str(error),
            'timestamp': datetime.now(),
            'consecutive_errors': self._consecutive_errors
        }

        # Log based on severity
        if self._consecutive_errors == 1:
            logger.warning(f"⚠️  Database connection issue detected: {error}")
        elif self._consecutive_errors >= 3:
            logger.error(f"🚨 CRITICAL: Database connection failed {self._consecutive_errors} times consecutively: {error}")

            # Trigger alerts for critical issues
            self._trigger_alerts()

    def _trigger_alerts(self):
        """Trigger all registered alert callbacks."""
        alert_data = {
            'error_count': self._error_count,
            'consecutive_errors': self._consecutive_errors,
            'last_error': self._last_connection_error,
            'pool_stats': self._container.get_pool_stats()
        }

        for callback in self._alerts:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def get_health_status(self) -> Dict:
        """Get current connection health status."""
        return {
            'healthy': self._consecutive_errors == 0,
            'consecutive_errors': self._consecutive_errors,
            'total_errors': self._error_count,
            'last_error': self._last_connection_error,
            'pool_stats': self._container.get_pool_stats()
        }


def default_alert_callback(alert_data: Dict):
    """Default alert callback that logs critical connection issues."""
    logger.critical("🚨 DATABASE CONNECTION ALERT 🚨")
    logger.critical(f"Consecutive errors: {alert_data['consecutive_errors']}")
    logger.critical(f"Total errors: {alert_data['error_count']}")
    logger.critical(f"Last error: {alert_data['last_error']}")
    logger.critical(f"Pool stats: {alert_data['pool_stats']}")
    logger.critical("This may indicate database server issues or connection pool exhaustion")