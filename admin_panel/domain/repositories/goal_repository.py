"""Goal Repository Interface - Port."""

from abc import ABC, abstractmethod
from typing import List, Optional

DEFAULT_PAGE_SIZE = 20

from ..entities import Goal


class IGoalRepository(ABC):
    """Goal Repository Interface."""

    @abstractmethod
    def find_by_id(self, goal_id: str) -> Optional[Goal]:
        """Find a goal by its ID."""
        pass

    @abstractmethod
    def find_by_campaign(self, campaign_id: str) -> List[Goal]:
        """Find all goals for a campaign."""
        pass

    @abstractmethod
    def find_all(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> List[Goal]:
        """Find all goals with pagination."""
        pass

    @abstractmethod
    def save(self, goal: Goal) -> Goal:
        """Save (create or update) a goal."""
        pass

    @abstractmethod
    def delete(self, goal_id: str) -> None:
        """Delete a goal by ID."""
        pass

    @abstractmethod
    def get_templates(self) -> List[dict]:
        """Get available goal templates."""
        pass
