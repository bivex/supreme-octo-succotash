#!/usr/bin/env python3
"""
PostgreSQL Connection Pool Monitor with deadlock protection.
"""

import threading
from typing import Dict, Optional
from loguru import logger
from datetime import datetime
import time


class TimeoutError(Exception):
    """Timeout exception for pool operations"""
    pass


class PostgresConnectionPoolMonitor:
    """Мониторинг PostgreSQL connection pool с защитой от блокировок"""

    def __init__(self, connection_pool):
        self.connection_pool = connection_pool
        self._stats_lock = threading.Lock()
        self._last_stats = None
        self._last_stats_time = 0
        self._stats_cache_ttl = 5  # Кеш на 5 секунд

    def get_pool_status(self, timeout_seconds: int = 3) -> Dict:
        """
        Получить статус пула с таймаутом

        Args:
            timeout_seconds: Максимальное время ожидания

        Returns:
            Dict с статусом или fallback данные при ошибке
        """
        # Проверить кеш
        current_time = time.time()
        if (self._last_stats and
            current_time - self._last_stats_time < self._stats_cache_ttl):
            logger.debug("Returning cached pool stats")
            return self._last_stats

        try:
            # Попытка получить статус с таймаутом
            stats = self._get_pool_status_with_timeout(timeout_seconds)

            # Обновить кеш
            with self._stats_lock:
                self._last_stats = stats
                self._last_stats_time = current_time

            return stats

        except TimeoutError:
            logger.error(f"get_pool_status timed out after {timeout_seconds}s")
            return self._get_fallback_stats("timeout")

        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return self._get_fallback_stats("error")

    def _get_pool_status_with_timeout(self, timeout_seconds: int) -> Dict:
        """Получить статус с таймаутом через threading"""
        result = {}
        exception = None

        def get_stats():
            nonlocal result, exception
            try:
                result = self.connection_pool.get_stats()
            except Exception as e:
                exception = e

        thread = threading.Thread(target=get_stats, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            logger.warning("get_stats() is still running (deadlock?)")
            raise TimeoutError(f"get_stats blocked for {timeout_seconds}s")

        if exception:
            raise exception

        return result

    def _get_fallback_stats(self, reason: str) -> Dict:
        """Вернуть безопасные fallback данные"""
        fallback = {
            'status': 'degraded',
            'reason': reason,
            'total_connections': 'unknown',
            'active_connections': 'unknown',
            'idle_connections': 'unknown',
            'pool_size': 'unknown',
            'pool_usage': 0,
            'waiting_count': 0,
            'error': f'Stats unavailable ({reason})',
            'cached': True,
            'timestamp': time.time()
        }

        # Если есть кешированные данные, использовать их
        if self._last_stats:
            logger.info("Using stale cached stats due to error")
            return {**self._last_stats, 'status': 'stale', 'reason': reason}

        return fallback

    def get_connection_stats(self) -> Dict:
        """Получить детальную статистику соединений (с защитой)"""
        try:
            return self._get_pool_status_with_timeout(timeout_seconds=2)
        except Exception as e:
            logger.error(f"Error in get_connection_stats: {e}")
            return self._get_fallback_stats("stats_error")

    def get_optimization_suggestions(self) -> Dict:
        """Получить предложения по оптимизации пула соединений"""
        try:
            current_stats = self.get_pool_status(timeout_seconds=3)
            suggestions = []

            # Анализ использования пула
            used = current_stats.get('used', 0)
            available = current_stats.get('available', 0)
            total = used + available

            if total > 0:
                utilization = used / total
                if utilization > 0.8:
                    suggestions.append({
                        'type': 'increase_pool_size',
                        'description': f'High utilization ({utilization:.1%}), consider increasing max connections',
                        'severity': 'medium'
                    })
                elif utilization < 0.1:
                    suggestions.append({
                        'type': 'decrease_pool_size',
                        'description': f'Low utilization ({utilization:.1%}), consider decreasing min connections',
                        'severity': 'low'
                    })

            return {
                'current_utilization': utilization if total > 0 else 0,
                'suggestions': suggestions,
                'generated_at': time.time()
            }
        except Exception as e:
            logger.error(f"Error getting optimization suggestions: {e}")
            return {
                'error': str(e),
                'suggestions': [],
                'generated_at': time.time()
            }
