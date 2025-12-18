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

"""Campaign service - legacy wrapper for backward compatibility."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from ...entities.campaign import Campaign
from ...entities.click import Click
from ...value_objects import CampaignStatus

# Import specialized services
from .campaign_validation_service import CampaignValidationService
from .campaign_performance_service import CampaignPerformanceService
from .campaign_lifecycle_service import CampaignLifecycleService


class CampaignService:
    """
    Legacy campaign service for backward compatibility.

    This service delegates to specialized services for better separation of concerns.
    """

    def __init__(self):
        self.validation_service = CampaignValidationService()
        self.performance_service = CampaignPerformanceService()
        self.lifecycle_service = CampaignLifecycleService()

    def can_activate_campaign(self, campaign: Campaign) -> tuple[bool, Optional[str]]:
        """Delegate to validation service."""
        return self.validation_service.can_activate_campaign(campaign)

    def calculate_campaign_performance(self, campaign: Campaign, clicks: List[Click]) -> Dict[str, Any]:
        """Delegate to performance service."""
        return self.performance_service.calculate_campaign_performance(campaign, clicks)

    def should_pause_campaign(self, campaign: Campaign, current_time: Optional[datetime] = None) -> tuple[bool, Optional[str]]:
        """Delegate to lifecycle service."""
        return self.lifecycle_service.should_pause_campaign(campaign, current_time)

    def validate_campaign_budget(self, campaign: Campaign) -> tuple[bool, Optional[str]]:
        """Delegate to validation service."""
        return self.validation_service.validate_campaign_budget(campaign)

    def update_status_from_performance(self, campaign: Campaign,
                                       performance_metrics: Dict[str, Any]) -> CampaignStatus:
        """Delegate to lifecycle service."""
        return self.lifecycle_service.update_status_from_performance(campaign, performance_metrics)
