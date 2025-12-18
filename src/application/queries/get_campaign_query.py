# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Get campaign query."""

from dataclasses import dataclass
from typing import Optional

from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignId


@dataclass
class GetCampaignQuery:
    """Query to get a campaign by ID."""

    campaign_id: str

    def __post_init__(self) -> None:
        """Validate query data."""
        if not self.campaign_id or not self.campaign_id.strip():
            raise ValueError("Campaign ID is required")


class GetCampaignHandler:
    """Handler for getting campaigns."""

    def __init__(self, campaign_repository: CampaignRepository):
        self._campaign_repository = campaign_repository

    def handle(self, query: GetCampaignQuery) -> Optional[Campaign]:
        """Handle get campaign query."""
        campaign_id = CampaignId.from_string(query.campaign_id)
        return self._campaign_repository.find_by_id(campaign_id)
