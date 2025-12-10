"""Goal repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..entities.goal import Goal, GoalType


class GoalRepository(ABC):
    """Abstract base class for goal repositories."""

    @abstractmethod
    def save(self, goal: Goal) -> None:
        """Save a goal."""
        pass

    @abstractmethod
    def get_by_id(self, goal_id: str) -> Optional[Goal]:
        """Get goal by ID."""
        pass

    @abstractmethod
    def get_by_campaign_id(self, campaign_id: int, active_only: bool = True) -> List[Goal]:
        """Get goals by campaign ID."""
        pass

    @abstractmethod
    def get_by_type(self, goal_type: GoalType, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by type, optionally filtered by campaign."""
        pass

    @abstractmethod
    def update_goal(self, goal_id: str, updates: dict) -> Optional[Goal]:
        """Update goal with new data."""
        pass

    @abstractmethod
    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal."""
        pass

    @abstractmethod
    def get_active_goals_for_campaign(self, campaign_id: int) -> List[Goal]:
        """Get all active goals for a campaign, ordered by priority."""
        pass

    @abstractmethod
    def get_goals_by_tag(self, tag: str, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by tag, optionally filtered by campaign."""
        pass
