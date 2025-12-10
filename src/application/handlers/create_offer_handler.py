"""Create offer command handler."""

from ..commands.create_offer_command import CreateOfferCommand
from ...domain.entities.offer import Offer
from ...domain.repositories.offer_repository import OfferRepository


class CreateOfferHandler:
    """Handler for creating offers."""

    def __init__(self, offer_repository: OfferRepository):
        self._offer_repository = offer_repository

    def handle(self, command: CreateOfferCommand) -> Offer:
        """
        Handle create offer command.

        Args:
            command: Create offer command

        Returns:
            Created offer entity
        """
        # Generate ID
        import uuid
        offer_id = f"offer_{str(uuid.uuid4())[:8]}"

        # Create offer entity
        offer = Offer(
            id=offer_id,
            campaign_id=command.campaign_id,
            name=command.name,
            url=command.url,
            offer_type=command.offer_type,
            payout=command.payout,
            revenue_share=command.revenue_share,
            cost_per_click=command.cost_per_click,
            weight=command.weight,
            is_control=command.is_control
        )

        # Save to repository
        self._offer_repository.save(offer)

        return offer
