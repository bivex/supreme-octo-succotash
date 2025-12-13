"""Create Offer Use Case."""

from decimal import Decimal
from typing import Optional

from ...dtos import CreateOfferDTO, OfferDTO
from ....domain.repositories import IOfferRepository
from ....domain.entities import Offer
from ....domain.value_objects import Money, Url


class CreateOfferUseCase:
    """Use case for creating a new offer."""

    def __init__(self, offer_repository: IOfferRepository):
        """Initialize use case with dependencies."""
        self._offer_repository = offer_repository

    def execute(self, dto: CreateOfferDTO) -> OfferDTO:
        """
        Execute the create offer use case.

        Args:
            dto: Data for creating the offer

        Returns:
            Created offer as DTO

        Raises:
            ValidationError: If offer data is invalid
        """
        # Create value objects
        url = Url(dto.url)
        payout = Money.from_float(dto.payout_amount, dto.payout_currency)
        cost_per_click = None
        if dto.cost_per_click_amount is not None:
            cost_per_click = Money.from_float(dto.cost_per_click_amount, dto.cost_per_click_currency)

        # Create offer entity
        offer = Offer(
            id=self._generate_offer_id(),
            campaign_id=dto.campaign_id,
            name=dto.name,
            url=url,
            offer_type=dto.offer_type,
            payout=payout,
            revenue_share=Decimal(str(dto.revenue_share)),
            cost_per_click=cost_per_click,
            weight=dto.weight,
            is_control=dto.is_control
        )

        # Save to repository
        saved_offer = self._offer_repository.save(offer)

        # Return as DTO
        return OfferDTO.from_entity(saved_offer)

    def _generate_offer_id(self) -> str:
        """Generate a unique offer ID."""
        import uuid
        return str(uuid.uuid4())