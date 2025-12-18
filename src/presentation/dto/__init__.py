# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:23
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Presentation DTOs."""

from .analytics_dto import GetAnalyticsRequest, AnalyticsResponse
from .campaign_dto import CreateCampaignRequest, CampaignResponse, CampaignSummaryResponse
from .click_dto import TrackClickRequest, ClickResponse

__all__ = [
    'CreateCampaignRequest',
    'CampaignResponse',
    'CampaignSummaryResponse',
    'TrackClickRequest',
    'ClickResponse',
    'GetAnalyticsRequest',
    'AnalyticsResponse'
]
