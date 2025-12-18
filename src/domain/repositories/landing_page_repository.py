# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Landing page repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.landing_page import LandingPage


class LandingPageRepository(ABC):
    """Abstract base class for landing page repositories."""

    @abstractmethod
    def save(self, landing_page: LandingPage) -> None:
        """Save a landing page."""
        pass

    @abstractmethod
    def find_by_id(self, landing_page_id: str) -> Optional[LandingPage]:
        """Get landing page by ID."""
        pass

    @abstractmethod
    def find_by_campaign_id(self, campaign_id: str) -> List[LandingPage]:
        """Get landing pages by campaign ID."""
        pass

    @abstractmethod
    def update(self, landing_page: LandingPage) -> None:
        """Update a landing page."""
        pass

    @abstractmethod
    def delete_by_id(self, landing_page_id: str) -> bool:
        """Delete landing page by ID."""
        pass

    @abstractmethod
    def exists_by_id(self, landing_page_id: str) -> bool:
        """Check if landing page exists by ID."""
        pass

    @abstractmethod
    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count landing pages by campaign ID."""
        pass