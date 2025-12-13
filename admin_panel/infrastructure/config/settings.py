"""Application Configuration."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Application settings loaded from environment."""

    # API Configuration
    api_base_url: str = "http://127.0.0.1:5000/v1"
    api_timeout: float = 30.0
    api_max_retries: int = 3

    # Authentication
    bearer_token: Optional[str] = None
    api_key: Optional[str] = None

    # UI Configuration
    auto_refresh_enabled: bool = True
    auto_refresh_interval: int = 30000  # milliseconds

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> 'Settings':
        """Load settings from environment variables."""
        return cls(
            api_base_url=os.getenv('API_BASE_URL', cls.api_base_url),
            api_timeout=float(os.getenv('API_TIMEOUT', cls.api_timeout)),
            api_max_retries=int(os.getenv('API_MAX_RETRIES', cls.api_max_retries)),
            bearer_token=os.getenv('API_BEARER_TOKEN'),
            api_key=os.getenv('API_KEY'),
            auto_refresh_enabled=os.getenv('AUTO_REFRESH', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', cls.log_level),
        )

    def update_from_ui(
        self,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> None:
        """Update settings from UI input."""
        if base_url:
            self.api_base_url = base_url
        if bearer_token:
            self.bearer_token = bearer_token
        if api_key:
            self.api_key = api_key
