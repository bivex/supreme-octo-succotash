# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Resume campaign command handler."""

from ..commands.resume_campaign_command import ResumeCampaignCommand
from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignStatus


class ResumeCampaignHandler:
    """Handler for resuming campaigns."""

    def __init__(self, campaign_repository: CampaignRepository):
        self._campaign_repository = campaign_repository

    def handle(self, command: ResumeCampaignCommand) -> Campaign:
        """
        Handle resume campaign command.

        Args:
            command: Resume campaign command

        Returns:
            Resumed campaign entity

        Raises:
            ValueError: If campaign not found or cannot be resumed
        """
        # Get existing campaign
        campaign = self._campaign_repository.find_by_id(command.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign with ID {command.campaign_id.value} not found")

        # Check if campaign can be resumed
        if campaign.status != CampaignStatus.PAUSED:
            raise ValueError(
                f"Campaign {command.campaign_id.value} is not paused (current status: {campaign.status.value})")

        # Update status to active
        campaign.status = CampaignStatus.ACTIVE

        # Update timestamp
        from datetime import datetime, timezone
        campaign.updated_at = datetime.now(timezone.utc)

        # Save updated campaign
        self._campaign_repository.save(campaign)

        return campaign
