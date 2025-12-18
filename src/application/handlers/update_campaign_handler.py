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

"""Update campaign command handler."""

from loguru import logger

from ..commands.update_campaign_command import UpdateCampaignCommand
from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository


class UpdateCampaignHandler:
    """Handler for updating campaigns."""

    def __init__(self, campaign_repository: CampaignRepository):
        self._campaign_repository = campaign_repository

    async def handle(self, command: UpdateCampaignCommand) -> Campaign:
        """
        Handle update campaign command.

        Args:
            command: Update campaign command

        Returns:
            Updated campaign entity

        Raises:
            ValueError: If campaign not found
        """
        # Get existing campaign
        campaign = self._campaign_repository.find_by_id(command.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign with ID {command.campaign_id.value} not found")

        logger.info(
            f"DEBUG: UpdateCampaignCommand received for campaign {command.campaign_id.value}. safe_page_url: {command.safe_page_url}, offer_page_url: {command.offer_page_url}")

        # Update fields if provided
        if command.name is not None:
            campaign.name = command.name
        if command.description is not None:
            campaign.description = command.description
        if command.cost_model is not None:
            campaign.cost_model = command.cost_model
        if command.payout is not None:
            campaign.payout = command.payout
        if command.safe_page_url is not None:
            campaign.safe_page_url = command.safe_page_url
        if command.offer_page_url is not None:
            campaign.offer_page_url = command.offer_page_url
        if command.daily_budget is not None:
            campaign.daily_budget = command.daily_budget
        if command.total_budget is not None:
            campaign.total_budget = command.total_budget
        if command.start_date is not None:
            campaign.start_date = command.start_date
        if command.end_date is not None:
            campaign.end_date = command.end_date

        logger.info(
            f"DEBUG: Campaign object before save for {campaign.id.value}. safe_page_url: {campaign.safe_page_url}, offer_page_url: {campaign.offer_page_url}")

        # Update timestamp
        from datetime import datetime, timezone
        campaign.updated_at = datetime.now(timezone.utc)

        # Save updated campaign
        self._campaign_repository.save(campaign)

        return campaign
