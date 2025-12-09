"""Repository interfaces."""

from .campaign_repository import CampaignRepository
from .click_repository import ClickRepository
from .analytics_repository import AnalyticsRepository

__all__ = [
    'CampaignRepository',
    'ClickRepository',
    'AnalyticsRepository'
]
