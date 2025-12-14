"""
Infrastructure Factory - Creates infrastructure components.
"""

from typing import Optional

import logging

logger = logging.getLogger(__name__)

from ..infrastructure.config.settings import Settings
from ..infrastructure.api.api_client import AdvertisingAPIClient
from ..infrastructure.repositories.api_campaign_repository import ApiCampaignRepository
from ..infrastructure.repositories.api_offer_repository import ApiOfferRepository
from ..infrastructure.repositories.api_landing_page_repository import ApiLandingPageRepository


class InfrastructureFactory:
    """Factory for creating infrastructure components."""

    def __init__(self, settings: Settings):
        """Initialize factory with settings."""
        self._settings = settings

        # Infrastructure components (lazy initialization)
        self._api_client: Optional[AdvertisingAPIClient] = None
        self._campaign_repository: Optional[ApiCampaignRepository] = None
        self._offer_repository: Optional[ApiOfferRepository] = None
        self._landing_page_repository: Optional[ApiLandingPageRepository] = None

    @property
    def api_client(self) -> AdvertisingAPIClient:
        """Get API client (singleton)."""
        if self._api_client is None:
            logger.debug(f"InfrastructureFactory: Creating new API client with base_url={self._settings.api_base_url}, bearer_token={'<set>' if self._settings.bearer_token else '<not set>'}, api_key={'<set>' if self._settings.api_key else '<not set>'}, timeout={self._settings.api_timeout}")
            self._api_client = AdvertisingAPIClient(
                base_url=self._settings.api_base_url,
                bearer_token=self._settings.bearer_token,
                api_key=self._settings.api_key,
                timeout=self._settings.api_timeout
            )
        return self._api_client

    def recreate_api_client(
        self,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> AdvertisingAPIClient:
        """Recreate API client with new credentials."""
        logger.debug(f"InfrastructureFactory: Recreating API client with base_url={base_url or self._settings.api_base_url}, bearer_token={'<set>' if (bearer_token or self._settings.bearer_token) else '<not set>'}, api_key={'<set>' if (api_key or self._settings.api_key) else '<not set>'}")
        self._api_client = AdvertisingAPIClient(
            base_url=base_url or self._settings.api_base_url,
            bearer_token=bearer_token or self._settings.bearer_token,
            api_key=api_key or self._settings.api_key,
            timeout=self._settings.api_timeout
        )
        # Reset dependent repositories to use new client
        self._campaign_repository = None
        self._offer_repository = None
        self._landing_page_repository = None
        return self._api_client

    @property
    def campaign_repository(self) -> ApiCampaignRepository:
        """Get campaign repository (singleton)."""
        if self._campaign_repository is None:
            self._campaign_repository = ApiCampaignRepository(self.api_client)
        return self._campaign_repository

    @property
    def offer_repository(self) -> ApiOfferRepository:
        """Get offer repository (singleton)."""
        if self._offer_repository is None:
            self._offer_repository = ApiOfferRepository(self.api_client)
        return self._offer_repository

    @property
    def landing_page_repository(self) -> ApiLandingPageRepository:
        """Get landing page repository (singleton)."""
        if self._landing_page_repository is None:
            self._landing_page_repository = ApiLandingPageRepository(self.api_client)
        return self._landing_page_repository

    def close(self) -> None:
        """Close infrastructure resources."""
        # Close API client if needed
        if self._api_client:
            # API client cleanup if necessary
            pass