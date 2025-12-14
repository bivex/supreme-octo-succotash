"""Update Landing Page Use Case."""

from typing import Optional

from ...dtos import UpdateLandingPageDTO, LandingPageDTO
from ....domain.repositories import ILandingPageRepository
from ....domain.entities import LandingPage
from ....domain.value_objects import Url
from ....domain.exceptions import ValidationError


class UpdateLandingPageUseCase:
    """Use case for updating an existing landing page."""

    def __init__(self, landing_page_repository: ILandingPageRepository):
        """Initialize use case with dependencies."""
        self._landing_page_repository = landing_page_repository

    def execute(self, landing_page_id: str, dto: UpdateLandingPageDTO) -> LandingPageDTO:
        """
        Execute the update landing page use case.

        Args:
            landing_page_id: ID of the landing page to update
            dto: Data for updating the landing page

        Returns:
            Updated landing page as DTO

        Raises:
            ValidationError: If landing page not found or data is invalid
        """
        # Get existing landing page
        landing_page = self._landing_page_repository.find_by_id(landing_page_id)
        if not landing_page:
            raise ValidationError(f"Landing page with ID {landing_page_id} not found")

        # Update fields if provided
        if dto.name is not None:
            landing_page.name = dto.name

        if dto.url is not None:
            landing_page.url = Url(dto.url)

        if dto.page_type is not None:
            landing_page.page_type = dto.page_type

        if dto.weight is not None:
            landing_page.weight = dto.weight

        if dto.is_active is not None:
            landing_page.is_active = dto.is_active

        if dto.is_control is not None:
            landing_page.is_control = dto.is_control

        # Save updated landing page
        saved_landing_page = self._landing_page_repository.save(landing_page)

        # Return as DTO
        return LandingPageDTO.from_entity(saved_landing_page)
