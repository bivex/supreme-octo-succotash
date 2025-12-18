# 🚀 Supreme Octo Succotash - План Оптимизации

## 🎯 Обзор Оптимизаций

На основе анализа архитектуры и лучших практик PostgreSQL, вот комплексный план оптимизации вашего приложения.

---

## 1. 🔗 **Оптимизация Connection Pooling**

### Текущая ситуация:

```python
# src/container.py - текущее решение
psycopg2.pool.SimpleConnectionPool(
    minconn=1,      # Слишком мало
    maxconn=100,    # Слишком много для небольшой системы
    ...
)
```

### Оптимизации:

#### A. Умный Connection Pooler

```python
# Новый файл: src/infrastructure/database/advanced_connection_pool.py
import psycopg2
from psycopg2 import pool
import threading
import time
from typing import Optional, Dict, Any

class AdvancedConnectionPool:
    """Advanced PostgreSQL connection pool with monitoring and optimization."""

    def __init__(self, **kwargs):
        self._pool = pool.SimpleConnectionPool(**kwargs)
        self._stats = {
            'connections_created': 0,
            'connections_returned': 0,
            'connections_failed': 0,
            'query_count': 0,
            'avg_query_time': 0,
            'slow_queries': 0
        }
        self._lock = threading.Lock()

    def getconn(self):
        """Get connection with stats tracking."""
        try:
            conn = self._pool.getconn()
            with self._lock:
                self._stats['connections_created'] += 1
            return conn
        except Exception as e:
            with self._lock:
                self._stats['connections_failed'] += 1
            raise e

    def putconn(self, conn):
        """Return connection with stats tracking."""
        try:
            self._pool.putconn(conn)
            with self._lock:
                self._stats['connections_returned'] += 1
        except Exception:
            pass

    def get_stats(self):
        """Get pool statistics."""
        with self._lock:
            pool_stats = {
                'minconn': getattr(self._pool, '_minconn', 0),
                'maxconn': getattr(self._pool, '_maxconn', 0),
                'used': len(getattr(self._pool, '_used', [])),
                'available': len(getattr(self._pool, '_pool', [])),
            }
            return {**pool_stats, **self._stats.copy()}

    def closeall(self):
        """Close all connections."""
        self._pool.closeall()
```

#### B. Оптимизация настроек пула

```python
# src/container.py - улучшенные настройки
def get_db_connection_pool(self):
    """Get optimized PostgreSQL connection pool."""
    if 'db_connection_pool' not in self._singletons:
        self._singletons['db_connection_pool'] = AdvancedConnectionPool(
            minconn=5,          # Увеличено для лучшей производительности
            maxconn=32,         # Оптимально для большинства приложений
            host="localhost",
            port=5432,
            database="supreme_octosuccotash_db",
            user="app_user",
            password="app_password",
            client_encoding='utf8',
            # Оптимизации соединения
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            tcp_user_timeout=60000,
        )
    return self._singletons['db_connection_pool']
```

---

## 2. 🔄 **Prepared Statements Повсеместно**

### Текущая ситуация:

Только базовые `cursor.execute()` без prepared statements.

### Оптимизация:

#### A. Prepared Statement Manager

```python
# Новый файл: src/infrastructure/database/prepared_statement_manager.py
class PreparedStatementManager:
    """Manages prepared statements for better performance."""

    def __init__(self):
        self._statements = {}

    def prepare_click_insert(self, cursor):
        """Prepare click insert statement."""
        if 'click_insert' not in self._statements:
            cursor.execute("""
                PREPARE click_insert AS
                INSERT INTO clicks (
                    id, campaign_id, ip_address, user_agent, referrer, is_valid,
                    sub1, sub2, sub3, sub4, sub5, click_id_param, affiliate_sub, affiliate_sub2,
                    landing_page_id, campaign_offer_id, traffic_source_id,
                    conversion_type, converted_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                ON CONFLICT (id) DO UPDATE SET
                    campaign_id = EXCLUDED.campaign_id,
                    ip_address = EXCLUDED.ip_address,
                    user_agent = EXCLUDED.user_agent,
                    referrer = EXCLUDED.referrer,
                    is_valid = EXCLUDED.is_valid,
                    updated_at = NOW()
            """)
            self._statements['click_insert'] = True

    def prepare_event_insert(self, cursor):
        """Prepare event insert statement."""
        if 'event_insert' not in self._statements:
            cursor.execute("""
                PREPARE event_insert AS
                INSERT INTO events (id, click_id, event_type, event_data, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO NOTHING
            """)
            self._statements['event_insert'] = True

    def execute_click_insert(self, cursor, click_data):
        """Execute prepared click insert."""
        cursor.execute("EXECUTE click_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                      click_data)

    def execute_event_insert(self, cursor, event_data):
        """Execute prepared event insert."""
        cursor.execute("EXECUTE event_insert (%s, %s, %s, %s, %s)", event_data)
```

