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

"""Retention repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

from ..entities.retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, UserSegment


class RetentionRepository(ABC):
    """Abstract repository for retention data access."""

    @abstractmethod
    def save_retention_campaign(self, campaign: RetentionCampaign) -> None:
        """Save retention campaign."""
        pass

    @abstractmethod
    def get_retention_campaign(self, campaign_id: str) -> Optional[RetentionCampaign]:
        """Get retention campaign by ID."""
        pass

    @abstractmethod
    def get_all_retention_campaigns(self, status_filter: Optional[str] = None) -> List[RetentionCampaign]:
        """Get all retention campaigns, optionally filtered by status."""
        pass

    @abstractmethod
    def get_active_retention_campaigns(self) -> List[RetentionCampaign]:
        """Get currently active retention campaigns."""
        pass

    @abstractmethod
    def update_campaign_metrics(self, campaign_id: str, sent_count: int,
                                opened_count: int, clicked_count: int, converted_count: int) -> None:
        """Update campaign performance metrics."""
        pass

    @abstractmethod
    def save_churn_prediction(self, prediction: ChurnPrediction) -> None:
        """Save churn prediction."""
        pass

    @abstractmethod
    def get_churn_prediction(self, customer_id: str) -> Optional[ChurnPrediction]:
        """Get churn prediction for customer."""
        pass

    @abstractmethod
    def get_high_risk_customers(self, limit: int = 100) -> List[ChurnPrediction]:
        """Get customers with high churn risk."""
        pass

    @abstractmethod
    def save_user_engagement_profile(self, profile: UserEngagementProfile) -> None:
        """Save user engagement profile."""
        pass

    @abstractmethod
    def get_user_engagement_profile(self, customer_id: str) -> Optional[UserEngagementProfile]:
        """Get user engagement profile by customer ID."""
        pass

    @abstractmethod
    def get_users_by_segment(self, segment: UserSegment, limit: int = 100) -> List[UserEngagementProfile]:
        """Get users by engagement segment."""
        pass

    @abstractmethod
    def get_retention_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get retention analytics for date range."""
        pass

    @abstractmethod
    def get_campaign_performance_summary(self, campaign_id: str) -> Dict[str, Any]:
        """Get detailed performance summary for a campaign."""
        pass
