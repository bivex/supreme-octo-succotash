"""Offer Repository Implementation - Adapter."""

import logging
from typing import List, Optional
from decimal import Decimal

from ...domain.entities import Offer
from ...domain.value_objects import Money, Url
from ...domain.repositories import IOfferRepository
from ...domain.exceptions import EntityNotFoundError
from ..api.api_client import AdvertisingAPIClient
from ..exceptions import APIException, RepositoryException

logger = logging.getLogger(__name__)


class ApiOfferRepository(IOfferRepository):
    """
    Offer repository implementation using API client.

    This is an ADAPTER that implements the domain PORT (IOfferRepository).
    """

    def __init__(self, api_client: AdvertisingAPIClient):
        """Initialize with API client."""
        self._api = api_client

    def find_by_id(self, offer_id: str) -> Optional[Offer]:
        """Find offer by ID."""
        try:
            # TODO: Implement when API endpoint is available
            # data = self._api.get_offer(offer_id)
            # return self._map_to_entity(data)
            return None
        except Exception:
            return None

    def find_by_campaign_id(self, campaign_id: str) -> List[Offer]:
        """Find all offers for a specific campaign."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_offers(campaign_id=campaign_id)
            # offers_data = response.get('data', [])
            # return [self._map_to_entity(o) for o in offers_data]
            return []
        except Exception:
            return []

    def find_all(
        self,
        page: int = 1,
        page_size: int = 20,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Offer]:
        """Find all offers with optional filtering and pagination."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_offers(
            #     page=page,
            #     page_size=page_size,
            #     campaign_id=campaign_id,
            #     is_active=is_active
            # )
            # offers_data = response.get('data', [])
            # return [self._map_to_entity(o) for o in offers_data]
            return []
        except Exception:
            return []

    def count_all(
        self,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Count offers with optional filters."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_offers(
            #     page=1,
            #     page_size=1,
            #     campaign_id=campaign_id,
            #     is_active=is_active
            # )
            # pagination = response.get('pagination', {})
            # return pagination.get('totalItems', 0)
            return 0
        except Exception:
            return 0

    def save(self, offer: Offer) -> Offer:
        """Save (create or update) an offer."""
        try:
            data = self._map_to_api(offer)

            if self.exists(offer.id):
                # Update
                # TODO: Implement when API endpoint is available
                # response = self._api.update_offer(offer.id, data)
                response = data  # Placeholder
            else:
                # Create
                # TODO: Implement when API endpoint is available
                # response = self._api.create_offer(data)
                response = data  # Placeholder

            return self._map_to_entity(response)
        except Exception:
            # For now, return the offer as-is (in-memory operation)
            return offer

    def delete(self, offer_id: str) -> None:
        """Delete an offer."""
        try:
            # TODO: Implement when API endpoint is available
            # self._api.delete_offer(offer_id)
            pass
        except Exception:
            pass

    def exists(self, offer_id: str) -> bool:
        """Check if an offer exists."""
        return self.find_by_id(offer_id) is not None

    @staticmethod
    def _map_to_entity(data: dict) -> Offer:
        """Map API data to domain entity."""
        # Parse payout
        payout_data = data.get('payout', {})
        payout = Money(
            Decimal(str(payout_data.get('amount', 0))),
            payout_data.get('currency', 'USD')
        )

        # Parse cost per click
        cost_per_click = None
        if data.get('cost_per_click'):
            cpc_data = data['cost_per_click']
            cost_per_click = Money(
                Decimal(str(cpc_data.get('amount', 0))),
                cpc_data.get('currency', 'USD')
            )

        # Parse revenue share
        revenue_share = Decimal(str(data.get('revenue_share', 0)))

        return Offer(
            id=data['id'],
            campaign_id=data['campaign_id'],
            name=data['name'],
            url=Url(data['url']),
            offer_type=data['offer_type'],
            payout=payout,
            revenue_share=revenue_share,
            cost_per_click=cost_per_click,
            weight=data.get('weight', 100),
            is_active=data.get('is_active', True),
            is_control=data.get('is_control', False),
            clicks=data.get('clicks', 0),
            conversions=data.get('conversions', 0),
            revenue=Money.from_float(data.get('revenue', {}).get('amount', 0),
                                   data.get('revenue', {}).get('currency', 'USD')),
            cost=Money.from_float(data.get('cost', {}).get('amount', 0),
                                data.get('cost', {}).get('currency', 'USD')),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def _map_to_api(offer: Offer) -> dict:
        """Map domain entity to API data."""
        data = {
            'id': offer.id,
            'campaign_id': offer.campaign_id,
            'name': offer.name,
            'url': str(offer.url),
            'offer_type': offer.offer_type,
            'payout': {
                'amount': float(offer.payout.amount),
                'currency': offer.payout.currency
            },
            'revenue_share': float(offer.revenue_share),
            'weight': offer.weight,
            'is_active': offer.is_active,
            'is_control': offer.is_control,
            'clicks': offer.clicks,
            'conversions': offer.conversions,
            'revenue': {
                'amount': float(offer.revenue.amount),
                'currency': offer.revenue.currency
            },
            'cost': {
                'amount': float(offer.cost.amount),
                'currency': offer.cost.currency
            }
        }

        # Add cost per click if present
        if offer.cost_per_click:
            data['cost_per_click'] = {
                'amount': float(offer.cost_per_click.amount),
                'currency': offer.cost_per_click.currency
            }

        # Add timestamps if present
        if offer.created_at:
            data['created_at'] = offer.created_at.isoformat()
        if offer.updated_at:
            data['updated_at'] = offer.updated_at.isoformat()

        return data