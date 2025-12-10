# 🚀 PostgreSQL Auto Upholder

**Автоматическая система оптимизации производительности PostgreSQL**

## 🎯 Что делает Upholder?

Upholder - это интеллектуальная система, которая автоматически анализирует и оптимизирует производительность вашей PostgreSQL базы данных. Она следует лучшим практикам из [PostgreSQL Best Practices Guide](POSTGRESQL_BEST_PRACTICES_GUIDE.md).

## ✨ Возможности

### 🔍 **Автоматический анализ запросов**
- Обнаружение медленных запросов через `pg_stat_statements`
- Анализ EXPLAIN ANALYZE для выявления Sequential Scan
- Рекомендации по оптимизации индексов

### 📊 **Мониторинг кеша**
- Отслеживание cache hit ratio (heap & index)
- Алерты при падении производительности ниже 95%
- Рекомендации по увеличению `shared_buffers`

### 🏗️ **Аудит индексов**
- Поиск недостающих индексов на WHERE/JOIN колонках
- Обнаружение неиспользуемых индексов
- Идентификация bloated индексов

### 🚀 **Оптимизация bulk операций**
- Автоматическая замена INSERT на COPY для больших объемов данных
- Интеллектуальный выбор метода загрузки (>1000 записей → COPY)

### ⚡ **Prepared Statements**
- Автоматическое обнаружение и оптимизация повторяющихся запросов
- Кеширование prepared statements для лучшей производительности

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install -r requirements-dev.txt
```

### Встроенная интеграция (рекомендуется)
PostgreSQL Auto Upholder **автоматически запускается** вместе с приложением!

```bash
# Просто запустите приложение - upholder включится автоматически
python src/main.py
# или
./restarter.bat
```

### Ручное управление

#### Запуск разового аудита
```bash
python scripts/performance/postgres_upholder_runner.py once
```

#### Запуск дашборда производительности
```bash
python scripts/performance/postgres_upholder_runner.py dashboard
```

#### Непрерывный мониторинг (1 час)
```bash
python scripts/performance/postgres_upholder_runner.py continuous --duration 60
```

### API эндпоинты (после запуска приложения)

#### Статус системы оптимизации
```bash
curl http://localhost:5000/v1/system/upholder/status
```

#### Ручный запуск аудита
```bash
curl -X POST http://localhost:5000/v1/system/upholder/audit
```

#### Конфигурация системы
```bash
curl http://localhost:5000/v1/system/upholder/config
```

#### Проверка здоровья (включая БД)
```bash
curl http://localhost:5000/health
```

### Тестирование интеграции
```bash
python scripts/test_upholder_integration.py
```

## 📋 Детальные возможности

### 1. Query Analysis (`PostgresQueryAnalyzer`)
```python
from infrastructure.monitoring.postgres_query_analyzer import PostgresQueryAnalyzer

analyzer = PostgresQueryAnalyzer(connection)
result = analyzer.analyze_query("SELECT * FROM campaigns WHERE status = 'active'")
print(f"Query cost: {result.total_cost}, Has seq scan: {result.has_sequential_scan}")
```

### 2. Index Audit (`PostgresIndexAuditor`)
```python
from infrastructure.monitoring.postgres_index_auditor import PostgresIndexAuditor

auditor = PostgresIndexAuditor(connection)
results = auditor.audit_all_tables()
for table, audit in results.items():
    print(f"{table}: {len(audit.missing_indexes)} missing, {len(audit.unused_indexes)} unused indexes")
```

### 3. Cache Monitoring (`PostgresCacheMonitor`)
```python
from infrastructure.monitoring.postgres_cache_monitor import create_default_cache_monitor

monitor = create_default_cache_monitor(connection)
monitor.start_monitoring(interval_seconds=300)  # Every 5 minutes
metrics = monitor.get_current_metrics()
print(f"Cache hit ratio: {metrics.heap_hit_ratio:.1f}%")
```

### 4. Query Optimization (`PostgresQueryOptimizer`)
```python
from infrastructure.monitoring.postgres_query_optimizer import PostgresQueryOptimizer

optimizer = PostgresQueryOptimizer(connection)
issues = optimizer.analyze_slow_queries(min_avg_time=100)
dashboard = optimizer.get_performance_dashboard()
```

### 5. Bulk Loading (`PostgresBulkLoader`)
```python
from infrastructure.repositories.postgres_bulk_loader import PostgresBulkLoader

loader = PostgresBulkLoader(connection)
result = loader.bulk_insert('clicks', click_data)
print(f"Loaded {result.records_loaded} records in {result.execution_time:.2f}s using {result.method_used}")
```

## ⚙️ Конфигурация

### Основные настройки
```python
from infrastructure.upholder.postgres_auto_upholder import UpholderConfig, PostgresAutoUpholder

config = UpholderConfig(
    query_analysis_interval=60,      # Анализ запросов каждые 60 минут
    index_audit_interval=240,        # Аудит индексов каждые 4 часа
    cache_monitoring_interval=30,    # Мониторинг кеша каждые 30 минут
    slow_query_threshold_ms=100,     # Порог медленных запросов
    auto_apply_safe_optimizations=False,  # Автоприменение безопасных оптимизаций
    dry_run_mode=True               # Режим сухого запуска
)

upholder = PostgresAutoUpholder(connection, config)
```

### Продвинутые настройки
```python
# Кастомные алерты
def custom_alert_handler(alert_type, message):
    print(f"🚨 {alert_type}: {message}")
    # Отправить в Slack, email и т.д.

upholder.add_alert_handler(custom_alert_handler)

