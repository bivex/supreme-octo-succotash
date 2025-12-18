# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:33
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Infrastructure repository implementations."""

from .in_memory_analytics_repository import InMemoryAnalyticsRepository
from .in_memory_campaign_repository import InMemoryCampaignRepository
from .in_memory_click_repository import InMemoryClickRepository
from .in_memory_conversion_repository import InMemoryConversionRepository
from .in_memory_event_repository import InMemoryEventRepository
from .in_memory_form_repository import InMemoryFormRepository
from .in_memory_goal_repository import InMemoryGoalRepository
from .in_memory_postback_repository import InMemoryPostbackRepository
from .in_memory_retention_repository import InMemoryRetentionRepository
from .in_memory_webhook_repository import InMemoryWebhookRepository
from .postgres_analytics_repository import PostgresAnalyticsRepository
from .postgres_campaign_repository import PostgresCampaignRepository
from .postgres_click_repository import PostgresClickRepository
from .postgres_conversion_repository import PostgresConversionRepository
from .postgres_customer_ltv_repository import PostgresCustomerLtvRepository
from .postgres_event_repository import PostgresEventRepository
from .postgres_form_repository import PostgresFormRepository
from .postgres_goal_repository import PostgresGoalRepository
from .postgres_impression_repository import PostgresImpressionRepository
from .postgres_landing_page_repository import PostgresLandingPageRepository
from .postgres_ltv_repository import PostgresLTVRepository
from .postgres_offer_repository import PostgresOfferRepository
from .postgres_postback_repository import PostgresPostbackRepository
from .postgres_pre_click_data_repository import PostgresPreClickDataRepository
from .postgres_retention_repository import PostgresRetentionRepository
from .postgres_webhook_repository import PostgresWebhookRepository
from .sqlite_analytics_repository import SQLiteAnalyticsRepository
from .sqlite_campaign_repository import SQLiteCampaignRepository
from .sqlite_click_repository import SQLiteClickRepository
from .sqlite_conversion_repository import SQLiteConversionRepository
from .sqlite_event_repository import SQLiteEventRepository
from .sqlite_form_repository import SQLiteFormRepository
from .sqlite_goal_repository import SQLiteGoalRepository
from .sqlite_ltv_repository import SQLiteLTVRepository
from .sqlite_postback_repository import SQLitePostbackRepository
from .sqlite_retention_repository import SQLiteRetentionRepository
from .sqlite_webhook_repository import SQLiteWebhookRepository

__all__ = [
    'InMemoryCampaignRepository',
    'InMemoryClickRepository',
    'InMemoryAnalyticsRepository',
    'InMemoryWebhookRepository',
    'InMemoryEventRepository',
    'InMemoryConversionRepository',
    'InMemoryPostbackRepository',
    'InMemoryGoalRepository',
    'InMemoryRetentionRepository',
    'InMemoryFormRepository',
    'SQLiteCampaignRepository',
    'SQLiteClickRepository',
    'SQLiteAnalyticsRepository',
    'SQLiteWebhookRepository',
    'SQLiteEventRepository',
    'SQLiteConversionRepository',
    'SQLitePostbackRepository',
    'SQLiteGoalRepository',
    'SQLiteLTVRepository',
    'SQLiteRetentionRepository',
    'SQLiteFormRepository',
    'PostgresCampaignRepository',
    'PostgresClickRepository',
    'PostgresImpressionRepository',
    'PostgresAnalyticsRepository',
    'PostgresWebhookRepository',
    'PostgresEventRepository',
    'PostgresConversionRepository',
    'PostgresPostbackRepository',
    'PostgresGoalRepository',
    'PostgresLandingPageRepository',
    'PostgresOfferRepository',
    'PostgresPreClickDataRepository',
    'PostgresLTVRepository',
    'PostgresRetentionRepository',
    'PostgresFormRepository'
]