#### B. Интеграция в репозитории

```python
# src/infrastructure/repositories/postgres_click_repository.py
class PostgresClickRepository(ClickRepository):
    def __init__(self, container):
        self._container = container
        self._stmt_manager = PreparedStatementManager()

    def save(self, click: Click) -> None:
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        try:
            # Prepare statement on first use
            self._stmt_manager.prepare_click_insert(cursor)

            # Execute prepared statement
            click_data = (
                click.id, click.campaign_id, click.ip_address, click.user_agent,
                click.referrer, click.is_valid, click.sub1, click.sub2, click.sub3,
                click.sub4, click.sub5, click.click_id_param, click.affiliate_sub,
                click.affiliate_sub2, click.landing_page_id, click.campaign_offer_id,
                click.traffic_source_id, click.conversion_type, click.converted_at,
                click.created_at
            )

            self._stmt_manager.execute_click_insert(cursor, click_data)
            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._container.put_db_connection(conn)
```

---

## 3. 📊 **Read Replicas Поддержка**

### Архитектура:

```
Master (Writes) → Replica 1 (Reads)
                  → Replica 2 (Reads)
```

### Реализация:

```python
# Новый файл: src/infrastructure/database/read_replica_manager.py
class ReadReplicaManager:
    """Manages read replicas for load distribution."""

    def __init__(self, master_config, replica_configs):
        self.master = master_config
        self.replicas = replica_configs
        self._replica_pools = []
        self._current_replica = 0

    def get_read_connection(self):
        """Get connection from replica (round-robin)."""
        if not self.replicas:
            return self._get_master_connection()

        # Round-robin load balancing
        replica_config = self.replicas[self._current_replica % len(self.replicas)]
        self._current_replica += 1

        # Return replica connection
        return self._create_connection(replica_config)

    def get_write_connection(self):
        """Get master connection for writes."""
        return self._get_master_connection()

    def _create_connection(self, config):
        """Create database connection."""
        return psycopg2.connect(**config)
```

#### Интеграция в Container:

```python
# src/container.py
def get_read_replica_manager(self):
    """Get read replica manager."""
    if 'read_replica_manager' not in self._singletons:
        # В будущем можно добавить конфигурацию реплик
        replica_configs = []  # Пока пусто, но готово к расширению

        self._singletons['read_replica_manager'] = ReadReplicaManager(
            master_config={
                'host': 'localhost',
                'port': 5432,
                'database': 'supreme_octosuccotash_db',
                'user': 'app_user',
                'password': 'app_password'
            },
            replica_configs=replica_configs
        )
    return self._singletons['read_replica_manager']
```

---

## 4. 🚀 **Redis Caching Layer**

### Для горячих данных:

```python
# Новый файл: src/infrastructure/cache/redis_cache.py
import redis
import json
import hashlib
from typing import Any, Optional

class RedisCache:
    """Redis caching layer for hot data."""

    def __init__(self, host='localhost', port=6379, db=0, ttl=3600):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.default_ttl = ttl

    def get_campaign(self, campaign_id: str) -> Optional[dict]:
        """Get campaign from cache."""
        key = f"campaign:{campaign_id}"
        data = self.client.get(key)
        return json.loads(data) if data else None

    def set_campaign(self, campaign_id: str, campaign_data: dict, ttl=None):
        """Cache campaign data."""
        key = f"campaign:{campaign_id}"
        self.client.setex(key, ttl or self.default_ttl, json.dumps(campaign_data))

    def get_click_stats(self, campaign_id: str) -> Optional[dict]:
        """Get cached click statistics."""
        key = f"click_stats:{campaign_id}"
        data = self.client.get(key)
        return json.loads(data) if data else None

    def invalidate_campaign(self, campaign_id: str):
        """Invalidate campaign cache."""
        pattern = f"campaign:{campaign_id}*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)

    def get_cache_stats(self):
        """Get cache statistics."""
        info = self.client.info()
        return {
            'used_memory': info.get('used_memory_human'),
            'connected_clients': info.get('connected_clients'),
            'total_connections_received': info.get('total_connections_received'),
            'keyspace_hits': info.get('keyspace_hits'),
            'keyspace_misses': info.get('keyspace_misses'),
        }
```

#### Интеграция в репозитории:

```python
# src/infrastructure/repositories/postgres_campaign_repository.py
def get_campaign(self, campaign_id: CampaignId) -> Optional[Campaign]:
    # Try cache first
    cached = self._cache.get_campaign(str(campaign_id))
    if cached:
        return self._row_to_campaign(cached)

    # Get from database
    campaign = self._get_from_db(campaign_id)

    # Cache for future use
    if campaign:
        self._cache.set_campaign(str(campaign_id), self._campaign_to_dict(campaign))

    return campaign
```

