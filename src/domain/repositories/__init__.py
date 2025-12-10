"""Repository interfaces."""

from .campaign_repository import CampaignRepository
from .click_repository import ClickRepository
from .analytics_repository import AnalyticsRepository
from .conversion_repository import ConversionRepository
from .event_repository import EventRepository
from .goal_repository import GoalRepository
from .postback_repository import PostbackRepository
from .webhook_repository import WebhookRepository
from .ltv_repository import LTVRepository

__all__ = [
    'CampaignRepository',
    'ClickRepository',
    'AnalyticsRepository',
    'ConversionRepository',
    'EventRepository',
    'GoalRepository',
    'PostbackRepository',
    'WebhookRepository',
    'LTVRepository'
]
