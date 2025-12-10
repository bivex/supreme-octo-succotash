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

    # Keitaro Tracker
    tracker_domain: str = Field(..., env="TRACKER_DOMAIN")
    campaign_id: int = Field(..., env="CAMPAIGN_ID")

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
    "sub2": "organic",
    "sub3": "main_flow",
    "sub4": "direct_message",
    "sub5": "standard_offer"
}


# Bot messages
BOT_MESSAGES = {
    "welcome": """
Hello. I will help you visit a special page with our offer.

Click the button below to learn more details.
""",

    "main_offer": """
Special offer.

Learn how to achieve results faster with our help.

Our client results include:
- 150% increase in performance
- 70% time savings
- Full support available 24/7
""",

    "cta_button": "Learn more details",

    "after_click": """
Good. You have visited the offer page.

If you have questions, write to me here.
I am always available.
""",

    "conversion_notification": """
Congratulations.

You have a new application from user {user_id}
Name: {name}
Email: {email}

Contact the client quickly.
"""
}


# API endpoints
API_ENDPOINTS = {
    "click_generate": "/clicks/generate",
    "event_track": "/events/track",
    "conversion_track": "/conversions/track",
    "postback_send": "/postbacks/send"
}
