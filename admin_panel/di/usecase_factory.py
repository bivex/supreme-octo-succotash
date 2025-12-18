# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
Use Case Factory - Creates application use cases.
"""

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


class UseCaseFactory:
    """Factory for creating application use cases."""

    def __init__(
        self,
        campaign_repository: ApiCampaignRepository,
        offer_repository: ApiOfferRepository,
        landing_page_repository: ApiLandingPageRepository
    ):
        """Initialize factory with repositories."""
        self._campaign_repository = campaign_repository
        self._offer_repository = offer_repository
        self._landing_page_repository = landing_page_repository

    # Campaign Use Cases
    @property
    def list_campaigns_use_case(self) -> ListCampaignsUseCase:
        """Get list campaigns use case."""
        return ListCampaignsUseCase(self._campaign_repository)

    @property
    def create_campaign_use_case(self) -> CreateCampaignUseCase:
        """Get create campaign use case."""
        return CreateCampaignUseCase(self._campaign_repository)

    @property
    def delete_campaign_use_case(self) -> DeleteCampaignUseCase:
        """Get delete campaign use case."""
        return DeleteCampaignUseCase(self._campaign_repository)

    @property
    def pause_campaign_use_case(self) -> PauseCampaignUseCase:
        """Get pause campaign use case."""
        return PauseCampaignUseCase(self._campaign_repository)

    @property
    def resume_campaign_use_case(self) -> ResumeCampaignUseCase:
        """Get resume campaign use case."""
        return ResumeCampaignUseCase(self._campaign_repository)

    # Offer Use Cases
    @property
    def list_offers_use_case(self) -> ListOffersUseCase:
        """Get list offers use case."""
        return ListOffersUseCase(self._offer_repository)

    @property
    def create_offer_use_case(self) -> CreateOfferUseCase:
        """Get create offer use case."""
        return CreateOfferUseCase(self._offer_repository)

    @property
    def get_offer_use_case(self) -> GetOfferUseCase:
        """Get offer use case."""
        return GetOfferUseCase(self._offer_repository)

    @property
    def update_offer_use_case(self) -> UpdateOfferUseCase:
        """Get update offer use case."""
        return UpdateOfferUseCase(self._offer_repository)

    @property
    def delete_offer_use_case(self) -> DeleteOfferUseCase:
        """Get delete offer use case."""
        return DeleteOfferUseCase(self._offer_repository)

    # Landing Page Use Cases
    @property
    def list_landing_pages_use_case(self) -> ListLandingPagesUseCase:
        """Get list landing pages use case."""
        return ListLandingPagesUseCase(self._landing_page_repository)

    @property
    def create_landing_page_use_case(self) -> CreateLandingPageUseCase:
        """Get create landing page use case."""
        return CreateLandingPageUseCase(self._landing_page_repository)

    @property
    def get_landing_page_use_case(self) -> GetLandingPageUseCase:
        """Get landing page use case."""
        return GetLandingPageUseCase(self._landing_page_repository)

    @property
    def update_landing_page_use_case(self) -> UpdateLandingPageUseCase:
        """Get update landing page use case."""
        return UpdateLandingPageUseCase(self._landing_page_repository)

    @property
    def delete_landing_page_use_case(self) -> DeleteLandingPageUseCase:
        """Get delete landing page use case."""
        return DeleteLandingPageUseCase(self._landing_page_repository)