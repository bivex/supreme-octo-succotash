"""Get Landing Page Use Case."""

from typing import Optional

from ...dtos import LandingPageDTO
from ....domain.repositories import ILandingPageRepository
from ....domain.exceptions import ValidationError


class GetLandingPageUseCase:
    """Use case for getting a single landing page."""

    def __init__(self, landing_page_repository: ILandingPageRepository):
        """Initialize use case with dependencies."""
        self._landing_page_repository = landing_page_repository

    def execute(self, landing_page_id: str) -> LandingPageDTO:
        """
        Execute the get landing page use case.

        Args:
            landing_page_id: The ID of the landing page to retrieve.

        Returns:
            The landing page as a Data Transfer Object (DTO).

        Raises:
            ValidationError: If the landing page is not found.
        """
        landing_page = self._landing_page_repository.find_by_id(landing_page_id)

        if not landing_page:
            raise ValidationError(f"Landing page with ID {landing_page_id} not found")

        return LandingPageDTO.from_entity(landing_page)
