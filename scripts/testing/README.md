# Testing Scripts

Скрипты для функционального тестирования, проверки API и бизнес-логики.

## Основные скрипты

- `run_tests.py` - Запуск полного набора тестов
- `test_api.py` - Тестирование REST API
- `test_business_logic.py` - Тестирование бизнес-логики
- `test_imports.py` - Проверка импортов модулей
- `test_pool_monitor.py` - Тестирование пула соединений
- `test_remaining_endpoints.py` - Тестирование всех эндпоинтов
- `validate_openapi.py` - Валидация OpenAPI спецификации

## Запуск

```bash
# Все тесты
python run_tests.py

# Тестирование API
python test_api.py

# Проверка бизнес-логики
python test_business_logic.py
```



