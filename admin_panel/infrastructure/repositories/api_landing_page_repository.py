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

"""Landing Page Repository Implementation - Adapter."""

import logging
from typing import List, Optional

from ...domain.entities import LandingPage
from ...domain.value_objects import Url
from ...domain.repositories import ILandingPageRepository
from ..api.api_client import AdvertisingAPIClient
from ..exceptions import APIException, RepositoryException

logger = logging.getLogger(__name__)


class ApiLandingPageRepository(ILandingPageRepository):
    """
    Landing Page repository implementation using API client.

    This is an ADAPTER that implements the domain PORT (ILandingPageRepository).
    """

    def __init__(self, api_client: AdvertisingAPIClient):
        """Initialize with API client."""
        self._api = api_client

    def find_by_id(self, landing_page_id: str) -> Optional[LandingPage]:
        """Find landing page by ID."""
        try:
            # TODO: Implement when API endpoint is available
            # data = self._api.get_landing_page(landing_page_id)
            # return self._map_to_entity(data)
            logger.debug(f"Landing page {landing_page_id} not found (API not implemented)")
            return None
        except APIException as e:
            logger.error(f"API error finding landing page {landing_page_id}: {e}")
            raise RepositoryException(f"Failed to find landing page {landing_page_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error finding landing page {landing_page_id}: {e}")
            raise RepositoryException(f"Unexpected error finding landing page {landing_page_id}") from e

    def find_by_campaign_id(self, campaign_id: str) -> List[LandingPage]:
        """Find all landing pages for a specific campaign."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_landing_pages(campaign_id=campaign_id)
            # landing_pages_data = response.get('data', [])
            # return [self._map_to_entity(lp) for lp in landing_pages_data]
            logger.debug(f"No landing pages found for campaign {campaign_id} (API not implemented)")
            return []
        except APIException as e:
            logger.error(f"API error finding landing pages for campaign {campaign_id}: {e}")
            raise RepositoryException(f"Failed to find landing pages for campaign {campaign_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error finding landing pages for campaign {campaign_id}: {e}")
            raise RepositoryException(f"Unexpected error finding landing pages for campaign {campaign_id}") from e

    def find_all(
        self,
        page: int = 1,
        page_size: int = 20,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[LandingPage]:
        """Find all landing pages with optional filtering and pagination."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_landing_pages(
            #     page=page,
            #     page_size=page_size,
            #     campaign_id=campaign_id,
            #     is_active=is_active
            # )
            # landing_pages_data = response.get('data', [])
            # return [self._map_to_entity(lp) for lp in landing_pages_data]
            logger.debug("No landing pages found (API not implemented)")
            return []
        except APIException as e:
            logger.error(f"API error finding landing pages: {e}")
            raise RepositoryException("Failed to find landing pages") from e
        except Exception as e:
            logger.error(f"Unexpected error finding landing pages: {e}")
            raise RepositoryException("Unexpected error finding landing pages") from e

    def count_all(
        self,
        campaign_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Count landing pages with optional filters."""
        try:
            # TODO: Implement when API endpoint is available
            # response = self._api.get_landing_pages(
            #     page=1,
            #     page_size=1,
            #     campaign_id=campaign_id,
            #     is_active=is_active
            # )
            # pagination = response.get('pagination', {})
            # return pagination.get('totalItems', 0)
            logger.debug("Count landing pages not implemented (API not available)")
            return 0
        except APIException as e:
            logger.error(f"API error counting landing pages: {e}")
            raise RepositoryException("Failed to count landing pages") from e
        except Exception as e:
            logger.error(f"Unexpected error counting landing pages: {e}")
            raise RepositoryException("Unexpected error counting landing pages") from e

    def save(self, landing_page: LandingPage) -> LandingPage:
        """Save (create or update) a landing page."""
        try:
            data = self._map_to_api(landing_page)

            if self.exists(landing_page.id):
                # Update
                # TODO: Implement when API endpoint is available
                # response = self._api.update_landing_page(landing_page.id, data)
                response = data  # Placeholder
                logger.debug(f"Landing page {landing_page.id} updated (placeholder)")
            else:
                # Create
                # TODO: Implement when API endpoint is available
                # response = self._api.create_landing_page(data)
                response = data  # Placeholder
                logger.debug(f"Landing page {landing_page.id} created (placeholder)")

            return self._map_to_entity(response)
        except APIException as e:
            logger.error(f"API error saving landing page {landing_page.id}: {e}")
            raise RepositoryException(f"Failed to save landing page {landing_page.id}") from e
        except Exception as e:
            logger.error(f"Unexpected error saving landing page {landing_page.id}: {e}")
            raise RepositoryException(f"Unexpected error saving landing page {landing_page.id}") from e

    def delete(self, landing_page_id: str) -> None:
        """Delete a landing page."""
        try:
            # TODO: Implement when API endpoint is available
            # self._api.delete_landing_page(landing_page_id)
            logger.debug(f"Landing page {landing_page_id} deletion not implemented (API not available)")
        except APIException as e:
            logger.error(f"API error deleting landing page {landing_page_id}: {e}")
            raise RepositoryException(f"Failed to delete landing page {landing_page_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting landing page {landing_page_id}: {e}")
            raise RepositoryException(f"Unexpected error deleting landing page {landing_page_id}") from e

    def exists(self, landing_page_id: str) -> bool:
        """Check if a landing page exists."""
        return self.find_by_id(landing_page_id) is not None

    @staticmethod
    def _map_to_entity(data: dict) -> LandingPage:
        """Map API data to domain entity."""
        return LandingPage(
            id=data['id'],
            campaign_id=data['campaign_id'],
            name=data['name'],
            url=Url(data['url']),
            page_type=data['page_type'],
            weight=data.get('weight', 100),
            is_active=data.get('is_active', True),
            is_control=data.get('is_control', False),
            impressions=data.get('impressions', 0),
            clicks=data.get('clicks', 0),
            conversions=data.get('conversions', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def _map_to_api(landing_page: LandingPage) -> dict:
        """Map domain entity to API data."""
        data = {
            'id': landing_page.id,
            'campaign_id': landing_page.campaign_id,
            'name': landing_page.name,
            'url': str(landing_page.url),
            'page_type': landing_page.page_type,
            'weight': landing_page.weight,
            'is_active': landing_page.is_active,
            'is_control': landing_page.is_control,
            'impressions': landing_page.impressions,
            'clicks': landing_page.clicks,
            'conversions': landing_page.conversions
        }

        # Add timestamps if present
        if landing_page.created_at:
            data['created_at'] = landing_page.created_at.isoformat()
        if landing_page.updated_at:
            data['updated_at'] = landing_page.updated_at.isoformat()

        return data