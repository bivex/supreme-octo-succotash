# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:35
# Last Updated: 2025-12-18T12:28:35
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Offer Repository Implementation - Adapter."""

import logging
from typing import List, Optional
from decimal import Decimal

DEFAULT_PAGE_SIZE = 20
COUNT_PAGE_SIZE = 1
DEFAULT_COUNT_PAGE = 1
COUNT_PAGE_SIZE = 1

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
            logger.debug(f"Offer {offer_id} not found (API not implemented)")
            return None
        except APIException as e:
            logger.error(f"API error finding offer {offer_id}: {e}")
            raise RepositoryException(f"Failed to find offer {offer_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error finding offer {offer_id}: {e}")
            raise RepositoryException(f"Unexpected error finding offer {offer_id}") from e

    def find_by_campaign_id(self, campaign_id: str) -> List[Offer]:
        """Find all offers for a specific campaign."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_offers(campaign_id=campaign_id)
            # offers_data = response.get('data', [])
            # return [self._map_to_entity(o) for o in offers_data]
            logger.debug(f"No offers found for campaign {campaign_id} (API not implemented)")
            return []
        except APIException as e:
            logger.error(f"API error finding offers for campaign {campaign_id}: {e}")
            raise RepositoryException(f"Failed to find offers for campaign {campaign_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error finding offers for campaign {campaign_id}: {e}")
            raise RepositoryException(f"Unexpected error finding offers for campaign {campaign_id}") from e

    def find_all(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
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
            logger.debug("No offers found (API not implemented)")
            return []
        except APIException as e:
            logger.error(f"API error finding offers: {e}")
            raise RepositoryException("Failed to find offers") from e
        except Exception as e:
            logger.error(f"Unexpected error finding offers: {e}")
            raise RepositoryException("Unexpected error finding offers") from e

    def count_all(
        self,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Count offers with optional filters."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_offers(
            #     page=DEFAULT_COUNT_PAGE,
            #     page_size=COUNT_PAGE_SIZE,
            #     campaign_id=campaign_id,
            #     is_active=is_active
            # )
            # pagination = response.get('pagination', {})
            # return pagination.get('totalItems', 0)
            logger.debug("Count offers not implemented (API not available)")
            return 0
        except APIException as e:
            logger.error(f"API error counting offers: {e}")
            raise RepositoryException("Failed to count offers") from e
        except Exception as e:
            logger.error(f"Unexpected error counting offers: {e}")
            raise RepositoryException("Unexpected error counting offers") from e

    def save(self, offer: Offer) -> Offer:
        """Save (create or update) an offer."""
        try:
            data = self._map_to_api(offer)

            if self.exists(offer.id):
                # Update
                # TODO: Implement when API endpoint is available
                # response = self._api.update_offer(offer.id, data)
                response = data  # Placeholder
                logger.debug(f"Offer {offer.id} updated (placeholder)")
            else:
                # Create
                # TODO: Implement when API endpoint is available
                # response = self._api.create_offer(data)
                response = data  # Placeholder
                logger.debug(f"Offer {offer.id} created (placeholder)")

            return self._map_to_entity(response)
        except APIException as e:
            logger.error(f"API error saving offer {offer.id}: {e}")
            raise RepositoryException(f"Failed to save offer {offer.id}") from e
        except Exception as e:
            logger.error(f"Unexpected error saving offer {offer.id}: {e}")
            raise RepositoryException(f"Unexpected error saving offer {offer.id}") from e

    def delete(self, offer_id: str) -> None:
        """Delete an offer."""
        try:
            # TODO: Implement when API endpoint is available
            # self._api.delete_offer(offer_id)
            logger.debug(f"Offer {offer_id} deletion not implemented (API not available)")
        except APIException as e:
            logger.error(f"API error deleting offer {offer_id}: {e}")
            raise RepositoryException(f"Failed to delete offer {offer_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting offer {offer_id}: {e}")
            raise RepositoryException(f"Unexpected error deleting offer {offer_id}") from e

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
            revenue=Money.from_float(
                data.get('revenue', {}).get('amount', 0),
                data.get('revenue', {}).get('currency', 'USD')
            ),
            cost=Money.from_float(
                data.get('cost', {}).get('amount', 0),
                data.get('cost', {}).get('currency', 'USD')
            ),
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