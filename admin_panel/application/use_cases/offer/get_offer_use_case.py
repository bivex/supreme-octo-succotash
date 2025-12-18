# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Get Offer Use Case."""

from typing import Optional

from ...dtos import OfferDTO
from ....domain.repositories import IOfferRepository
from ....domain.exceptions import ValidationError


class GetOfferUseCase:
    """Use case for getting a single offer."""

    def __init__(self, offer_repository: IOfferRepository):
        """Initialize use case with dependencies."""
        self._offer_repository = offer_repository

    def execute(self, offer_id: str) -> OfferDTO:
        """
        Execute the get offer use case.

        Args:
            offer_id: The ID of the offer to retrieve.

        Returns:
            The offer as a Data Transfer Object (DTO).

        Raises:
            ValidationError: If the offer is not found.
        """
        offer = self._offer_repository.find_by_id(offer_id)

        if not offer:
            raise ValidationError(f"Offer with ID {offer_id} not found")

        return OfferDTO.from_entity(offer)
