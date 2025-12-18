# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Application handlers."""

from .create_campaign_handler import CreateCampaignHandler
from .update_campaign_handler import UpdateCampaignHandler
from .pause_campaign_handler import PauseCampaignHandler
from .resume_campaign_handler import ResumeCampaignHandler
from .create_landing_page_handler import CreateLandingPageHandler
from .create_offer_handler import CreateOfferHandler
from .track_click_handler import TrackClickHandler
from .process_webhook_handler import ProcessWebhookHandler
from .track_event_handler import TrackEventHandler
from .track_conversion_handler import TrackConversionHandler
from .gaming_webhook_handler import GamingWebhookHandler
from .send_postback_handler import SendPostbackHandler
from .generate_click_handler import GenerateClickHandler
from .manage_goal_handler import ManageGoalHandler
from .analyze_journey_handler import AnalyzeJourneyHandler
from .bulk_click_handler import BulkClickHandler
from .click_validation_handler import ClickValidationHandler
from .fraud_handler import FraudHandler
from .system_handler import SystemHandler
from .analytics_handler import AnalyticsHandler
from .ltv_handler import LTVHandler
from .retention_handler import RetentionHandler
from .form_handler import FormHandler
from .cohort_analysis_handler import CohortAnalysisHandler
from .segmentation_handler import SegmentationHandler

__all__ = [
    'CreateCampaignHandler',
    'UpdateCampaignHandler',
    'PauseCampaignHandler',
    'ResumeCampaignHandler',
    'CreateLandingPageHandler',
    'CreateOfferHandler',
    'TrackClickHandler',
    'ProcessWebhookHandler',
    'TrackEventHandler',
    'TrackConversionHandler',
    'GamingWebhookHandler',
    'SendPostbackHandler',
    'GenerateClickHandler',
    'ManageGoalHandler',
    'AnalyzeJourneyHandler',
    'BulkClickHandler',
    'ClickValidationHandler',
    'FraudHandler',
    'SystemHandler',
    'AnalyticsHandler',
    'LTVHandler',
    'RetentionHandler',
    'FormHandler',
    'CohortAnalysisHandler',
    'SegmentationHandler'
]