# Кастомные отчеты
def custom_report_handler(report):
    with open(f'report_{report.timestamp.strftime("%Y%m%d_%H%M")}.json', 'w') as f:
        json.dump(report.__dict__, f, default=str)

upholder.add_report_handler(custom_report_handler)
```

## 📊 Мониторинг и алерты

### Что вы увидите в логах при запуске
```
🔧 Initializing PostgreSQL Auto Upholder...
✅ PostgreSQL Auto Upholder started successfully
📊 PostgreSQL upholder endpoints registered: /v1/system/upholder/*

🚨 PostgreSQL Performance Alert: Heap cache hit ratio is 87.3% (threshold: 95.0%)
🚨 PostgreSQL Performance Alert: Index cache hit ratio is 72.1% (threshold: 90.0%)
```

### Типы алертов
- `low_heap_hit_ratio` - Низкий cache hit ratio для heap
- `low_index_hit_ratio` - Низкий cache hit ratio для индексов
- `high_buffer_usage` - Высокое использование shared buffers
- `missing_index` - Отсутствующие индексы
- `sequential_scan` - Sequential scan на больших таблицах

### Пример алерта с рекомендациями
```
🚨 performance_alert: Heap cache hit ratio is 87.3% (threshold: 95.0%)
Recommendations:
- Consider increasing shared_buffers
- Review frequently accessed tables for proper indexing
- Run ANALYZE on tables with stale statistics
```

## 🔧 Интеграция в приложение

### Добавление в существующие репозитории
```python
from infrastructure.repositories.postgres_prepared_statements import AutoPreparedRepositoryMixin

class MyRepository(AutoPreparedRepositoryMixin):
    def __init__(self, container):
        super().__init__(container)
        # Автоматическая оптимизация prepared statements

    def find_campaigns_by_status(self, status: str):
        # Автоматически использует prepared statements
        return self.execute_optimized(
            "SELECT * FROM campaigns WHERE status = %s",
            (status,)
        )
```

### Интеграция в приложение (уже реализована!)
PostgreSQL Auto Upholder **полностью интегрирован** в основное приложение!

#### Что происходит при запуске:
1. **Автоматическая инициализация** в `src/main.py`
2. **Фоновый мониторинг** запускается автоматически
3. **API эндпоинты** регистрируются для управления
4. **Алерты** интегрируются в систему логирования

#### Архитектура интеграции:
```
main.py
├── create_app()
    ├── _initialize_postgres_upholder()  # ✅ Авто-запуск
    └── _add_upholder_endpoints()         # ✅ API endpoints

container.py
└── get_postgres_upholder()              # ✅ Dependency injection

Результат: Полная автоматизация без ручных действий!
```

### Ручная интеграция (для других проектов)
```python
# В container.py
def get_postgres_upholder(self):
    if 'upholder' not in self._singletons:
        from infrastructure.upholder.postgres_auto_upholder import create_default_upholder
        connection = self.get_db_connection()
        self._singletons['upholder'] = create_default_upholder(connection)
    return self._singletons['upholder']

# В main.py
upholder = container.get_postgres_upholder()
upholder.start()  # Запуск фонового мониторинга
```

## 📈 Производительность

### Типичные улучшения
- **Cache hit ratio**: 85% → 98% (увеличение shared_buffers)
- **Query performance**: 500ms → 50ms (добавление индексов)
- **Bulk loading**: 10x быстрее (COPY vs INSERT)
- **Memory usage**: Снижение на 30% (оптимизация индексов)

### Метрики мониторинга
```python
dashboard = upholder.get_performance_dashboard()
print(json.dumps(dashboard, indent=2))
```

## 🛠️ Troubleshooting

### Проблема: Нет данных в pg_stat_statements
```sql
-- Включить расширение
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Проверить настройки в postgresql.conf
-- shared_preload_libraries = 'pg_stat_statements'
-- pg_stat_statements.track = all
-- pg_stat_statements.max = 10000
```

### Проблема: Медленный анализ
```python
# Уменьшить интервалы анализа
config = UpholderConfig(
    query_analysis_interval=120,  # Каждые 2 часа вместо 1
    index_audit_interval=480      # Каждые 8 часов вместо 4
)
```

### Проблема: Слишком много алертов
```python
# Настроить cooldown и thresholds
config = UpholderConfig(
    alert_cooldown_minutes=120,      # Алерт раз в 2 часа
    cache_hit_ratio_min=0.90         # Threshold 90% вместо 95%
)
```

## 🚦 Безопасность

- **Dry-run mode**: По умолчанию включен - изменения не применяются
- **Safe optimizations**: Только безопасные оптимизации применяются автоматически
- **Audit logging**: Все действия логируются
- **Rollback support**: Для примененных изменений есть rollback команды

## 📚 API Reference

### PostgresAutoUpholder
- `start()` - Запуск фонового мониторинга
- `stop()` - Остановка мониторинга
- `run_full_audit()` - Запуск полного цикла аудита
- `get_status()` - Получение статуса системы
- `get_performance_dashboard()` - Получение дашборда производительности

### Компоненты
- `PostgresQueryAnalyzer` - Анализ запросов
- `PostgresIndexAuditor` - Аудит индексов
- `PostgresCacheMonitor` - Мониторинг кеша
- `PostgresQueryOptimizer` - Оптимизация запросов
- `PostgresBulkLoader` - Bulk загрузка данных

## 🎯 Следующие шаги

1. **Тестирование**: Запустите на staging окружении
2. **Мониторинг**: Настройте алерты и дашборды
3. **Оптимизация**: Примените рекомендации системы
4. **Масштабирование**: Интегрируйте в CI/CD пайплайн

---

**Upholder поможет вам поддерживать PostgreSQL в оптимальном состоянии автоматически!** 🚀
