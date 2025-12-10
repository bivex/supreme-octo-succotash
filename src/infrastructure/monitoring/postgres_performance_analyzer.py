#!/usr/bin/env python3
"""
Advanced PostgreSQL Performance Analyzer - извлекает глубокие метрики из pg_stat_statements
"""

import psycopg2
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Расширенные метрики производительности запроса"""
    query: str
    queryid: str
    calls: int

    # Время выполнения
    total_exec_time: float
    mean_exec_time: float
    min_exec_time: float
    max_exec_time: float
    stddev_exec_time: float

    # Строки и данные (required fields first)
    rows: int
    rows_per_call: float

    # Блоки (кеширование)
    shared_blks_hit: int
    shared_blks_read: int
    shared_blks_cache_ratio: float

    temp_blks_read: int
    temp_blks_written: int

    # Время планирования (если доступно)
    total_plan_time: Optional[float] = None
    mean_plan_time: Optional[float] = None

    # WAL активность
    wal_records: Optional[int] = None
    wal_bytes: Optional[int] = None

    # JIT компиляция (если включена)
    jit_functions: Optional[int] = None
    jit_generation_time: Optional[float] = None

    # Параллельность
    parallel_workers_launched: Optional[int] = None

    # Анализ
    is_read_query: bool = False
    is_write_query: bool = False
    is_dml_query: bool = False
    tables_accessed: List[str] = field(default_factory=list)
    estimated_complexity: str = "unknown"


@dataclass
class SystemPerformanceReport:
    """Общий отчет о производительности системы"""
    total_queries: int
    total_calls: int
    total_exec_time: float

    # Кеширование
    avg_cache_hit_ratio: float
    queries_with_bad_cache: int

    # Ресурсы
    total_temp_bytes: int
    queries_using_temp: int

    # Проблемные паттерны
    sequential_scans: int
    nested_loops_high: int
    high_temp_usage: int
    long_running_queries: int

    # Рекомендации
    optimization_recommendations: List[str]

    generated_at: datetime


class PostgresPerformanceAnalyzer:
    """
    Продвинутый анализатор производительности PostgreSQL
    Извлекает максимум информации из pg_stat_statements
    """

    def __init__(self, connection):
        self.connection = connection

    def get_comprehensive_performance_report(self) -> SystemPerformanceReport:
        """
        Получить полный отчет о производительности системы
        """
        try:
            if hasattr(self.connection, 'getconn'):
                conn = self.connection.getconn()
                try:
                    cursor = conn.cursor()
                    report = self._generate_performance_report(cursor)
                    cursor.close()
                    return report
                finally:
                    self.connection.putconn(conn)
            else:
                with self.connection.cursor() as cursor:
                    return self._generate_performance_report(cursor)
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return self._create_empty_report()

    def _generate_performance_report(self, cursor) -> SystemPerformanceReport:
        """Генерировать полный отчет производительности"""

        # Получить все доступные метрики из pg_stat_statements
        query_metrics = self._extract_all_query_metrics(cursor)

        # Анализировать паттерны
        analysis = self._analyze_performance_patterns(query_metrics)

        # Генерировать рекомендации
        recommendations = self._generate_optimization_recommendations(query_metrics, analysis)

        return SystemPerformanceReport(
            total_queries=len(query_metrics),
            total_calls=sum(m.calls for m in query_metrics),
            total_exec_time=sum(m.total_exec_time for m in query_metrics),
            avg_cache_hit_ratio=sum(m.shared_blks_cache_ratio for m in query_metrics) / len(query_metrics) if query_metrics else 0,
            queries_with_bad_cache=len([m for m in query_metrics if m.shared_blks_cache_ratio < 95]),
            total_temp_bytes=sum(m.temp_blks_written * 8192 for m in query_metrics),  # 8KB blocks
            queries_using_temp=len([m for m in query_metrics if m.temp_blks_written > 0]),
            sequential_scans=analysis.get('sequential_scans', 0),
            nested_loops_high=analysis.get('nested_loops_high', 0),
            high_temp_usage=analysis.get('high_temp_usage', 0),
            long_running_queries=analysis.get('long_running_queries', 0),
            optimization_recommendations=recommendations,
            generated_at=datetime.now()
        )

    def _extract_all_query_metrics(self, cursor) -> List[QueryPerformanceMetrics]:
        """Извлечь все доступные метрики из pg_stat_statements"""

        # Проверить доступные колонки
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'pg_stat_statements'
            ORDER BY column_name
        """)
        available_columns = {row[0] for row in cursor.fetchall()}

        # Построить запрос на основе доступных колонок
        select_columns = [
            'queryid', 'query', 'calls', 'rows',
            'shared_blks_hit', 'shared_blks_read',
            'temp_blks_read', 'temp_blks_written'
        ]

        # Время выполнения
        if 'total_exec_time' in available_columns:
            select_columns.extend(['total_exec_time', 'mean_exec_time', 'min_exec_time', 'max_exec_time', 'stddev_exec_time'])
        elif 'total_time' in available_columns:
            select_columns.extend(['total_time', 'mean_time', 'min_time', 'max_time', 'stddev_time'])

        # Время планирования
        if 'total_plan_time' in available_columns:
            select_columns.extend(['total_plan_time', 'mean_plan_time'])

        # WAL статистика
        if 'wal_records' in available_columns:
            select_columns.extend(['wal_records', 'wal_bytes'])

        # JIT статистика
        if 'jit_functions' in available_columns:
            select_columns.extend(['jit_functions', 'jit_generation_time'])

        # Параллельность
        if 'parallel_workers_launched' in available_columns:
            select_columns.append('parallel_workers_launched')

        # Выполнить запрос
        query = f"""
            SELECT {', '.join(select_columns)}
            FROM pg_stat_statements
            WHERE calls > 5
            AND query NOT LIKE '%pg_stat%'
            AND query NOT LIKE '%information_schema%'
            ORDER BY total_exec_time DESC
            LIMIT 1000
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        metrics = []
        for row in rows:
            metric = self._parse_query_metric_row(row, select_columns)
            if metric:
                metrics.append(metric)

        return metrics

    def _parse_query_metric_row(self, row: tuple, columns: List[str]) -> Optional[QueryPerformanceMetrics]:
        """Распарсить строку с метриками запроса"""
        try:
            data = dict(zip(columns, row))

            # Рассчитать кеш ratio
            shared_hit = data.get('shared_blks_hit', 0)
            shared_read = data.get('shared_blks_read', 0)
            cache_ratio = (shared_hit / (shared_hit + shared_read) * 100) if (shared_hit + shared_read) > 0 else 100.0

            # Анализировать тип запроса
            query_text = data.get('query', '').strip()
            is_read = self._is_read_query(query_text)
            is_write = self._is_write_query(query_text)
            is_dml = self._is_dml_query(query_text)
            tables = self._extract_tables_from_query(query_text)

            return QueryPerformanceMetrics(
                query=query_text,
                queryid=str(data.get('queryid', '')),
                calls=data.get('calls', 0),
                total_exec_time=data.get('total_exec_time', data.get('total_time', 0)),
                mean_exec_time=data.get('mean_exec_time', data.get('mean_time', 0)),
                min_exec_time=data.get('min_exec_time', data.get('min_time', 0)),
                max_exec_time=data.get('max_exec_time', data.get('max_time', 0)),
                stddev_exec_time=data.get('stddev_exec_time', data.get('stddev_time', 0)),
                total_plan_time=data.get('total_plan_time'),
                mean_plan_time=data.get('mean_plan_time'),
                rows=data.get('rows', 0),
                rows_per_call=data.get('rows', 0) / max(data.get('calls', 1), 1),
                shared_blks_hit=shared_hit,
                shared_blks_read=shared_read,
                shared_blks_cache_ratio=cache_ratio,
                temp_blks_read=data.get('temp_blks_read', 0),
                temp_blks_written=data.get('temp_blks_written', 0),
                wal_records=data.get('wal_records'),
                wal_bytes=data.get('wal_bytes'),
                jit_functions=data.get('jit_functions'),
                jit_generation_time=data.get('jit_generation_time'),
                parallel_workers_launched=data.get('parallel_workers_launched'),
                is_read_query=is_read,
                is_write_query=is_write,
                is_dml_query=is_dml,
                tables_accessed=tables,
                estimated_complexity=self._estimate_query_complexity(query_text)
            )
        except Exception as e:
            logger.warning(f"Error parsing query metric row: {e}")
            return None

    def _is_read_query(self, query: str) -> bool:
        """Определить, является ли запрос читающим"""
        query_upper = query.upper().strip()
        return query_upper.startswith('SELECT') and not self._is_write_query(query)

    def _is_write_query(self, query: str) -> bool:
        """Определить, является ли запрос пишущим"""
        query_upper = query.upper().strip()
        return any(query_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'])

    def _is_dml_query(self, query: str) -> bool:
        """Определить, является ли запрос DML"""
        query_upper = query.upper().strip()
        return any(query_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE'])

    def _extract_tables_from_query(self, query: str) -> List[str]:
        """Извлечь имена таблиц из запроса"""
        # Простой regex для поиска FROM table и JOIN table
        tables = []

        # Найти все вхождения FROM и JOIN
        from_pattern = r'\bFROM\s+(\w+)|JOIN\s+(\w+)'
        matches = re.findall(from_pattern, query, re.IGNORECASE)

        for match in matches:
            table = match[0] or match[1]
            if table and table not in tables:
                tables.append(table)

        return tables

    def _estimate_query_complexity(self, query: str) -> str:
        """Оценить сложность запроса"""
        query_upper = query.upper()

        # Сложные паттерны
        if 'WITH' in query_upper or 'UNION' in query_upper:
            return 'high'
        elif 'JOIN' in query_upper or 'GROUP BY' in query_upper or 'ORDER BY' in query_upper:
            return 'medium'
        elif 'WHERE' in query_upper or 'HAVING' in query_upper:
            return 'low'
        else:
            return 'very_low'

    def _analyze_performance_patterns(self, metrics: List[QueryPerformanceMetrics]) -> Dict[str, int]:
        """Анализировать паттерны производительности"""
        analysis = {
            'sequential_scans': 0,
            'nested_loops_high': 0,
            'high_temp_usage': 0,
            'long_running_queries': 0
        }

        for metric in metrics:
            # Запросы с низким кешем (возможные sequential scans)
            if metric.shared_blks_cache_ratio < 80:
                analysis['sequential_scans'] += 1

            # Запросы с высокой temp активностью
            if metric.temp_blks_written > 100:  # > 800KB temp space
                analysis['high_temp_usage'] += 1

            # Долгие запросы
            if metric.mean_exec_time > 1000:  # > 1 second
                analysis['long_running_queries'] += 1

            # Запросы возвращающие много строк
            if metric.rows_per_call > 1000:
                analysis['nested_loops_high'] += 1

        return analysis

    def _generate_optimization_recommendations(
        self,
        metrics: List[QueryPerformanceMetrics],
        analysis: Dict[str, int]
    ) -> List[str]:
        """Генерировать рекомендации по оптимизации"""
        recommendations = []

        # Анализ кеширования
        bad_cache_queries = len([m for m in metrics if m.shared_blks_cache_ratio < 95])
        if bad_cache_queries > 0:
            recommendations.append(
                f"{bad_cache_queries} запросов имеют низкий cache hit ratio (<95%). "
                "Рекомендуется добавить индексы или увеличить shared_buffers."
            )

        # Анализ temp space
        high_temp_queries = analysis.get('high_temp_usage', 0)
        if high_temp_queries > 0:
            recommendations.append(
                f"{high_temp_queries} запросов используют большое количество temp space. "
                "Проверьте work_mem или оптимизируйте запросы с сортировками."
            )

        # Анализ долгих запросов
        long_queries = analysis.get('long_running_queries', 0)
        if long_queries > 0:
            recommendations.append(
                f"{long_queries} запросов выполняются более 1 секунды. "
                "Рекомендуется оптимизация запросов или добавление индексов."
            )

        # Анализ COUNT(*) запросов
        count_queries = len([m for m in metrics if 'COUNT(*)' in m.query.upper()])
        if count_queries > len(metrics) * 0.1:  # > 10% запросов - COUNT(*)
            recommendations.append(
                f"Высокая частота COUNT(*) запросов ({count_queries}). "
                "Рассмотрите кеширование счетчиков или использование approximations."
            )

        # Анализ простых запросов с низкой эффективностью
        simple_slow_queries = [
            m for m in metrics
            if m.estimated_complexity == 'very_low' and m.mean_exec_time > 10
        ]
        if len(simple_slow_queries) > 5:
            recommendations.append(
                f"{len(simple_slow_queries)} простых запросов выполняются медленно. "
                "Проверьте состояние индексов или параметры PostgreSQL."
            )

        return recommendations if recommendations else ["Система работает оптимально - нет критичных проблем производительности."]

    def _create_empty_report(self) -> SystemPerformanceReport:
        """Создать пустой отчет при ошибке"""
        return SystemPerformanceReport(
            total_queries=0,
            total_calls=0,
            total_exec_time=0.0,
            avg_cache_hit_ratio=0.0,
            queries_with_bad_cache=0,
            total_temp_bytes=0,
            queries_using_temp=0,
            sequential_scans=0,
            nested_loops_high=0,
            high_temp_usage=0,
            long_running_queries=0,
            optimization_recommendations=["Невозможно получить метрики производительности"],
            generated_at=datetime.now()
        )
