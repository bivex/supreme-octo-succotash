"""Application Configuration."""

import os
import configparser
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import logging

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Application settings loaded from environment or INI file."""

    # Default INI file location
    INI_FILE_PATH = Path(__file__).parent.parent.parent / "config.ini"

    # API Configuration
    api_base_url: str = "http://127.0.0.1:5000/v1"
    api_timeout: float = 30.0
    api_max_retries: int = 3

    # Authentication
    _bearer_token_val: Optional[str] = None
    _api_key_val: Optional[str] = None  # Deprecated: Use JWT tokens instead

    # UI Configuration
    auto_refresh_enabled: bool = True
    auto_refresh_interval: int = 30000  # milliseconds

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> 'Settings':
        """Load settings from INI file, then override with environment variables."""
        # Try to load from INI file first
        try:
            if cls.INI_FILE_PATH.exists():
                settings = cls.load_from_ini()
            else:
                settings = cls()
        except Exception as e:
            logger.warning(f"⚠️  Warning: Failed to load INI file, using defaults: {e}")
            settings = cls()

        # Override with environment variables if present
        settings._override_from_env(settings)

        return settings

    def _override_from_env(self, settings: 'Settings') -> None:
        try:
            if os.getenv('API_BASE_URL'):
                settings.api_base_url = os.getenv('API_BASE_URL')
            if os.getenv('API_TIMEOUT'):
                settings.api_timeout = float(os.getenv('API_TIMEOUT'))
            if os.getenv('API_MAX_RETRIES'):
                settings.api_max_retries = int(os.getenv('API_MAX_RETRIES'))
            if os.getenv('API_BEARER_TOKEN'):
                settings.bearer_token = os.getenv('API_BEARER_TOKEN')
            if os.getenv('API_KEY'):
                settings.api_key = os.getenv('API_KEY')
            if os.getenv('AUTO_REFRESH'):
                settings.auto_refresh_enabled = os.getenv('AUTO_REFRESH', 'true').lower() == 'true'
            if os.getenv('LOG_LEVEL'):
                settings.log_level = os.getenv('LOG_LEVEL')
        except Exception as e:
            logger.warning(f"⚠️  Warning: Failed to parse environment variables: {e}")

    @classmethod
    def load_from_ini(cls, file_path: Optional[Path] = None) -> 'Settings':
        """Load settings from INI file."""
        ini_path = file_path or cls.INI_FILE_PATH

        config = configparser.ConfigParser()
        try:
            config.read(ini_path)
        except Exception as e:
            logger.warning(f"⚠️  Warning: Failed to read INI file {ini_path}: {e}")
            return cls()

        # Helper to safely get values
        def get_str(section: str, key: str, default: str = None) -> Optional[str]:
            try:
                value = config.get(section, key)
                return value
            except (configparser.NoSectionError, configparser.NoOptionError):
                return default

        def get_float(section: str, key: str, default: float) -> float:
            try:
                return config.getfloat(section, key)
            except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
                return default

        def get_int(section: str, key: str, default: int) -> int:
            try:
                return config.getint(section, key)
            except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
                return default

        def get_bool(section: str, key: str, default: bool) -> bool:
            try:
                return config.getboolean(section, key)
            except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
                return default

        return cls(
            api_base_url=get_str('API', 'base_url', cls.api_base_url),
            api_timeout=get_float('API', 'timeout', cls.api_timeout),
            api_max_retries=get_int('API', 'max_retries', cls.api_max_retries),
            _bearer_token_val=get_str('API', 'bearer_token'),
            _api_key_val=get_str('API', 'api_key'),
            auto_refresh_enabled=get_bool('UI', 'auto_refresh_enabled', cls.auto_refresh_enabled),
            auto_refresh_interval=get_int('UI', 'auto_refresh_interval', cls.auto_refresh_interval),
            log_level=get_str('Logging', 'log_level', cls.log_level),
        )


    # Temporary variables to store token values read from INI
    _bearer_token_val: Optional[str] = None
    _api_key_val: Optional[str] = None

    # Properties to handle the temporary variables
    @property
    def bearer_token(self) -> Optional[str]:
        return self._bearer_token_val

    @bearer_token.setter
    def bearer_token(self, value: Optional[str]):
        self._bearer_token_val = value
        logger.debug(f"Settings: Bearer token set to {self._bearer_token_val}")

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key_val

    @api_key.setter
    def api_key(self, value: Optional[str]):
        self._api_key_val = value
        logger.debug(f"Settings: API key set to {self._api_key_val}")

    def save_to_ini(self, file_path: Optional[Path] = None) -> None:
        """Save settings to INI file."""
        ini_path = file_path or self.INI_FILE_PATH

        try:
            config = configparser.ConfigParser()

            # API section
            config['API'] = {
                'base_url': self.api_base_url,
                'timeout': str(self.api_timeout),
                'max_retries': str(self.api_max_retries),
            }

            # Add optional authentication values only if they exist
            config['API']['bearer_token'] = self.bearer_token if self.bearer_token is not None else ''
            config['API']['api_key'] = self.api_key if self.api_key is not None else ''

            # UI section
            config['UI'] = {
                'auto_refresh_enabled': str(self.auto_refresh_enabled),
                'auto_refresh_interval': str(self.auto_refresh_interval),
            }

            # Logging section
            config['Logging'] = {
                'log_level': self.log_level,
            }

            # Write to file
            with open(ini_path, 'w') as configfile:
                config.write(configfile)

        except Exception as e:
            logger.warning(f"⚠️  Warning: Failed to save settings to {ini_path}: {e}")
            raise

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
