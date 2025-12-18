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

"""Retention campaign domain entities."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class RetentionCampaignStatus(Enum):
    """Retention campaign status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserSegment(Enum):
    """User segment types for retention."""
    NEW_USERS = "new_users"
    ACTIVE_USERS = "active_users"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    HIGH_VALUE = "high_value"
    LOW_ENGAGEMENT = "low_engagement"


@dataclass
class RetentionTrigger:
    """Trigger condition for retention campaign."""

    id: str
    type: str  # 'inactive_days', 'no_purchase', 'low_engagement'
    value: int  # days, amount, etc.
    operator: str  # '>', '<', '=', '>=', '<='
    created_at: datetime


@dataclass
class RetentionCampaign:
    """Retention campaign entity."""

    id: str
    name: str
    description: str
    target_segment: UserSegment
    status: RetentionCampaignStatus
    triggers: List[RetentionTrigger]
    message_template: str
    target_user_count: int
    sent_count: int
    opened_count: int
    clicked_count: int
    converted_count: int
    budget: Optional[float]
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @property
    def open_rate(self) -> float:
        """Calculate email open rate."""
        return self.opened_count / max(self.sent_count, 1)

    @property
    def click_rate(self) -> float:
        """Calculate click rate."""
        return self.clicked_count / max(self.sent_count, 1)

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        return self.converted_count / max(self.sent_count, 1)

    @property
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        now = datetime.now()
        return (self.status == RetentionCampaignStatus.ACTIVE and
                self.start_date <= now and
                (self.end_date is None or self.end_date >= now))

    @property
    def days_remaining(self) -> Optional[int]:
        """Get days remaining until campaign ends."""
        if self.end_date is None:
            return None
        return max(0, (self.end_date - datetime.now()).days)


@dataclass
class ChurnPrediction:
    """Customer churn prediction."""

    customer_id: str
    churn_probability: float
    risk_level: str  # 'low', 'medium', 'high'
    predicted_churn_date: Optional[datetime]
    reasons: List[str]
    last_activity_date: datetime
    engagement_score: float
    created_at: datetime
    updated_at: datetime

    @property
    def days_since_last_activity(self) -> int:
        """Get days since last activity."""
        return (datetime.now() - self.last_activity_date).days

    @property
    def is_high_risk(self) -> bool:
        """Check if customer is high churn risk."""
        return self.churn_probability >= 0.7

    @property
    def risk_score(self) -> int:
        """Get risk score from 1-10."""
        return min(10, max(1, int(self.churn_probability * 10)))


@dataclass
class UserEngagementProfile:
    """User engagement profile for retention analysis."""

    customer_id: str
    total_sessions: int
    total_clicks: int
    total_conversions: int
    avg_session_duration: float  # minutes
    last_session_date: datetime
    engagement_score: float  # 0-100
    segment: UserSegment
    interests: List[str]
    created_at: datetime
    updated_at: datetime

    @property
    def is_engaged(self) -> bool:
        """Check if user is engaged."""
        return self.engagement_score >= 60

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        return self.total_conversions / max(self.total_clicks, 1)
