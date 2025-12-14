"""Dependency Injection Container."""

from typing import Optional

import logging

logger = logging.getLogger(__name__)

from ..infrastructure.config.settings import Settings
from ..infrastructure.api.api_client import AdvertisingAPIClient
from ..infrastructure.repositories.api_campaign_repository import ApiCampaignRepository
from ..infrastructure.repositories.api_offer_repository import ApiOfferRepository
from ..infrastructure.repositories.api_landing_page_repository import ApiLandingPageRepository
from ..application.use_cases.campaign import (
    ListCampaignsUseCase,
    CreateCampaignUseCase,
    DeleteCampaignUseCase,
    PauseCampaignUseCase,
    ResumeCampaignUseCase
)
from ..application.use_cases.offer import (
    ListOffersUseCase,
    CreateOfferUseCase,
    GetOfferUseCase,
    UpdateOfferUseCase,
    DeleteOfferUseCase
)
from ..application.use_cases.landing_page import (
    ListLandingPagesUseCase,
    CreateLandingPageUseCase,
    GetLandingPageUseCase,
    UpdateLandingPageUseCase,
    DeleteLandingPageUseCase
)
from .infrastructure_factory import InfrastructureFactory
from .usecase_factory import UseCaseFactory


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

        # Initialize factories
        self._infrastructure_factory = InfrastructureFactory(settings)
        self._usecase_factory = None  # Lazy initialization

    @property
    def settings(self) -> Settings:
        """Get application settings."""
        return self._settings

    # Infrastructure - Delegated to InfrastructureFactory
    @property
    def api_client(self) -> AdvertisingAPIClient:
        """Get API client (singleton)."""
        return self._infrastructure_factory.api_client

    def recreate_api_client(
        self,
        base_url=None,
        bearer_token=None,
        api_key=None
    ) -> AdvertisingAPIClient:
        """Recreate API client with new credentials."""
        return self._infrastructure_factory.recreate_api_client(
            base_url, bearer_token, api_key
        )

    @property
    def campaign_repository(self) -> ApiCampaignRepository:
        logger.debug("Container: Accessing campaign_repository property.")
        repository = self._infrastructure_factory.campaign_repository
        logger.debug(f"Container: campaign_repository property returning: {type(repository)}")
        """Get campaign repository (singleton)."""
        return repository

    @property
    def offer_repository(self) -> ApiOfferRepository:
        """Get offer repository (singleton)."""
        return self._infrastructure_factory.offer_repository

    @property
    def landing_page_repository(self) -> ApiLandingPageRepository:
        """Get landing page repository (singleton)."""
        return self._infrastructure_factory.landing_page_repository

    # Use Cases - Delegated to UseCaseFactory
    @property
    def _usecase_factory_instance(self) -> UseCaseFactory:
        """Get use case factory (lazy initialization)."""
        if self._usecase_factory is None:
            self._usecase_factory = UseCaseFactory(
                campaign_repository=self.campaign_repository,
                offer_repository=self.offer_repository,
                landing_page_repository=self.landing_page_repository
            )
        return self._usecase_factory

    # Campaign Use Cases
    @property
    def list_campaigns_use_case(self) -> ListCampaignsUseCase:
        """Get list campaigns use case."""
        return self._usecase_factory_instance.list_campaigns_use_case

    @property
    def create_campaign_use_case(self) -> CreateCampaignUseCase:
        """Get create campaign use case."""
        return self._usecase_factory_instance.create_campaign_use_case

    @property
    def delete_campaign_use_case(self) -> DeleteCampaignUseCase:
        """Get delete campaign use case."""
        return self._usecase_factory_instance.delete_campaign_use_case

    @property
    def pause_campaign_use_case(self) -> PauseCampaignUseCase:
        """Get pause campaign use case."""
        return self._usecase_factory_instance.pause_campaign_use_case

    @property
    def resume_campaign_use_case(self) -> ResumeCampaignUseCase:
        """Get resume campaign use case."""
        return self._usecase_factory_instance.resume_campaign_use_case

    # Offer Use Cases
    @property
    def list_offers_use_case(self) -> ListOffersUseCase:
        """Get list offers use case."""
        return self._usecase_factory_instance.list_offers_use_case

    @property
    def create_offer_use_case(self) -> CreateOfferUseCase:
        """Get create offer use case."""
        return self._usecase_factory_instance.create_offer_use_case

    @property
    def get_offer_use_case(self) -> GetOfferUseCase:
        """Get offer use case."""
        return self._usecase_factory_instance.get_offer_use_case

    @property
    def update_offer_use_case(self) -> UpdateOfferUseCase:
        """Get update offer use case."""
        return self._usecase_factory_instance.update_offer_use_case

    @property
    def delete_offer_use_case(self) -> DeleteOfferUseCase:
        """Get delete offer use case."""
        return self._usecase_factory_instance.delete_offer_use_case

    # Landing Page Use Cases
    @property
    def list_landing_pages_use_case(self) -> ListLandingPagesUseCase:
        """Get list landing pages use case."""
        return self._usecase_factory_instance.list_landing_pages_use_case

    @property
    def create_landing_page_use_case(self) -> CreateLandingPageUseCase:
        """Get create landing page use case."""
        return self._usecase_factory_instance.create_landing_page_use_case

    @property
    def get_landing_page_use_case(self) -> GetLandingPageUseCase:
        """Get landing page use case."""
        return self._usecase_factory_instance.get_landing_page_use_case

    @property
    def update_landing_page_use_case(self) -> UpdateLandingPageUseCase:
        """Get update landing page use case."""
        return self._usecase_factory_instance.update_landing_page_use_case

    @property
    def delete_landing_page_use_case(self) -> DeleteLandingPageUseCase:
        """Get delete landing page use case."""
        return self._usecase_factory_instance.delete_landing_page_use_case

    def close(self) -> None:
        """Close all resources."""
        if hasattr(self, '_infrastructure_factory'):
            self._infrastructure_factory.close()
        # Clear references to help with garbage collection
        self._usecase_factory = None

        # Use cases (lazy initialization)
        self._list_campaigns_use_case: Optional[ListCampaignsUseCase] = None
        self._create_campaign_use_case: Optional[CreateCampaignUseCase] = None
        self._delete_campaign_use_case: Optional[DeleteCampaignUseCase] = None
        self._pause_campaign_use_case: Optional[PauseCampaignUseCase] = None
        self._resume_campaign_use_case: Optional[ResumeCampaignUseCase] = None
        self._list_offers_use_case: Optional[ListOffersUseCase] = None
        self._create_offer_use_case: Optional[CreateOfferUseCase] = None
        self._get_offer_use_case: Optional[GetOfferUseCase] = None
        self._update_offer_use_case: Optional[UpdateOfferUseCase] = None
        self._delete_offer_use_case: Optional[DeleteOfferUseCase] = None
        self._list_landing_pages_use_case: Optional[ListLandingPagesUseCase] = None
        self._create_landing_page_use_case: Optional[CreateLandingPageUseCase] = None
        self._get_landing_page_use_case: Optional[GetLandingPageUseCase] = None
        self._update_landing_page_use_case: Optional[UpdateLandingPageUseCase] = None
        self._delete_landing_page_use_case: Optional[DeleteLandingPageUseCase] = None

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
        self._campaign_repository = None  # Reset repositories
        self._offer_repository = None
        self._landing_page_repository = None

        # Force recreation
        _ = self.api_client

    # Repositories
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

    # Use Cases - Offers
    @property
    def list_offers_use_case(self) -> ListOffersUseCase:
        """Get list offers use case."""
        if self._list_offers_use_case is None:
            self._list_offers_use_case = ListOffersUseCase(
                self.offer_repository
            )
        return self._list_offers_use_case

    @property
    def create_offer_use_case(self) -> CreateOfferUseCase:
        """Get create offer use case."""
        if self._create_offer_use_case is None:
            self._create_offer_use_case = CreateOfferUseCase(
                self.offer_repository
            )
        return self._create_offer_use_case

    @property
    def get_offer_use_case(self) -> GetOfferUseCase:
        """Get get offer use case."""
        if self._get_offer_use_case is None:
            self._get_offer_use_case = GetOfferUseCase(
                self.offer_repository
            )
        return self._get_offer_use_case

    @property
    def update_offer_use_case(self) -> UpdateOfferUseCase:
        """Get update offer use case."""
        if self._update_offer_use_case is None:
            self._update_offer_use_case = UpdateOfferUseCase(
                self.offer_repository
            )
        return self._update_offer_use_case

    @property
    def delete_offer_use_case(self) -> DeleteOfferUseCase:
        """Get delete offer use case."""
        if self._delete_offer_use_case is None:
            self._delete_offer_use_case = DeleteOfferUseCase(
                self.offer_repository
            )
        return self._delete_offer_use_case

    # Use Cases - Landing Pages
    @property
    def list_landing_pages_use_case(self) -> ListLandingPagesUseCase:
        """Get list landing pages use case."""
        if self._list_landing_pages_use_case is None:
            self._list_landing_pages_use_case = ListLandingPagesUseCase(
                self.landing_page_repository
            )
        return self._list_landing_pages_use_case

    @property
    def create_landing_page_use_case(self) -> CreateLandingPageUseCase:
        """Get create landing page use case."""
        if self._create_landing_page_use_case is None:
            self._create_landing_page_use_case = CreateLandingPageUseCase(
                self.landing_page_repository
            )
        return self._create_landing_page_use_case

    @property
    def get_landing_page_use_case(self) -> GetLandingPageUseCase:
        """Get get landing page use case."""
        if self._get_landing_page_use_case is None:
            self._get_landing_page_use_case = GetLandingPageUseCase(
                self.landing_page_repository
            )
        return self._get_landing_page_use_case

    @property
    def update_landing_page_use_case(self) -> UpdateLandingPageUseCase:
        """Get update landing page use case."""
        if self._update_landing_page_use_case is None:
            self._update_landing_page_use_case = UpdateLandingPageUseCase(
                self.landing_page_repository
            )
        return self._update_landing_page_use_case

    @property
    def delete_landing_page_use_case(self) -> DeleteLandingPageUseCase:
        """Get delete landing page use case."""
        if self._delete_landing_page_use_case is None:
            self._delete_landing_page_use_case = DeleteLandingPageUseCase(
                self.landing_page_repository
            )
        return self._delete_landing_page_use_case

    def close(self) -> None:
        """Close all resources."""
        if hasattr(self, '_infrastructure_factory'):
            self._infrastructure_factory.close()
        # Clear references to help with garbage collection
        self._usecase_factory = None
