"""Presentation routes."""

from .campaign_routes import CampaignRoutes
from .click_routes import ClickRoutes
from .webhook_routes import WebhookRoutes
from .event_routes import EventRoutes
from .conversion_routes import ConversionRoutes
from .postback_routes import PostbackRoutes
from .click_generation_routes import ClickGenerationRoutes
from .goal_routes import GoalRoutes
from .journey_routes import JourneyRoutes
from .ltv_routes import LtvRoutes
from .form_routes import FormRoutes
from .retention_routes import RetentionRoutes

__all__ = [
    'CampaignRoutes',
    'ClickRoutes',
    'WebhookRoutes',
    'EventRoutes',
    'ConversionRoutes',
    'PostbackRoutes',
    'ClickGenerationRoutes',
    'GoalRoutes',
    'JourneyRoutes',
    'LtvRoutes',
    'FormRoutes',
    'RetentionRoutes'
]
