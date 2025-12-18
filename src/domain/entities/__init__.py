# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:30
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Domain entities."""

from .campaign import Campaign
from .click import Click
from .conversion import Conversion
from .event import Event
from .form import Lead, FormSubmission, LeadScore, FormValidationRule, LeadStatus, LeadSource
from .goal import Goal
from .impression import Impression
from .journey import CustomerJourney
from .landing_page import LandingPage
from .ltv import Cohort, CustomerLTV, LTVSegment
from .offer import Offer
from .postback import Postback
from .retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, RetentionTrigger, \
    RetentionCampaignStatus, UserSegment
from .webhook import TelegramWebhook

__all__ = [
    'Campaign',
    'Click',
    'Impression',
    'LandingPage',
    'Offer',
    'Conversion',
    'Event',
    'Goal',
    'CustomerJourney',
    'Postback',
    'TelegramWebhook',
    'Cohort',
    'CustomerLTV',
    'LTVSegment',
    'RetentionCampaign',
    'ChurnPrediction',
    'UserEngagementProfile',
    'RetentionTrigger',
    'RetentionCampaignStatus',
    'UserSegment',
    'Lead',
    'FormSubmission',
    'LeadScore',
    'FormValidationRule',
    'LeadStatus',
    'LeadSource'
]
