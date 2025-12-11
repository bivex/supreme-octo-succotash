# Бизнес-логика системы трекинга кликов

## 🎯 Основная цель
Система обеспечивает отслеживание рекламных кликов, валидацию трафика и умное управление редиректами пользователей на целевые страницы.

## 🔄 Основной процесс: Обработка клика

### Шаг 1: Получение клика
```
Пользователь → GET /v1/click?cid=camp_9061&lp_id=42&offer_id=24&ts_id=1
```

### Шаг 2: Валидация кампании
- Найти кампанию по `campaign_id`
- Если не найдена → редирект на fallback URL

### Шаг 3: Создание объекта клика
- Генерация `click_id`
- Сбор всех параметров (IP, UA, referrer, tracking params)

### Шаг 4: Fraud Detection
- Анализ IP, геолокации, частоты кликов
- Присвоение fraud_score (0-100)
- Маркировка подозрительных кликов

### Шаг 5: Определение редиректа (Приоритеты)

#### 🔥 **Приоритет 1: Landing Page (lp_id)**
```python
if lp_id and landing_page.exists() and landing_page.is_active:
    redirect_url = landing_page.url
    skip_fraud_check = True  # Доверительный редирект
```

#### 🔥 **Приоритет 2: Offer (offer_id)**
```python
if offer_id and offer.exists() and offer.is_active:
    redirect_url = offer.url
    skip_fraud_check = True  # Доверительный редирект
```

#### 🔥 **Приоритет 3: Campaign URLs (Valid clicks)**
```python
if is_valid and campaign.offer_page_url:
    redirect_url = campaign.offer_page_url
elif is_valid and campaign.safe_page_url:
    redirect_url = campaign.safe_page_url
```

#### 🔥 **Приоритет 4: Safe Page (Invalid clicks)**
```python
if not is_valid and campaign.safe_page_url:
    redirect_url = campaign.safe_page_url
```

#### 🔥 **Приоритет 5: Fallback**
```python
redirect_url = "http://localhost:5000/mock-safe-page"
```

### Шаг 6: Сохранение и метрики
- Сохранение клика в БД
- Обновление счетчиков кампании
- Логирование для аналитики

### Шаг 7: Редирект
- 302 HTTP redirect на выбранный URL
- Добавление `click_id` в test mode

## 🎲 Генерация Tracking URL

### Вход от бота:
```json
{
  "campaign_id": 9061,
  "lp_id": 42,
  "offer_id": 24,
  "ts_id": 1,
  "source": "telegram_bot"
}
```

### Выход:
```
https://domain.com/v1/click?cid=camp_9061&lp_id=42&offer_id=24&ts_id=1
```

## 📊 Fraud Detection Rules

### Красные флаги:
- **IP в черном списке**
- **Подозрительный User Agent** (боты, скрипты)
- **Неестественная частота** (>10 кликов/минуту с одного IP)
- **Несоответствие геолокации**
- **Отсутствие referrer** при ожидаемом источнике

### Fraud Score:
- **0-30**: ✅ Valid (зеленый)
- **31-70**: ⚠️ Suspicious (желтый)
- **71-100**: ❌ Fraudulent (красный)

## 📈 Метрики и аналитика

### Campaign Performance:
- Total/Valid/Invalid/Fraud clicks
- CTR, Conversion Rate
- География, устройства, источники

### Real-time monitoring:
- Fraud alerts
- Traffic anomalies
- Performance degradation

## 🛡️ Безопасность

### Rate Limiting:
- 100 кликов/минуту per IP
- 1000 кликов/минуту per campaign

### Data Protection:
- GDPR compliance
- PII encryption
- Secure API endpoints

## 🎯 Use Cases

### 1. Telegram Bot Marketing
```
Бот → Генерация URL с lp_id → Пользователь клик → Редирект на landing page
```

### 2. Affiliate Network
```
Партнер → API генерация с offer_id → Traffic → Редирект на offer
```

### 3. A/B Testing
```
Кампания → Разные landing pages → Аналитика конверсий
```

### 4. Fraud Prevention
```
Подозрительный трафик → Safe page → Снижение убытков
```

## 🚀 Масштабируемость

- **Microservices architecture**
- **Event-driven processing**
- **Horizontal database scaling**
- **CDN integration**

**Target: 10,000+ кликов/секунду при <100ms response time**
