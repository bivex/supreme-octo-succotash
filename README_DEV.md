# Development Guide

## Hot Reload

Проект поддерживает hot reload для удобной разработки. При изменении Python файлов сервер автоматически перезапускается.

### Запуск с hot reload

```bash
# Через development runner (рекомендуется)
python run_dev.py

# Или напрямую с флагом
python main_clean.py --reload

# Через batch скрипт
restarter.bat
```

### Что отслеживается

- Все файлы в директории `src/`
- Файл `main_clean.py`

При изменении любого `.py` файла (кроме `__pycache__`) сервер автоматически перезапускается.

### Установка зависимостей

```bash
# Установка dev зависимостей
pip install -r requirements-dev.txt

# Или через batch скрипт
setup_dev.bat
```

### Troubleshooting

Если hot reload не работает:

1. Убедитесь, что установлен `watchdog`: `pip install watchdog`
2. Проверьте, что файлы не в `__pycache__` директориях
3. Для Windows может потребоваться запуск с правами администратора

## Логирование

- Уровень логирования: `DEBUG`
- Полная трассировка исключений включена
- Логи пишутся в `app.log` и консоль

## Exception Handling

- Глобальный обработчик исключений перехватывает все неперехваченные ошибки
- Кастомный JSON encoder обрабатывает `Decimal` объекты
- Полная трассировка выводится в логи

## API Testing

```bash
# Запуск тестов
python test_api.py

# Или вручную
curl -H "Authorization: Bearer test_jwt_token_12345" http://localhost:5000/v1/campaigns
```
