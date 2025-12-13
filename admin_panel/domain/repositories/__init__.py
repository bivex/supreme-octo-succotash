"""Repository Interfaces - Ports for data persistence."""

from .campaign_repository import ICampaignRepository
from .goal_repository import IGoalRepository
from .analytics_repository import IAnalyticsRepository
from .click_repository import IClickRepository
from .offer_repository import IOfferRepository
from .landing_page_repository import ILandingPageRepository

__all__ = [
    'ICampaignRepository',
    'IGoalRepository',
    'IAnalyticsRepository',
    'IClickRepository',
    'IOfferRepository',
    'ILandingPageRepository'
]
