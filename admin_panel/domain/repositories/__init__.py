"""Repository Interfaces - Ports for data persistence."""

from .campaign_repository import ICampaignRepository
from .goal_repository import IGoalRepository
from .analytics_repository import IAnalyticsRepository
from .click_repository import IClickRepository

__all__ = [
    'ICampaignRepository',
    'IGoalRepository',
    'IAnalyticsRepository',
    'IClickRepository'
]
