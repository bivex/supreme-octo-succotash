# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Application queries."""

from .get_campaign_query import GetCampaignQuery, GetCampaignHandler
from .get_campaign_analytics_query import GetCampaignAnalyticsQuery, GetCampaignAnalyticsHandler
from .get_campaign_landing_pages_query import GetCampaignLandingPagesQuery, GetCampaignLandingPagesHandler
from .get_campaign_offers_query import GetCampaignOffersQuery, GetCampaignOffersHandler

__all__ = [
    'GetCampaignQuery',
    'GetCampaignHandler',
    'GetCampaignAnalyticsQuery',
    'GetCampaignAnalyticsHandler',
    'GetCampaignLandingPagesQuery',
    'GetCampaignLandingPagesHandler',
    'GetCampaignOffersQuery',
    'GetCampaignOffersHandler'
]
