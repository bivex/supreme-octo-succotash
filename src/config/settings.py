"""Application configuration settings."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseSettings:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "affiliate_db"
    user: str = "affiliate_user"
    password: str = ""
    connection_string: Optional[str] = None

    def get_connection_string(self) -> str:
        """Get database connection string."""
        if self.connection_string:
            return self.connection_string
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class APISettings:
    """API configuration."""
    host: str = "localhost"
    port: int = 5000
    debug: bool = False
    workers: int = 1
    cors_origins: list[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


@dataclass
class SecuritySettings:
    """Security configuration."""
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    rate_limit_requests: int = 1000000
    rate_limit_window_seconds: int = 60
    allowed_hosts: list[str] = None

    def __post_init__(self):
        if self.allowed_hosts is None:
            self.allowed_hosts = ["localhost", "127.0.0.1"]


@dataclass
class ExternalServicesSettings:
    """External services configuration."""
    ip_geolocation_api_key: Optional[str] = None
    ip_geolocation_timeout: int = 5
    redis_url: Optional[str] = None


@dataclass
class LoggingSettings:
    """Logging configuration."""
    level: str = "WARNING"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None


@dataclass
class Settings:
    """Main application settings."""
    environment: str = "development"
    database: DatabaseSettings = None
    api: APISettings = None
    security: SecuritySettings = None
    external_services: ExternalServicesSettings = None
    logging: LoggingSettings = None

    def __post_init__(self):
        # Comment out database initialization for mock server testing
        # if self.database is None:
        #     self.database = DatabaseSettings()
        if self.api is None:
            self.api = APISettings()
        if self.security is None:
            self.security = SecuritySettings()
        if self.external_services is None:
            self.external_services = ExternalServicesSettings()
        if self.logging is None:
            self.logging = LoggingSettings()


def _load_external_settings() -> ExternalServicesSettings:
    """Load external services settings from environment."""
    return ExternalServicesSettings(
        ip_geolocation_api_key=os.getenv("IP_GEOLOCATION_API_KEY"),
        ip_geolocation_timeout=int(os.getenv("IP_GEOLOCATION_TIMEOUT", "5")),
        redis_url=os.getenv("REDIS_URL"),
    )


def load_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        # Comment out database for mock server testing
        # database=DatabaseSettings(
        #     host=os.getenv("DB_HOST", "localhost"),
        #     port=int(os.getenv("DB_PORT", "5432")),
        #     database=os.getenv("DB_NAME", "affiliate_db"),
        #     user=os.getenv("DB_USER", "affiliate_user"),
        #     password=os.getenv("DB_PASSWORD", ""),
        #     connection_string=os.getenv("DATABASE_URL"),
        # ),
        api=APISettings(
            host=os.getenv("API_HOST", "localhost"),
            port=int(os.getenv("API_PORT", "5000")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            workers=int(os.getenv("WORKERS", "1")),
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        ),
        security=SecuritySettings(
            secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
        ),
        external_services=_load_external_settings(),
        logging=LoggingSettings(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=os.getenv("LOG_FILE"),
        ),
    )


# Global settings instance
settings = load_settings()
