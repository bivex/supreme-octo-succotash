"""Update Offer Use Case."""

from decimal import Decimal
from typing import Optional

from ...dtos import UpdateOfferDTO, OfferDTO
from ....domain.repositories import IOfferRepository
from ....domain.entities import Offer
from ....domain.value_objects import Money, Url
from ....domain.exceptions import ValidationError


class UpdateOfferUseCase:
    """Use case for updating an existing offer."""

    def __init__(self, offer_repository: IOfferRepository):
        """Initialize use case with dependencies."""
        self._offer_repository = offer_repository

    def _update_offer_fields(self, offer: Offer, dto: UpdateOfferDTO) -> None:
        if dto.name is not None:
            offer.name = dto.name

        if dto.url is not None:
            offer.url = Url(dto.url)

        if dto.offer_type is not None:
            offer.offer_type = dto.offer_type

        if dto.payout_amount is not None:
            currency = dto.payout_currency or offer.payout.currency
            offer.payout = Money.from_float(dto.payout_amount, currency)

        if dto.revenue_share is not None:
            offer.revenue_share = Decimal(str(dto.revenue_share))

        if dto.cost_per_click_amount is not None:
            cost_per_click_currency = offer.payout.currency
            if offer.cost_per_click:
                cost_per_click_currency = offer.cost_per_click.currency
            currency = dto.cost_per_click_currency or cost_per_click_currency
            offer.cost_per_click = Money.from_float(dto.cost_per_click_amount, currency)
        elif dto.cost_per_click_amount == 0:  # Explicitly set to None
            offer.cost_per_click = None

        if dto.weight is not None:
            offer.weight = dto.weight

        if dto.is_active is not None:
            offer.is_active = dto.is_active

        if dto.is_control is not None:
            offer.is_control = dto.is_control

    def execute(self, offer_id: str, dto: UpdateOfferDTO) -> OfferDTO:
        """
        Execute the update offer use case.

        Args:
            offer_id: The ID of the offer to be updated.
            dto: Data Transfer Object containing the updated offer information.

        Returns:
            The updated offer as a Data Transfer Object (DTO).

        Raises:
            ValidationError: If the offer is not found or the provided data is invalid.
        """
        # Get existing offer
        offer = self._offer_repository.find_by_id(offer_id)
        if not offer:
            raise ValidationError(f"Offer with ID {offer_id} not found")

        # Update fields if provided
        self._update_offer_fields(offer, dto)

        # Save updated offer
        saved_offer = self._offer_repository.save(offer)

        # Return as DTO
        return OfferDTO.from_entity(saved_offer)
