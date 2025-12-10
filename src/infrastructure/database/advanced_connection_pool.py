#!/usr/bin/env python3
"""
Advanced PostgreSQL connection pool with monitoring and optimization.
"""

import psycopg2
from psycopg2 import pool
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ConnectionPoolStats:
    """Statistics for connection pool monitoring."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.connections_created = 0
        self.connections_returned = 0
        self.connections_failed = 0
        self.query_count = 0
        self.total_query_time = 0.0
        self.slow_queries = 0
        self.errors = 0
        self.created_at = datetime.now()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total_time = (datetime.now() - self.created_at).total_seconds()
        avg_query_time = self.total_query_time / max(self.query_count, 1)

        return {
            'connections_created': self.connections_created,
            'connections_returned': self.connections_returned,
            'connections_failed': self.connections_failed,
            'query_count': self.query_count,
            'avg_query_time_ms': round(avg_query_time * 1000, 2),
            'slow_queries': self.slow_queries,
            'errors': self.errors,
            'qps': round(self.query_count / max(total_time, 1), 2),
            'uptime_seconds': round(total_time, 1)
        }

class AdvancedConnectionPool:
    """
    Advanced PostgreSQL connection pool with monitoring, optimization and health checks.
    """

    def __init__(self,
                 minconn: int = 5,
                 maxconn: int = 32,
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "supreme_octosuccotash_db",
                 user: str = "app_user",
                 password: str = "app_password",
                 **kwargs):
        """
        Initialize advanced connection pool.

        Args:
            minconn: Minimum number of connections
            maxconn: Maximum number of connections
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            **kwargs: Additional psycopg2 connection parameters
        """
        self._config = {
            'minconn': minconn,
            'maxconn': maxconn,
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            **kwargs
        }

        # Connection pool
        self._pool = pool.SimpleConnectionPool(**self._config)

        # Statistics and monitoring
        self._stats = ConnectionPoolStats()
        self._lock = threading.Lock()
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0

        logger.info(f"AdvancedConnectionPool initialized: minconn={minconn}, maxconn={maxconn}")

    def getconn(self) -> psycopg2.extensions.connection:
        """
        Get a connection from the pool with monitoring.

        Returns:
            Database connection

        Raises:
            Exception: If connection cannot be obtained
        """
        start_time = time.time()

        try:
            conn = self._pool.getconn()
            elapsed = time.time() - start_time

            with self._lock:
                self._stats.connections_created += 1

            # Test connection health
            if not self._is_connection_healthy(conn):
                logger.warning("Unhealthy connection detected, creating new one")
                try:
                    conn.close()
                except:
                    pass
                conn = self._create_new_connection()

            logger.debug(".3f")
            return conn

        except Exception as e:
            elapsed = time.time() - start_time
            with self._lock:
                self._stats.connections_failed += 1

            logger.error(".3f")
            raise e

    def putconn(self, conn: psycopg2.extensions.connection) -> None:
        """
        Return a connection to the pool.

        Args:
            conn: Database connection to return
        """
        try:
            # Quick health check before returning
            if self._is_connection_healthy(conn, quick=True):
                self._pool.putconn(conn)
                with self._lock:
                    self._stats.connections_returned += 1
                logger.debug("Connection returned to pool")
            else:
                logger.warning("Unhealthy connection discarded")
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing unhealthy connection: {e}")

        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")

    def execute_with_monitoring(self, conn: psycopg2.extensions.connection,
                               query: str, params: tuple = None) -> Any:
        """
        Execute query with performance monitoring.

        Args:
            conn: Database connection
            query: SQL query
            params: Query parameters

        Returns:
            Query result
        """
        start_time = time.time()

        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()

            elapsed = time.time() - start_time

            with self._lock:
                self._stats.query_count += 1
                self._stats.total_query_time += elapsed

                # Track slow queries (>100ms)
                if elapsed > 0.1:
                    self._stats.slow_queries += 1
                    logger.warning(".3f")

            logger.debug(".3f")
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            with self._lock:
                self._stats.errors += 1

            logger.error(".3f")
            raise e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive pool statistics.

        Returns:
            Dictionary with pool and performance statistics
        """
        with self._lock:
            pool_stats = {
                'minconn': getattr(self._pool, '_minconn', 0),
                'maxconn': getattr(self._pool, '_maxconn', 0),
                'used': len(getattr(self._pool, '_used', [])),
                'available': len(getattr(self._pool, '_pool', [])),
            }

            return {
                **pool_stats,
                **self._stats.get_summary(),
                'pool_efficiency': self._calculate_pool_efficiency(pool_stats),
                'health_status': self._get_health_status()
            }

    def _calculate_pool_efficiency(self, pool_stats: Dict[str, Any]) -> float:
        """Calculate pool utilization efficiency."""
        used = pool_stats.get('used', 0)
        max_conn = pool_stats.get('maxconn', 1)

        if max_conn == 0:
            return 0.0

        # Optimal utilization is 60-80%
        utilization = used / max_conn

        if 0.6 <= utilization <= 0.8:
            return 100.0  # Perfect utilization
        elif 0.3 <= utilization < 0.6:
            return 75.0   # Good utilization
        elif 0.8 < utilization <= 0.95:
            return 60.0   # High utilization, may need more connections
        else:
            return 40.0   # Poor utilization

    def _get_health_status(self) -> str:
        """Get overall pool health status."""
        with self._lock:
            error_rate = self._stats.errors / max(self._stats.query_count, 1)
            failure_rate = self._stats.connections_failed / max(self._stats.connections_created, 1)

        if error_rate > 0.05 or failure_rate > 0.02:
            return "CRITICAL"
        elif error_rate > 0.01 or failure_rate > 0.005:
            return "WARNING"
        else:
            return "HEALTHY"

    def _is_connection_healthy(self, conn: psycopg2.extensions.connection,
                              quick: bool = False) -> bool:
        """
        Check if connection is healthy.

        Args:
            conn: Connection to check
            quick: If True, do only basic checks

        Returns:
            True if connection is healthy
        """
        if conn.closed:
            return False

        if quick:
            # Just check if we can get cursor
            try:
                cursor = conn.cursor()
                cursor.close()
                return True
            except:
                return False

        # Full health check
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except:
            return False

    def _create_new_connection(self) -> psycopg2.extensions.connection:
        """Create a new database connection."""
        return psycopg2.connect(**self._config)

    def closeall(self) -> None:
        """Close all connections in the pool."""
        logger.info("Closing all connections in advanced pool")
        self._pool.closeall()

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        with self._lock:
            self._stats.reset()
        logger.info("Pool statistics reset")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.closeall()
