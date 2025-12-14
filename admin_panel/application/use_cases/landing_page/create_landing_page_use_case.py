"""Create Landing Page Use Case."""

from ...dtos import CreateLandingPageDTO, LandingPageDTO
from ....domain.repositories import ILandingPageRepository
from ....domain.entities import LandingPage
from ....domain.value_objects import Url


class CreateLandingPageUseCase:
    """Use case for creating a new landing page."""

    def __init__(self, landing_page_repository: ILandingPageRepository):
        """Initialize use case with dependencies."""
        self._landing_page_repository = landing_page_repository

    def execute(self, dto: CreateLandingPageDTO) -> LandingPageDTO:
        """
        Execute the create landing page use case.

        Args:
            dto: Data for creating the landing page.

        Returns:
            The created landing page as a Data Transfer Object (DTO).

        Raises:
            ValidationError: If the landing page data is invalid.
        """
        # Create value objects
        url = Url(dto.url)

        # Create landing page entity
        lp_id = self._generate_landing_page_id()
        lp_campaign_id = dto.campaign_id
        lp_name = dto.name
        lp_url = url
        lp_page_type = dto.page_type
        lp_weight = dto.weight
        lp_is_control = dto.is_control

        landing_page = LandingPage(
            id=lp_id,
            campaign_id=lp_campaign_id,
            name=lp_name,
            url=lp_url,
            page_type=lp_page_type,
            weight=lp_weight,
            is_control=lp_is_control
        )

        # Save to repository
        saved_landing_page = self._landing_page_repository.save(landing_page)

        # Return as DTO
        return LandingPageDTO.from_entity(saved_landing_page)

    def _generate_landing_page_id(self) -> str:
        """Generate a unique landing page ID."""
        import uuid
        return str(uuid.uuid4())
