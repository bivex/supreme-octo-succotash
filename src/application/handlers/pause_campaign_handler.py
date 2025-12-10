"""Pause campaign command handler."""

from ..commands.pause_campaign_command import PauseCampaignCommand
from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignStatus


class PauseCampaignHandler:
    """Handler for pausing campaigns."""

    def __init__(self, campaign_repository: CampaignRepository):
        self._campaign_repository = campaign_repository

    def handle(self, command: PauseCampaignCommand) -> Campaign:
        """
        Handle pause campaign command.

        Args:
            command: Pause campaign command

        Returns:
            Paused campaign entity

        Raises:
            ValueError: If campaign not found or cannot be paused
        """
        # Get existing campaign
        campaign = self._campaign_repository.find_by_id(command.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign with ID {command.campaign_id.value} not found")

        # Check if campaign can be paused
        if campaign.status == CampaignStatus.PAUSED:
            raise ValueError(f"Campaign {command.campaign_id.value} is already paused")

        if campaign.status == CampaignStatus.COMPLETED:
            raise ValueError(f"Cannot pause completed campaign {command.campaign_id.value}")

        if campaign.status == CampaignStatus.CANCELLED:
            raise ValueError(f"Cannot pause cancelled campaign {command.campaign_id.value}")

        # Update status
        campaign.status = CampaignStatus.PAUSED

        # Update timestamp
        from datetime import datetime, timezone
        campaign.updated_at = datetime.now(timezone.utc)

        # Save updated campaign
        self._campaign_repository.save(campaign)

        return campaign
