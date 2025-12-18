"""Delete Offer Use Case."""

from ....domain.repositories import IOfferRepository
from ....domain.exceptions import ValidationError


class DeleteOfferUseCase:
    """Use case for deleting an offer."""

    def __init__(self, offer_repository: IOfferRepository):
        """Initialize use case with dependencies."""
        self._offer_repository = offer_repository

    def execute(self, offer_id: str) -> None:
        """
        Execute the delete offer use case.

        Args:
            offer_id: ID of the offer to delete

        Raises:
            ValidationError: If offer not found
        """
        # Check if offer exists
        if not self._offer_repository.exists(offer_id):
            raise ValidationError(f"Offer with ID {offer_id} not found")

        # Delete the offer
        self._offer_repository.delete(offer_id)


