"""
Configuration for Telegram bot with click tracking to landing pages
"""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""

    # Telegram Bot
    bot_token: str = Field(..., env="BOT_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, env="ADMIN_IDS")

    # Supreme Tracker
    tracker_domain: str = Field(..., env="TRACKER_DOMAIN")
    campaign_id: str = Field("camp_9061", env="CAMPAIGN_ID")  # Fixed to correct campaign ID

    # Landing Page
    landing_url: str = Field(..., env="LANDING_URL")

    # Database (optional)
    database_url: Optional[str] = Field(None, env="DATABASE_URL")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


# Default tracking parameters
DEFAULT_TRACKING_PARAMS = {
    "sub1": "telegram_bot",
    "sub2": "local_landing",
    "sub3": "supreme_company",
    "sub4": "direct_message",
    "sub5": "premium_offer"
}


# Bot messages
BOT_MESSAGES = {
    "welcome": """
Добро пожаловать в Supreme Company!

Я помогу вам перейти на специальную страницу с нашим предложением.

Нажмите кнопку ниже, чтобы узнать подробности.
""",

    "main_offer": """
🚀 Supreme Company - Премиум решение

Узнайте, как достичь результатов быстрее с нашей помощью.

Результаты наших клиентов:
✅ 200% увеличение производительности
✅ 80% экономия времени
✅ Полная поддержка 24/7
✅ Индивидуальный подход
""",

    "cta_button": "Узнать подробности",

    "after_click": """
Отлично! Вы перешли на страницу предложения.

Если возникнут вопросы, пишите мне здесь.
Я всегда на связи.
""",

    "conversion_notification": """
🎉 Новая заявка!

Пользователь {user_id} оставил заявку
Имя: {name}
Email: {email}

Свяжитесь с клиентом как можно скорее!
"""
}


# API endpoints
API_ENDPOINTS = {
    "click_generate": "/clicks/generate",
    "event_track": "/events/track",
    "conversion_track": "/conversions/track",
    "postback_send": "/postbacks/send"
}
