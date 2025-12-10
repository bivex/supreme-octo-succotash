"""Create campaign command handler."""

from ..commands.create_campaign_command import CreateCampaignCommand
from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignId, Url


class CreateCampaignHandler:
    """Handler for creating campaigns."""

    def __init__(self, campaign_repository: CampaignRepository):
        self._campaign_repository = campaign_repository

    def handle(self, command: CreateCampaignCommand) -> Campaign:
        """Handle create campaign command."""
        # Convert command data to domain objects
        safe_page_url = Url(command.white_url) if command.white_url else None
        offer_page_url = Url(command.black_url) if command.black_url else None

        # Create campaign entity
        campaign_id = CampaignId.generate()
        campaign_data = {
            'id': campaign_id,
            'name': command.name,
            'description': command.description,
            'cost_model': command.cost_model,
            'payout': command.payout,
            'safe_page_url': safe_page_url,
            'offer_page_url': offer_page_url,
            'daily_budget': command.daily_budget,
            'total_budget': command.total_budget,
            'start_date': command.start_date,
            'end_date': command.end_date,
        }

        campaign = Campaign(**campaign_data)

        # Save to repository
        self._campaign_repository.save(campaign)

        return campaign
