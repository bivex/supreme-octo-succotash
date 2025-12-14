"""Campaign Repository Implementation - Adapter."""

import logging
from typing import List, Optional
from decimal import Decimal

from ...domain.entities import Campaign, CampaignStatus
from ...domain.value_objects import Money, Budget, DateRange, BudgetType
from ...domain.repositories import ICampaignRepository
from ..api.api_client import AdvertisingAPIClient
from ..exceptions import APIException, RepositoryException

logger = logging.getLogger(__name__)


class ApiCampaignRepository(ICampaignRepository):
    """
    Campaign repository implementation using API client.

    This is an ADAPTER that implements the domain PORT (ICampaignRepository).
    """

    def __init__(self, api_client: AdvertisingAPIClient):
        """Initialize with API client."""
        self._api = api_client

    def find_by_id(self, campaign_id: str) -> Optional[Campaign]:
        """Find campaign by ID."""
        try:
            data = self._api.get_campaign(campaign_id)
            return self._map_to_entity(data)
        except APIException as e:
            logger.error(f"API error finding campaign {campaign_id}: {e}")
            raise RepositoryException(f"Failed to find campaign {campaign_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error finding campaign {campaign_id}: {e}")
            raise RepositoryException(f"Unexpected error finding campaign {campaign_id}") from e

    def find_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CampaignStatus] = None
    ) -> List[Campaign]:
        """Find all campaigns."""
        try:
        status_str = status.value if status else None
        response = self._api.get_campaigns(
            page=page,
            page_size=page_size,
            status=status_str
        )

        campaigns_data = response.get('data', [])
        return [self._map_to_entity(c) for c in campaigns_data]
        except APIException as e:
            logger.error(f"API error finding campaigns: {e}")
            raise RepositoryException("Failed to find campaigns") from e
        except Exception as e:
            logger.error(f"Unexpected error finding campaigns: {e}")
            raise RepositoryException("Unexpected error finding campaigns") from e

    def count_all(self, status: Optional[CampaignStatus] = None) -> int:
        """Count all campaigns."""
        try:
        status_str = status.value if status else None
        response = self._api.get_campaigns(page=1, page_size=1, status=status_str)

        pagination = response.get('pagination', {})
        return pagination.get('totalItems', 0)
        except APIException as e:
            logger.error(f"API error counting campaigns: {e}")
            raise RepositoryException("Failed to count campaigns") from e
        except Exception as e:
            logger.error(f"Unexpected error counting campaigns: {e}")
            raise RepositoryException("Unexpected error counting campaigns") from e

    def save(self, campaign: Campaign) -> Campaign:
        """Save (create or update) campaign."""
        try:
        data = self._map_to_api(campaign)

        if self.exists(campaign.id):
            # Update
            response = self._api.update_campaign(campaign.id, data)
        else:
            # Create
            response = self._api.create_campaign(data)

        return self._map_to_entity(response)
        except APIException as e:
            logger.error(f"API error saving campaign {campaign.id}: {e}")
            raise RepositoryException(f"Failed to save campaign {campaign.id}") from e
        except Exception as e:
            logger.error(f"Unexpected error saving campaign {campaign.id}: {e}")
            raise RepositoryException(f"Unexpected error saving campaign {campaign.id}") from e

    def delete(self, campaign_id: str) -> None:
        """Delete campaign."""
        try:
        self._api.delete_campaign(campaign_id)
        except APIException as e:
            logger.error(f"API error deleting campaign {campaign_id}: {e}")
            raise RepositoryException(f"Failed to delete campaign {campaign_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting campaign {campaign_id}: {e}")
            raise RepositoryException(f"Unexpected error deleting campaign {campaign_id}") from e

    def exists(self, campaign_id: str) -> bool:
        """Check if campaign exists."""
        return self.find_by_id(campaign_id) is not None

    @staticmethod
    def _map_to_entity(data: dict) -> Campaign:
        """Map API data to domain entity."""
        # Map budget
        budget_data = data.get('budget', {})
        money = Money(
            Decimal(str(budget_data.get('amount', 0))),
            budget_data.get('currency', 'USD')
        )
        budget_type = BudgetType(budget_data.get('type', 'daily'))
        budget = Budget(money, budget_type)

        # Map date range
        date_range = DateRange.from_strings(
            data.get('start_date', '2025-01-01'),
            data.get('end_date')
        )

        # Map status
        status = CampaignStatus(data.get('status', 'draft'))

        return Campaign(
            id=data['id'],
            name=data['name'],
            status=status,
            budget=budget,
            target_url=data.get('target_url', ''),
            date_range=date_range,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def _map_to_api(campaign: Campaign) -> dict:
        """Map domain entity to API data."""
        return {
            'name': campaign.name,
            'status': campaign.status.value,
            'budget': {
                'amount': campaign.budget.amount.to_float(),
                'currency': campaign.budget.amount.currency,
                'type': campaign.budget.budget_type.value
            },
            'target_url': campaign.target_url,
            'start_date': campaign.date_range.start_date.isoformat(),
            'end_date': campaign.date_range.end_date.isoformat() if campaign.date_range.end_date else None
        }
