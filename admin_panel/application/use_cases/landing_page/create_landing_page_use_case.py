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
            dto: Data for creating the landing page

        Returns:
            Created landing page as DTO

        Raises:
            ValidationError: If landing page data is invalid
        """
        # Create value objects
        url = Url(dto.url)

        # Create landing page entity
        landing_page = LandingPage(
            id=self._generate_landing_page_id(),
            campaign_id=dto.campaign_id,
            name=dto.name,
            url=url,
            page_type=dto.page_type,
            weight=dto.weight,
            is_control=dto.is_control
        )

        # Save to repository
        saved_landing_page = self._landing_page_repository.save(landing_page)

        # Return as DTO
        return LandingPageDTO.from_entity(saved_landing_page)

    def _generate_landing_page_id(self) -> str:
        """Generate a unique landing page ID."""
        import uuid
        return str(uuid.uuid4())