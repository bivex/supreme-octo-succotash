# Telegram Bot Restarter Scripts

## Описание

Скрипты для автоматического перезапуска Telegram бота с правильной настройкой вебхуков.

## Файлы

### `bot_restarter.bat`

Полнофункциональный рестартер для работы в webhook режиме:

- Удаляет существующий вебхук
- Устанавливает новый вебхук
- Проверяет статус вебхука
- Запускает бота в webhook режиме

### `bot_restarter_simple.bat`

Простой рестартер для работы в polling режиме:

- Удаляет вебхук (чтобы бот работал в polling режиме)
- Запускает бота в polling режиме

## Настройка

### 1. Создайте файл `.env`

```bash
# Скопируйте из env.example
cp env.example .env

# Отредактируйте .env файл:
BOT_TOKEN=ваш_токен_бота
# другие настройки...
```

### 2. Настройте WEBHOOK_URL (для webhook режима)

В `.env` файле добавьте:

```bash
WEBHOOK_URL=https://ваш-домен.ngrok-free.dev/webhook
```

Или измените в `bot_restarter.bat`:

```batch
set WEBHOOK_URL=https://ваш-домен.ngrok-free.dev/webhook
```

## Использование

### Webhook режим (рекомендуется для продакшена)

```bash
bot_restarter.bat
```

### Polling режим (для разработки)

```bash
bot_restarter_simple.bat
```

## Что делает скрипт

### bot_restarter.bat:

1. **Проверяет наличие файла `.env`**
2. **Загружает переменные окружения**
3. **Удаляет существующий вебхук** через Telegram API
4. **Устанавливает новый вебхук** с указанным URL
5. **Проверяет статус вебхука**
6. **Запускает бота** в webhook режиме

### bot_restarter_simple.bat:

1. **Проверяет наличие файла `.env`**
2. **Удаляет вебхук** (чтобы бот мог работать в polling режиме)
3. **Запускает бота** в polling режиме

## Troubleshooting

### Ошибка "BOT_TOKEN not found"

- Убедитесь что файл `.env` существует
- Проверьте что в нем указан `BOT_TOKEN=ваш_токен`

### Ошибка установки вебхука

- Проверьте что `WEBHOOK_URL` доступен (ngrok работает)
- Убедитесь что URL начинается с `https://`
- Проверьте логи бота на ошибки

### Бот не отвечает на сообщения

- В webhook режиме: проверьте что вебхук установлен (`getWebhookInfo`)
- В polling режиме: проверьте что нет активного вебхука

## Полезные команды для отладки

```bash
# Проверить статус вебхука
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Удалить вебхук вручную
curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"

# Установить вебхук вручную
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" -d "url=https://your-domain.ngrok-free.dev/webhook"
```
