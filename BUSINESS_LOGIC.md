# Бизнес-логика системы трекинга кликов

## Обзор

Система трекинга кликов предназначена для отслеживания пользовательских переходов, валидации трафика и управления редиректами в рекламных кампаниях. Система поддерживает различные источники трафика (Telegram боты, партнерские сети) и обеспечивает гибкую логику редиректа на основе приоритетов.

## Основные сущности

### 1. Click (Клик)
- **ID**: Уникальный идентификатор клика
- **Campaign ID**: ID рекламной кампании
- **Source**: Источник трафика (telegram_bot, partner_network, etc.)
- **IP Address**: IP адрес пользователя
- **User Agent**: Браузер/устройство пользователя
- **Referrer**: Реферер (источник перехода)
- **Landing Page ID**: ID целевой страницы (опционально)
- **Offer ID**: ID предложения/оффера (опционально)
- **Traffic Source ID**: ID источника трафика (опционально)
- **Tracking Parameters**: Дополнительные параметры (sub1-sub5, click_id, etc.)
- **Timestamp**: Время клика
- **Fraud Status**: Статус фрода (valid/invalid/fraudulent)
- **Validation Score**: Оценка валидности

### 2. Campaign (Кампания)
- **ID**: Уникальный идентификатор кампании
- **Name**: Название кампании
- **Offer Page URL**: URL страницы предложения
- **Safe Page URL**: URL безопасной страницы
- **Status**: Статус кампании (active/inactive)
- **Performance Metrics**: Метрики производительности

### 3. Landing Page (Целевая страница)
- **ID**: Уникальный идентификатор
- **Name**: Название страницы
- **URL**: URL страницы
- **Is Active**: Статус активности
- **Campaign ID**: ID связанной кампании

### 4. Offer (Предложение)
- **ID**: Уникальный идентификатор
- **Name**: Название предложения
- **URL**: URL предложения
- **Is Active**: Статус активности
- **Campaign ID**: ID связанной кампании

## Бизнес-процессы

### 1. Обработка клика (Track Click)

#### Входные данные:
- Campaign ID (cid)
- Landing Page ID (lp_id) - опционально
- Offer ID (offer_id) - опционально
- Traffic Source ID (ts_id) - опционально
- Tracking параметры (sub1-sub5, click_id, etc.)

#### Алгоритм обработки:

1. **Поиск кампании**
   - Найти кампанию по campaign_id
   - Если кампания не найдена → редирект на fallback URL

2. **Создание объекта Click**
   - Генерация уникального click_id
   - Сбор всех параметров из запроса

3. **Валидация клика**
   - Проверка на фрод с использованием ClickValidationService
   - Анализ: IP, User Agent, геолокация, частота кликов
   - Присвоение fraud_score и статуса валидности

4. **Определение URL редиректа**
   - **Приоритет 1**: Landing Page по lp_id
     - Если lp_id указан и landing page найден и активен
     - Пропустить проверку фрода (доверительный редирект)
   - **Приоритет 2**: Offer по offer_id
     - Если offer_id указан и offer найден и активен
     - Пропустить проверку фрода (доверительный редирект)
   - **Приоритет 3**: Campaign URLs для валидных кликов
     - Использовать offer_page_url кампании
     - Или safe_page_url если offer_page_url не задан
   - **Приоритет 4**: Campaign safe page для невалидных кликов
     - Использовать safe_page_url кампании
   - **Fallback**: Системный safe page URL

5. **Сохранение клика**
   - Запись в базу данных
   - Обновление метрик кампании (если валидный клик)

6. **Редирект пользователя**
   - 302 redirect на определенный URL
   - Добавление click_id в URL при test_mode

### 2. Генерация Tracking URL (API /clicks/generate)

#### Входные данные:
- base_url: Базовый URL системы
- campaign_id: ID кампании
- click_id: Уникальный ID клика
- source: Источник трафика
- lp_id, offer_id, ts_id: Опциональные ID для таргетинга
- Дополнительные параметры (sub1-sub5, metadata)

#### Алгоритм:
1. Валидация входных параметров
2. Создание tracking URL с base_url + параметры
3. Оптимизация параметров для URL
4. Возврат tracking URL с click_id и всеми параметрами

### 3. Отслеживание событий (Event Tracking)

#### Типы событий:
- **click**: Первичный клик
- **page_view**: Просмотр страницы
- **conversion**: Конверсия (заявка, покупка)
- **bounce**: Отказ от страницы

#### Логика:
1. Получение события от клиента
2. Валидация click_id и campaign_id
3. Анализ фрода для события
4. Сохранение события в БД
5. Обновление метрик кампании

## Логика валидации фрода

### Уровни валидации:
1. **IP Validation**: Проверка черных списков IP
2. **Geographic Validation**: Проверка геолокации
3. **Frequency Validation**: Ограничение частоты кликов
4. **User Agent Validation**: Анализ подозрительных UA
5. **Referrer Validation**: Проверка источника перехода
6. **Bot Detection**: Обнаружение ботов и скриптов

### Fraud Score:
- 0-30: Valid (зеленый)
- 31-70: Suspicious (желтый)
- 71-100: Fraudulent (красный)

## Метрики производительности

### Campaign Metrics:
- **Total Clicks**: Общее количество кликов
- **Valid Clicks**: Валидные клики
- **Invalid Clicks**: Невалидные клики
- **Fraud Clicks**: Клики с фродом
- **CTR**: Click-through rate
- **Conversion Rate**: Процент конверсий

### Traffic Source Metrics:
- **Source Performance**: Эффективность источников
- **Geographic Distribution**: Географическое распределение
- **Device/Browser Stats**: Статистика устройств и браузеров

## API Endpoints

### Click Tracking:
- `GET /v1/click` - Обработка клика и редирект
- `POST /clicks/generate` - Генерация tracking URL

### Event Tracking:
- `POST /events/track` - Отправка события

### Management:
- `GET /v1/clicks` - Получение списка кликов
- `GET /v1/clicks/{click_id}` - Детали клика
- `PUT /v1/campaigns/{campaign_id}` - Обновление кампании

## Безопасность и производительность

### Rate Limiting:
- Ограничение по IP: 100 кликов/минуту
- Ограничение по кампании: 1000 кликов/минуту
- DDoS защита через Cloudflare/AWS Shield

### Data Retention:
- Raw click data: 90 дней
- Aggregated metrics: 2 года
- Fraud logs: 1 год

### Monitoring:
- Real-time alerts на подозрительную активность
- Performance monitoring всех компонентов
- Business metrics dashboard

## Масштабируемость

### Архитектура:
- **Microservices**: Разделение на сервисы (tracking, validation, analytics)
- **Event-Driven**: Асинхронная обработка через Kafka/RabbitMQ
- **Database Sharding**: Горизонтальное масштабирование БД
- **CDN Integration**: Кеширование статических ресурсов

### Performance Targets:
- **Response Time**: <100ms для 95% запросов
- **Throughput**: 10,000+ кликов/секунду
- **Availability**: 99.9% uptime
- **Data Freshness**: Real-time для critical metrics
