"""Presentation routes."""

from .campaign_routes import CampaignRoutes
from .click_routes import ClickRoutes
from .webhook_routes import WebhookRoutes
from .event_routes import EventRoutes
from .conversion_routes import ConversionRoutes
from .gaming_webhook_routes import GamingWebhookRoutes
from .postback_routes import PostbackRoutes
from .click_generation_routes import ClickGenerationRoutes
from .goal_routes import GoalRoutes
from .journey_routes import JourneyRoutes
from .ltv_routes import LtvRoutes
from .form_routes import FormRoutes
from .retention_routes import RetentionRoutes
from .bulk_operations_routes import BulkOperationsRoutes
from .fraud_routes import FraudRoutes
from .system_routes import SystemRoutes
from .analytics_routes import AnalyticsRoutes

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
    'RetentionRoutes',
    'BulkOperationsRoutes',
    'FraudRoutes',
    'SystemRoutes',
    'AnalyticsRoutes'
]
