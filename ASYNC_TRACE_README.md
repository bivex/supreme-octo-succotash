# 🔍 Async-Trace Integration Guide

Этот гид объясняет, как использовать **async-trace** для отладки asyncio задач в вашем сервере с **автоматическим сохранением трейсов в файлы** для последующего анализа.

## ⚡ Быстрый старт с автоматическим сохранением

Сервер **автоматически сохраняет трейсы** в ключевых точках жизненного цикла:

```bash
python main_clean.py --async-trace
```

**Что сохраняется автоматически:**
- 🚀 **Server startup** → `debug_snapshot_server_startup_*.html`
- 🛑 **Signal shutdown** → `debug_snapshot_signal_shutdown_*.html`
- 💥 **Unhandled exceptions** → `debug_snapshot_unhandled_exception_*.html`
- ❌ **Route handler errors** → `debug_snapshot_create_offer_error_*.html`
- 🛑 **Graceful shutdown** → `debug_snapshot_server_shutdown_*.html`

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

## 📂 Где смотреть сохраненные трейсы

Все трейсы сохраняются в папку **`traces/`** относительно корня проекта:

```
traces/
├── debug_snapshot_server_startup_074121.html      # Запуск сервера
├── debug_snapshot_signal_shutdown_sig2_074151.html # Остановка по сигналу
├── debug_snapshot_unhandled_exception_074200.html  # Необработанные ошибки
└── debug_snapshot_create_offer_error_074300.html   # Ошибки в обработчиках
```

**HTML файлы** можно открывать в браузере для просмотра красивой визуализации call stack'а.

**JSON файлы** подходят для программного анализа и интеграции с системами мониторинга.

## 💾 Сохранение трейсов в файлы

### Автоматическое сохранение (уже настроено)

Сервер автоматически сохраняет трейсы при:

#### 🚀 **Запуск сервера**
```python
# main_clean.py
startup_trace = save_debug_snapshot("server_startup")
logger.info(f"📸 Server startup trace saved: {startup_trace}")
```

#### 🛑 **Обработка сигналов**
```python
# main_clean.py - signal_handler
signal_trace = save_debug_snapshot(f"signal_shutdown_sig{signum}")
logger.info(f"📸 Signal shutdown trace saved: {signal_trace}")
```

#### 💥 **Необработанные исключения**
```python
# src/main.py - global_exception_handler
error_trace = save_debug_snapshot("unhandled_exception")
logger.critical(f"📸 Unhandled exception trace saved: {error_trace}")
```

#### ❌ **Ошибки в route handlers**
```python
# src/presentation/routes/campaign_routes.py
try:
    # ... бизнес логика ...
except Exception as e:
    error_trace = save_debug_snapshot("create_offer_error")
    logger.error(f"📸 Create offer error trace saved: {error_trace}")
```

#### 🛑 **Graceful shutdown**
```python
# main_clean.py - atexit handler
shutdown_trace = save_debug_snapshot("server_shutdown")
logger.info(f"📸 Server shutdown trace saved: {shutdown_trace}")
```

### Форматы сохранения

**JSON** - Для программного анализа:
```python
from utils.async_debug import save_trace_to_file
json_file = save_trace_to_file(format="json")
# Сохраняет в traces/async_trace_YYYYMMDD_HHMMSS.json
```

**HTML** - Для визуального просмотра:
```python
html_file = save_trace_to_file(format="html")
# Сохраняет в traces/async_trace_YYYYMMDD_HHMMSS.html
# Открыть в браузере для интерактивного просмотра
```

**JSONL (JSON Lines)** - Для непрерывного логирования:
```python
from utils.async_debug import log_trace_to_continuous_file
log_trace_to_continuous_file("server_trace.jsonl")
# Добавляет каждую трассировку как отдельную строку в лог-файл
```

### Удобные функции

```python
from utils.async_debug import (
    save_trace_to_file,           # Сохранить в JSON/HTML
    log_trace_to_continuous_file, # Логировать непрерывно
    save_debug_snapshot          # Быстрый снимок с причиной
)

# Быстрый debug snapshot при ошибке
save_debug_snapshot("database_timeout")

# Непрерывное логирование в фоне
log_trace_to_continuous_file()
```

### Структура файлов

**traces/async_trace_20231211_143052.json:**
```json
{
  "timestamp": 1702305052.123,
  "current_task_name": "Task-42",
  "frames": [
    {
      "name": "handle_request",
      "line": 25,
      "filename": "handlers.py",
      "indent": 0,
      "task_name": "Task-42"
    },
    {
      "name": "create_campaign",
      "line": 120,
      "filename": "routes.py",
      "indent": 1
    }
  ]
}
```

**HTML файлы** содержат красивую визуализацию с:
- Статистикой (количество фреймов, задач, глубина)
- Интерактивными элементами
- Цветовой подсветкой границ задач
- Информацией о каждом фрейме

### Примеры использования

#### При ошибках:
```python
try:
    await risky_database_operation()
except Exception as e:
    # Сохранить состояние на момент ошибки
    snapshot_file = save_debug_snapshot("db_error")
    logger.error(f"Database error! Snapshot saved to: {snapshot_file}")
    raise
```

#### Мониторинг производительности:
```python
async def monitored_handler():
    start_time = time.time()

    # Логировать вход
    log_trace_to_continuous_file()

    result = await process_request()

    # Логировать выход с результатом
    log_trace_to_continuous_file()

    duration = time.time() - start_time
    if duration > 1.0:  # Медленный запрос
        slow_snapshot = save_debug_snapshot("slow_request")
        logger.warning(f"Slow request detected! Snapshot: {slow_snapshot}")

    return result
```

#### Анализ после факта:
```bash
# Просмотреть все сохраненные трейсы
ls traces/*.html
# Открыть в браузере для анализа

# Проанализировать JSON программно
python -c "
import json
with open('traces/debug_snapshot_error_143052.json') as f:
    trace = json.load(f)
    print(f'Task: {trace[\"current_task_name\"]}')
    print(f'Frames: {len(trace[\"frames\"])}')
"
```

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

#### Сохранение трейсов при подозрительных ситуациях:
```python
async def database_handler():
    debug_before_await("complex query")

    try:
        result = await db.execute_complex_query()
        debug_after_await("complex query")
        return result
    except Exception as e:
        # Сохранить состояние на момент ошибки
        error_snapshot = save_debug_snapshot("db_query_error")
        logger.error(f"Database error! Trace saved to: {error_snapshot}")
        raise

# Непрерывное логирование для мониторинга
async def request_handler():
    # Логировать каждый входящий запрос
    log_trace_to_continuous_file("request_log.jsonl")

    result = await process_request()

    # Логировать завершение
    log_trace_to_continuous_file("request_log.jsonl")

    return result
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
