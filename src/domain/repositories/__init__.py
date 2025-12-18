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

"""Repository interfaces."""

from .campaign_repository import CampaignRepository
from .click_repository import ClickRepository
from .impression_repository import ImpressionRepository
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
    'ImpressionRepository',
    'AnalyticsRepository',
    'ConversionRepository',
    'EventRepository',
    'GoalRepository',
    'PostbackRepository',
    'WebhookRepository',
    'LTVRepository'
]
