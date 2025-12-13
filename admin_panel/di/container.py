"""Dependency Injection Container."""

from typing import Optional

from infrastructure.config.settings import Settings
from infrastructure.api.api_client import AdvertisingAPIClient
from infrastructure.repositories.api_campaign_repository import ApiCampaignRepository
from application.use_cases.campaign import (
    ListCampaignsUseCase,
    CreateCampaignUseCase,
    DeleteCampaignUseCase,
    PauseCampaignUseCase,
    ResumeCampaignUseCase
)


class Container:
    """
    Dependency Injection Container.

    Wires up all application dependencies following the Dependency Inversion Principle.
    High-level modules (use cases) depend on abstractions (repository interfaces),
    and low-level modules (repositories) implement those abstractions.
    """

    def __init__(self, settings: Settings):
        """Initialize container with settings."""
        self._settings = settings

        # Infrastructure (lazy initialization)
        self._api_client: Optional[AdvertisingAPIClient] = None
        self._campaign_repository: Optional[ApiCampaignRepository] = None

        # Use cases (lazy initialization)
        self._list_campaigns_use_case: Optional[ListCampaignsUseCase] = None
        self._create_campaign_use_case: Optional[CreateCampaignUseCase] = None
        self._delete_campaign_use_case: Optional[DeleteCampaignUseCase] = None
        self._pause_campaign_use_case: Optional[PauseCampaignUseCase] = None
        self._resume_campaign_use_case: Optional[ResumeCampaignUseCase] = None

    # Settings
    @property
    def settings(self) -> Settings:
        """Get application settings."""
        return self._settings

    # Infrastructure - API Client
    @property
    def api_client(self) -> AdvertisingAPIClient:
        """Get API client (singleton)."""
        if self._api_client is None:
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
        bearer_token: Optional[str] = None
    ) -> None:
        """Recreate API client with new settings (e.g., after connection)."""
        if base_url:
            self._settings.api_base_url = base_url
        if bearer_token:
            self._settings.bearer_token = bearer_token

        # Close old client
        if self._api_client:
            self._api_client.close()

        # Create new client
        self._api_client = None
        self._campaign_repository = None  # Reset repository too

        # Force recreation
        _ = self.api_client

    # Repositories
    @property
    def campaign_repository(self) -> ApiCampaignRepository:
        """Get campaign repository (singleton)."""
        if self._campaign_repository is None:
            self._campaign_repository = ApiCampaignRepository(self.api_client)
        return self._campaign_repository

    # Use Cases - Campaigns
    @property
    def list_campaigns_use_case(self) -> ListCampaignsUseCase:
        """Get list campaigns use case."""
        if self._list_campaigns_use_case is None:
            self._list_campaigns_use_case = ListCampaignsUseCase(
                self.campaign_repository
            )
        return self._list_campaigns_use_case

    @property
    def create_campaign_use_case(self) -> CreateCampaignUseCase:
        """Get create campaign use case."""
        if self._create_campaign_use_case is None:
            self._create_campaign_use_case = CreateCampaignUseCase(
                self.campaign_repository
            )
        return self._create_campaign_use_case

    @property
    def delete_campaign_use_case(self) -> DeleteCampaignUseCase:
        """Get delete campaign use case."""
        if self._delete_campaign_use_case is None:
            self._delete_campaign_use_case = DeleteCampaignUseCase(
                self.campaign_repository
            )
        return self._delete_campaign_use_case

    @property
    def pause_campaign_use_case(self) -> PauseCampaignUseCase:
        """Get pause campaign use case."""
        if self._pause_campaign_use_case is None:
            self._pause_campaign_use_case = PauseCampaignUseCase(
                self.campaign_repository
            )
        return self._pause_campaign_use_case

    @property
    def resume_campaign_use_case(self) -> ResumeCampaignUseCase:
        """Get resume campaign use case."""
        if self._resume_campaign_use_case is None:
            self._resume_campaign_use_case = ResumeCampaignUseCase(
                self.campaign_repository
            )
        return self._resume_campaign_use_case

    def close(self) -> None:
        """Close all resources."""
        if self._api_client:
            self._api_client.close()
