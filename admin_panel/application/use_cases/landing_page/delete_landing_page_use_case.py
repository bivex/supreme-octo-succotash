"""Delete Landing Page Use Case."""

from ....domain.repositories import ILandingPageRepository
from ....domain.exceptions import ValidationError


class DeleteLandingPageUseCase:
    """Use case for deleting a landing page."""

    def __init__(self, landing_page_repository: ILandingPageRepository):
        """Initialize use case with dependencies."""
        self._landing_page_repository = landing_page_repository

    def execute(self, landing_page_id: str) -> None:
        """
        Execute the delete landing page use case.

        Args:
            landing_page_id: ID of the landing page to delete

        Raises:
            ValidationError: If landing page not found
        """
        # Check if landing page exists
        if not self._landing_page_repository.exists(landing_page_id):
            raise ValidationError(f"Landing page with ID {landing_page_id} not found")

        # Delete the landing page
        self._landing_page_repository.delete(landing_page_id)