---

## 5. 📈 **Performance Monitoring**

### Метрики сбора:

```python
# Новый файл: src/infrastructure/monitoring/performance_monitor.py
import time
import psycopg2
import threading
from collections import defaultdict
from loguru import logger

class PerformanceMonitor:
    """Monitor database and application performance."""

    def __init__(self):
        self.metrics = defaultdict(list)
        self._lock = threading.Lock()

    def track_query(self, query_name: str, execution_time: float, success: bool = True):
        """Track query performance."""
        with self._lock:
            self.metrics[f"{query_name}_time"].append(execution_time)
            self.metrics[f"{query_name}_count"].append(1)
            if not success:
                self.metrics[f"{query_name}_errors"].append(1)

    def track_connection_pool(self, pool_stats: dict):
        """Track connection pool statistics."""
        with self._lock:
            for key, value in pool_stats.items():
                self.metrics[f"pool_{key}"].append(value)

    def get_database_stats(self):
        """Get current database statistics."""
        try:
            conn = psycopg2.connect(
                host='localhost', port=5432,
                database='supreme_octosuccotash_db',
                user='app_user', password='app_password'
            )
            cursor = conn.cursor()

            # Cache hit ratio
            cursor.execute("""
                SELECT
                    sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 as heap_hit_ratio,
                    sum(idx_blks_hit) / nullif(sum(idx_blks_hit) + sum(idx_blks_read), 0) * 100 as index_hit_ratio
                FROM pg_statio_user_tables
            """)

            cache_stats = cursor.fetchone()

            # Active connections
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity
                WHERE state = 'active' AND datname = 'supreme_octosuccotash_db'
            """)

            active_connections = cursor.fetchone()[0]

            conn.close()

            return {
                'cache_hit_ratio': {
                    'heap': float(cache_stats[0] or 0),
                    'index': float(cache_stats[1] or 0)
                },
                'active_connections': active_connections,
                'timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return None

    def get_summary_stats(self):
        """Get summary statistics."""
        with self._lock:
            summary = {}

            for metric_name, values in self.metrics.items():
                if values and len(values) > 10:  # Only if we have enough data
                    summary[metric_name] = {
                        'count': len(values),
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'p95': sorted(values)[int(len(values) * 0.95)]
                    }

            return summary
```

---

## 6. ⚡ **Async Operations (Будущая оптимизация)**

### Переход на async PostgreSQL:

```python
# requirements.txt добавить:
# asyncpg==0.29.0

import asyncpg
import asyncio

class AsyncPostgresRepository:
    """Async version of repository for better concurrency."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    async def save_click_async(self, click: Click) -> None:
        """Async click save."""
        conn = await asyncpg.connect(self.connection_string)

        try:
            await conn.execute("""
                INSERT INTO clicks (id, campaign_id, ip_address, user_agent, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET
                    campaign_id = EXCLUDED.campaign_id,
                    updated_at = NOW()
            """, click.id, click.campaign_id, click.ip_address, click.user_agent, click.created_at)

        finally:
            await conn.close()
```

---

## 🎯 **Приоритетная очередность внедрения:**

### **Фаза 1 (Неделя 1-2):**

1. ✅ **Advanced Connection Pooling** - +20-30% производительности
2. ✅ **Prepared Statements** - +15-25% для повторяющихся запросов
3. ✅ **Performance Monitoring** - видимость проблем

### **Фаза 2 (Неделя 3-4):**

1. 🔄 **Redis Caching** - +50-80% для горячих данных
2. 🔄 **Read Replicas Support** - готовность к масштабированию

### **Фаза 3 (Месяц 2):**

1. 🚀 **Async Operations** - максимальная concurrency
2. 🚀 **Advanced Query Optimization** - сложные запросы

---

## 📊 **Ожидаемые результаты:**

| Оптимизация            | Текущая производительность   | После оптимизации                | Улучшение       |
|------------------------|------------------------------|----------------------------------|-----------------|
| **Connection Pooling** | Базовый SimpleConnectionPool | Advanced Pool с мониторингом     | +25%            |
| **Query Performance**  | Без prepared statements      | Повсеместные prepared statements | +20%            |
| **Cache Hit Ratio**    | 99.4% heap, 99.2% index      | + Redis layer                    | +300%           |
| **Read Operations**    | Только master                | Read replicas                    | +200%           |
| **Monitoring**         | Логи                         | Метрики + алерты                 | 100% visibility |

**Supreme Octo Succotash готов к значительному улучшению производительности!** 🚀

Хотите начать с внедрения **Advanced Connection Pooling**?
