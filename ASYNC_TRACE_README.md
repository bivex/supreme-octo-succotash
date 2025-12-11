# 🔍 Async-Trace Integration Guide

Этот гид объясняет, как использовать **async-trace** для отладки asyncio задач в вашем сервере.

## 🚀 Быстрый старт

### 1. Запуск с трассировкой

```bash
python main_clean.py --async-trace
```

### 2. Добавление отладки в код

```python
from utils.async_debug import debug_async_trace, debug_before_await, debug_after_await

async def my_handler():
    debug_async_trace("Начало обработки запроса")

    debug_before_await("database query")
    result = await database_call()
    debug_after_await("database query")

    return result
```

### 3. Просмотр демо

```bash
python examples/async_trace_demo.py
```

## 📋 Что показывает async-trace

Когда сервер "висит", async-trace покажет:

```
🔍 Начало обработки запроса
↑ my_handler() at line 25 [handlers.py]
  ↑ route_handler() at line 45 [routes.py]
    ↑ Task-42 created at line 120 [server.py]
      ↑ main_event_loop() at line 88 [main.py]
```

Из этого видно:
- Где была создана зависшая задача (`server.py:120`)
- Полный путь выполнения до текущей точки
- Место, где происходит зависание

## 🛠️ Инструменты отладки

### Основные функции

```python
from utils.async_debug import (
    debug_async_trace,      # Показать полный call stack
    get_async_trace_data,   # Получить структурированные данные
    log_task_info,          # Информация о текущих задачах
    debug_before_await,     # Лог перед async операцией
    debug_after_await,      # Лог после async операции
    debug_database_call,    # Специально для БД вызовов
    debug_http_request,     # Специально для HTTP запросов
    debug_task_creation     # Когда создаются новые задачи
)
```

### Примеры использования

#### Отладка зависаний в handlers

```python
async def create_campaign_handler(res, req):
    debug_http_request("create_campaign")

    # ... validation ...

    debug_before_await("campaign creation")
    campaign = await campaign_service.create(command)
    debug_after_await("campaign creation")

    return campaign
```

#### Поиск медленных операций

```python
async def slow_database_query():
    debug_database_call("complex analytics query")

    # Если эта строка появится в логе, но следующая нет -
    # значит зависание здесь
    debug_async_trace("Before heavy calculation")

    result = await analytics_repository.get_complex_report()

    debug_async_trace("After heavy calculation")
    return result
```

## 🔧 Распространенные сценарии отладки

### 1. Сервер не отвечает на запросы

```python
# Добавьте в начало каждого route handler'а
async def any_route_handler(res, req):
    debug_http_request(f"{req.get_method()} {req.get_url()}")
    # ... остальной код
```

### 2. База данных "висит"

```python
# Перед каждым database call'ом
debug_before_await("user lookup query")
user = await user_repository.find_by_id(user_id)
debug_after_await("user lookup query")
```

### 3. Создание слишком многих задач

```python
# При создании задач
for item in items:
    task = asyncio.create_task(process_item(item))
    debug_task_creation()  # Покажет где создаются задачи
    tasks.append(task)
```

### 4. Таймауты и зависания

```python
async def risky_operation():
    debug_async_trace("Starting risky operation")

    try:
        async with asyncio.timeout(5):  # 5 секунд таймаут
            result = await external_api_call()
        return result
    except asyncio.TimeoutError:
        debug_async_trace("TIMEOUT! Here's the call stack:")
        # async-trace покажет где именно произошел таймаут
        raise
```

## 📊 Анализ результатов

### Чтение call stack'а

```
↑ current_function() at line 25 [file.py]
  ↑ caller_function() at line 45 [file.py]
    ↑ Task-42 created at line 120 [server.py]
```

- `↑` показывает направление стека (внутренний → внешний)
- `line X` - номер строки в файле
- `[file.py]` - файл с кодом
- `Task-XX` - название asyncio задачи

### Поиск проблем

1. **Если стек обрывается на системном вызове** → проблема в блокирующем коде
2. **Если стек показывает бесконечное ожидание** → deadlock или неправильный await
3. **Если много уровней задач** → переизбыток конкурентности
4. **Если стек не меняется** → event loop заблокирован

## 🐛 Отладка реальных багов

### Пример: Route registration зависал

В коде было:
```python
(await container.get_click_routes()).register(app)  # ❌ Нет await для register()
```

async-trace показал:
```
↑ register() coroutine never awaited
  ↑ _register_routes() at line 177 [main.py]
```

Исправлено на:
```python
await (await container.get_click_routes()).register(app)  # ✅ Правильно
```

### Пример: Database call завис

```python
async def handler():
    debug_before_await("slow query")
    result = await db.query("SELECT * FROM huge_table")  # Зависает здесь
    debug_after_await("slow query")  # Никогда не выполняется
```

async-trace показал точную строку зависания.

## 🎯 Лучшие практики

### 1. Добавляйте отладку стратегически

```python
# В route handlers
debug_http_request(endpoint_name)

# Перед database calls
debug_before_await("db operation name")

# При создании задач
debug_task_creation()

# В подозрительных местах
debug_async_trace("checkpoint description")
```

### 2. Используйте timeouts

```python
async with asyncio.timeout(10):
    debug_before_await("potentially slow operation")
    result = await slow_operation()
    debug_after_await("potentially slow operation")
```

### 3. Мониторьте в production

```python
# В критических местах добавьте условную отладку
if settings.debug_mode or random.random() < 0.01:  # 1% запросов
    debug_async_trace("production monitoring")
```

## 🚨 Когда async-trace спасает

- **Сервер завис и не отвечает** → показывает где именно
- **Database queries тормозят** → точная локализация
- **Слишком много задач** → показывает точки создания
- **Deadlocks в async коде** → раскрывает циклические зависимости
- **Memory leaks от задач** → показывает неубранные корутины

## 📚 Дополнительные ресурсы

- [async-trace GitHub](https://github.com/r4u-dev/async-trace)
- [AsyncIO debugging guide](https://docs.python.org/3/library/asyncio-dev.html)
- [Python async best practices](https://docs.python.org/3/library/asyncio.html)

---

**Запомните**: async-trace дает то же понимание async кода, что и обычный traceback для sync кода. Используйте его, когда asyncio "ведет себя странно"! 🎯</contents>
</xai:function_call: write>
<parameter name="file_path">ASYNC_TRACE_README.md
