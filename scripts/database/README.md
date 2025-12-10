# Database Scripts

Скрипты для работы с PostgreSQL базой данных: настройка, мониторинг, индексы, разрешения.

## Основные скрипты

- `setup_postgres_monitoring.py` - Настройка мониторинга PostgreSQL
- `enable_pg_stat_statements.py` - Включение сбора статистики запросов
- `create_indexes_simple.py` - Создание индексов производительности
- `check_postgres_config.py` - Проверка конфигурации PostgreSQL
- `test_postgres_monitoring.py` - Тестирование мониторинга

## Быстрый старт

```bash
# Настройка мониторинга
python setup_postgres_monitoring.py

# Создание индексов
python create_indexes_simple.py

# Тестирование
python test_postgres_monitoring.py
```

