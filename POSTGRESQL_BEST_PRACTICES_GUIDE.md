# PostgreSQL Best Practices Guide

## 🎯 Правильное использование PostgreSQL

PostgreSQL - это высокопроизводительная база данных, но она требует правильного использования. Не считайте её "медленной" - она просто требует корректного подхода.

## 📋 Ключевые Принципы

### 1. **Prepared Statements для долгоживущих сервисов**
```python
# Правильно: подготовка один раз, исполнение многократно
cursor.execute("PREPARE get_user AS SELECT * FROM users WHERE id = $1")
for user_id in user_ids:
    cursor.execute("EXECUTE get_user (%s)", (user_id,))
```

**Почему это важно:**
- Парсер и планировщик работают только один раз
- Снижается CPU overhead
- Лучше для connection pooling

### 2. **EXPLAIN ANALYZE вместо догадок**
```sql
EXPLAIN ANALYZE
SELECT * FROM campaigns WHERE status = 'active';
```

**Что проверять:**
- Sequential Scan (плохо для больших таблиц)
- Index Scan (хорошо)
- Planning time vs Execution time
- Buffer hits ratio

### 3. **Правильное индексирование**

#### Индексируйте WHERE, JOIN, ORDER BY колонки:
```sql
-- WHERE условия
CREATE INDEX ON campaigns (status);

-- JOIN колонки
CREATE INDEX ON events (click_id);
CREATE INDEX ON clicks (campaign_id);

-- ORDER BY колонки
CREATE INDEX ON campaigns (created_at DESC);
```

#### Понимайте trade-offs:
```sql
-- Индексы ускоряют ЧТЕНИЕ
SELECT * FROM campaigns WHERE status = 'active'; -- Быстрее с индексом

-- Но замедляют ЗАПИСЬ
INSERT INTO campaigns VALUES (...); -- Медленнее с индексом
```

### 4. **Партиционирование больших таблиц**

```sql
-- Партиционирование по времени
CREATE TABLE events (
    id TEXT,
    click_id TEXT,
    event_type TEXT,
    created_at TIMESTAMP NOT NULL
) PARTITION BY RANGE (created_at);

-- Создание партиций
CREATE TABLE events_2024_01 PARTITION OF events
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE events_2024_02 PARTITION OF events
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

**Преимущества:**
- Операции над меньшими кусками данных
- Лучшая производительность обслуживания
- Легче управлять retention

### 5. **COPY для bulk loading**

```sql
-- Самый быстрый способ загрузки данных
COPY clicks FROM '/path/to/data.csv' WITH CSV HEADER;

-- Или из Python:
cursor.copy_expert("COPY clicks FROM STDIN WITH CSV", csv_file)
```

**Сравнение производительности:**
- COPY: 10,000+ строк/сек
- Prepared statements: 1,000+ строк/сек
- Individual INSERTs: 100+ строк/сек

### 6. **Read Replicas для масштабирования чтения**

```
Master (Writes) → Replica 1 (Reads)
                  → Replica 2 (Reads)
                  → Replica 3 (Reads)
```

**Использование:**
```sql
-- Приложение автоматически маршрутизирует
# SELECT queries → read replicas
# INSERT/UPDATE/DELETE → master
```

### 7. **Connection Pooling**

```python
# Используйте connection pooler
import psycopg2.pool

pool = psycopg2.pool.SimpleConnectionPool(
    minconn=5,
    maxconn=20,
    host='localhost',
    database='mydb'
)

conn = pool.getconn()
# ... use connection ...
pool.putconn(conn)
```

**Рекомендуемые poolers:**
- **PgBouncer**: Легковесный, для простых случаев
- **Pgpool-II**: Продвинутый, с load balancing
- **Приложение**: SQLAlchemy, HikariCP

## 🛠️ Практические Примеры

### Оптимизация медленного запроса:

**Шаг 1: Анализ**
```sql
EXPLAIN ANALYZE
SELECT c.name, COUNT(o.id)
FROM campaigns c
LEFT JOIN orders o ON c.id = o.campaign_id
WHERE c.status = 'active'
GROUP BY c.id, c.name;
```

**Шаг 2: Проверка индексов**
```sql
SELECT * FROM pg_stat_user_indexes
WHERE relname IN ('campaigns', 'orders');
```

**Шаг 3: Добавление недостающих индексов**
```sql
CREATE INDEX CONCURRENTLY ON campaigns (status);
CREATE INDEX CONCURRENTLY ON orders (campaign_id);
```

**Шаг 4: Повторный анализ**
```sql
EXPLAIN ANALYZE ... -- Сравнить улучшение
```

### Bulk Data Loading:

```python
# 1. Подготовка данных
csv_data = generate_csv_data()

# 2. Bulk загрузка
with psycopg2.connect(**conn_params) as conn:
    with conn.cursor() as cursor:
        cursor.copy_expert("""
            COPY my_table FROM STDIN WITH CSV HEADER
        """, csv_data)
        conn.commit()
```

## 📊 Мониторинг Производительности

### Ключевые метрики:
```sql
-- Cache hit ratio
SELECT
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as heap_ratio,
  sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read)) as index_ratio
FROM pg_statio_user_tables;

-- Активные запросы
SELECT pid, query, state, duration
FROM pg_stat_activity
WHERE state = 'active';

-- Размер таблиц и индексов
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Регулярные аудиты:
- **Еженедельно**: Проверка cache hit ratio
- **Ежемесячно**: Анализ медленных запросов
- **Ежеквартально**: Полный аудит индексов

## 🚀 Продвинутые Техники

### Partial Indexes:
```sql
-- Индекс только для активных записей
CREATE INDEX ON campaigns (created_at)
WHERE status = 'active';
```

### Expression Indexes:
```sql
-- Индекс на выражение
CREATE INDEX ON events (lower(event_type));
```

### Covering Indexes:
```sql
-- Индекс покрывает весь запрос
CREATE INDEX ON campaigns (status, name, created_at);
```

## 🔧 Инструменты

### Для разработки:
- **pg_stat_statements**: Анализ запросов
- **auto_explain**: Автоматический EXPLAIN
- **pg_buffercache**: Анализ кеша

### Для production:
- **PgHero**: Web-интерфейс для мониторинга
- **pgBadger**: Анализ логов
- **pg_stat_kcache**: Статистика системных ресурсов

## 🎯 Заключение

**PostgreSQL - это мощный инструмент, но он требует понимания:**

1. **Используйте правильные инструменты** для каждой задачи
2. **Мониторьте производительность** регулярно
3. **Оптимизируйте iteratively** - измеряйте, меняйте, измеряйте снова
4. **Балансируйте** между скоростью чтения и записи
5. **Масштабируйте** правильно - read replicas, partitioning, connection pooling

**Следуйте этим практикам, и PostgreSQL покажет outstanding производительность!** 🚀
