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
