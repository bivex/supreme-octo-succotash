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

"""Campaign Use Cases."""

from typing import List, Optional
from decimal import Decimal

DEFAULT_PAGE_SIZE = 20

from ....domain.entities import Campaign, CampaignStatus
from ....domain.value_objects import Money, Budget, DateRange, BudgetType
from ....domain.repositories import ICampaignRepository
from ...dtos import CampaignDTO, CreateCampaignRequest


class ListCampaignsUseCase:
    """Use case for listing campaigns."""

    def __init__(self, repository: ICampaignRepository):
        self._repository = repository

    def execute(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        status: Optional[str] = None
    ) -> tuple[List[CampaignDTO], int]:
        """Execute the use case."""
        status_enum = CampaignStatus(status) if status else None
        campaigns = self._repository.find_all(page, page_size, status_enum)
        total = self._repository.count_all(status_enum)

        dtos = [self._to_dto(c) for c in campaigns]
        return dtos, total

    @staticmethod
    def _to_dto(campaign: Campaign) -> CampaignDTO:
        """Convert entity to DTO."""
        end_date_iso = (
            campaign.date_range.end_date.isoformat()
            if campaign.date_range.end_date else None
        )
        return CampaignDTO(
            id=campaign.id,
            name=campaign.name,
            status=campaign.status.value,
            budget_amount=campaign.budget.amount.to_float(),
            budget_currency=campaign.budget.amount.currency,
            budget_type=campaign.budget.budget_type.value,
            target_url=campaign.target_url,
            start_date=campaign.date_range.start_date.isoformat(),
            end_date=end_date_iso,
            created_at=campaign.created_at
        )


class CreateCampaignUseCase:
    """Use case for creating a campaign."""

    def __init__(self, repository: ICampaignRepository):
        self._repository = repository

    def execute(self, request: CreateCampaignRequest) -> CampaignDTO:
        """Execute the use case."""
        # Convert DTO to domain objects
        money = Money.from_float(request.budget_amount, request.budget_currency)
        budget_type = BudgetType(request.budget_type)
        budget = Budget(money, budget_type)
        date_range = DateRange.from_strings(request.start_date, request.end_date)

        # Create domain entity
        campaign = Campaign.create(
            name=request.name,
            budget=budget,
            target_url=request.target_url,
            date_range=date_range
        )

        # Persist
        saved_campaign = self._repository.save(campaign)

        # Return DTO
        return ListCampaignsUseCase._to_dto(saved_campaign)


class DeleteCampaignUseCase:
    """Use case for deleting a campaign."""

    def __init__(self, repository: ICampaignRepository):
        self._repository = repository

    def execute(self, campaign_id: str) -> None:
        """Execute the use case."""
        self._repository.delete(campaign_id)


class PauseCampaignUseCase:
    """Use case for pausing a campaign."""

    def __init__(self, repository: ICampaignRepository):
        self._repository = repository

    def execute(self, campaign_id: str) -> CampaignDTO:
        """Execute the use case."""
        campaign = self._repository.find_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign.pause()
        saved_campaign = self._repository.save(campaign)
        return ListCampaignsUseCase._to_dto(saved_campaign)


class ResumeCampaignUseCase:
    """Use case for resuming a campaign."""

    def __init__(self, repository: ICampaignRepository):
        self._repository = repository

    def execute(self, campaign_id: str) -> CampaignDTO:
        """Execute the use case."""
        campaign = self._repository.find_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign.resume()
        saved_campaign = self._repository.save(campaign)
        return ListCampaignsUseCase._to_dto(saved_campaign)
