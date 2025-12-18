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

"""In-memory retention repository implementation."""

from collections import defaultdict
from datetime import datetime
from typing import Optional, List, Dict, Any

from ...domain.entities.retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, UserSegment
from ...domain.repositories.retention_repository import RetentionRepository


class InMemoryRetentionRepository(RetentionRepository):
    """In-memory implementation of RetentionRepository for testing and development."""

    def __init__(self):
        self._campaigns: Dict[str, RetentionCampaign] = {}
        self._churn_predictions: Dict[str, ChurnPrediction] = {}
        self._engagement_profiles: Dict[str, UserEngagementProfile] = {}
        self._deleted_campaigns: set[str] = set()

    def save_retention_campaign(self, campaign: RetentionCampaign) -> None:
        """Save retention campaign."""
        self._campaigns[campaign.id] = campaign

    def get_retention_campaign(self, campaign_id: str) -> Optional[RetentionCampaign]:
        """Get retention campaign by ID."""
        if campaign_id in self._deleted_campaigns:
            return None
        return self._campaigns.get(campaign_id)

    def get_all_retention_campaigns(self, status_filter: Optional[str] = None) -> List[RetentionCampaign]:
        """Get all retention campaigns, optionally filtered by status."""
        campaigns = [c for c in self._campaigns.values() if c.id not in self._deleted_campaigns]

        if status_filter:
            campaigns = [c for c in campaigns if c.status.value == status_filter]

        return sorted(campaigns, key=lambda x: x.created_at, reverse=True)

    def get_active_retention_campaigns(self) -> List[RetentionCampaign]:
        """Get currently active retention campaigns."""
        return [c for c in self._campaigns.values()
                if c.id not in self._deleted_campaigns and c.is_active]

    def update_campaign_metrics(self, campaign_id: str, sent_count: int,
                                opened_count: int, clicked_count: int, converted_count: int) -> None:
        """Update campaign performance metrics."""
        if campaign_id in self._campaigns and campaign_id not in self._deleted_campaigns:
            campaign = self._campaigns[campaign_id]
            updated_campaign = RetentionCampaign(
                id=campaign.id,
                name=campaign.name,
                description=campaign.description,
                target_segment=campaign.target_segment,
                status=campaign.status,
                triggers=campaign.triggers,
                message_template=campaign.message_template,
                target_user_count=campaign.target_user_count,
                sent_count=sent_count,
                opened_count=opened_count,
                clicked_count=clicked_count,
                converted_count=converted_count,
                budget=campaign.budget,
                start_date=campaign.start_date,
                end_date=campaign.end_date,
                created_at=campaign.created_at,
                updated_at=datetime.now()
            )
            self._campaigns[campaign_id] = updated_campaign

    def save_churn_prediction(self, prediction: ChurnPrediction) -> None:
        """Save churn prediction."""
        self._churn_predictions[prediction.customer_id] = prediction

    def get_churn_prediction(self, customer_id: str) -> Optional[ChurnPrediction]:
        """Get churn prediction for customer."""
        return self._churn_predictions.get(customer_id)

    def get_high_risk_customers(self, limit: int = 100) -> List[ChurnPrediction]:
        """Get customers with high churn risk."""
        high_risk = [p for p in self._churn_predictions.values() if p.risk_level == "high"]
        return sorted(high_risk, key=lambda x: x.churn_probability, reverse=True)[:limit]

    def save_user_engagement_profile(self, profile: UserEngagementProfile) -> None:
        """Save user engagement profile."""
        self._engagement_profiles[profile.customer_id] = profile

    def get_user_engagement_profile(self, customer_id: str) -> Optional[UserEngagementProfile]:
        """Get user engagement profile by customer ID."""
        return self._engagement_profiles.get(customer_id)

    def get_users_by_segment(self, segment: UserSegment, limit: int = 100) -> List[UserEngagementProfile]:
        """Get users by engagement segment."""
        matching_profiles = [p for p in self._engagement_profiles.values() if p.segment == segment]
        return sorted(matching_profiles, key=lambda x: x.engagement_score, reverse=True)[:limit]

    def get_retention_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get retention analytics for date range."""
        # Filter campaigns within date range
        relevant_campaigns = [
            c for c in self._campaigns.values()
            if c.created_at >= start_date and c.created_at <= end_date
        ]

        # Calculate metrics
        total_campaigns = len(relevant_campaigns)
        active_campaigns = len([c for c in relevant_campaigns if c.is_active])
        total_sent = sum(c.sent_count for c in relevant_campaigns)
        total_opened = sum(c.opened_count for c in relevant_campaigns)
        total_clicked = sum(c.clicked_count for c in relevant_campaigns)
        total_converted = sum(c.converted_count for c in relevant_campaigns)

        # Calculate rates
        open_rate = total_opened / max(total_sent, 1)
        click_rate = total_clicked / max(total_sent, 1)
        conversion_rate = total_converted / max(total_sent, 1)

        # Churn risk distribution
        risk_distribution = defaultdict(int)
        for prediction in self._churn_predictions.values():
            if prediction.created_at >= start_date and prediction.created_at <= end_date:
                risk_distribution[prediction.risk_level] += 1

        return {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'campaign_metrics': {
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_sent': total_sent,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'total_converted': total_converted,
                'open_rate': open_rate,
                'click_rate': click_rate,
                'conversion_rate': conversion_rate
            },
            'churn_risk_distribution': dict(risk_distribution),
            'segment_distribution': self._get_segment_distribution()
        }

    def get_campaign_performance_summary(self, campaign_id: str) -> Dict[str, Any]:
        """Get detailed performance summary for a campaign."""
        campaign = self.get_retention_campaign(campaign_id)
        if not campaign:
            return {}

        return {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'status': campaign.status.value,
            'target_segment': campaign.target_segment.value,
            'metrics': {
                'target_user_count': campaign.target_user_count,
                'sent_count': campaign.sent_count,
                'opened_count': campaign.opened_count,
                'clicked_count': campaign.clicked_count,
                'converted_count': campaign.converted_count,
                'open_rate': campaign.open_rate,
                'click_rate': campaign.click_rate,
                'conversion_rate': campaign.conversion_rate
            },
            'budget': campaign.budget,
            'dates': {
                'start_date': campaign.start_date.isoformat() if campaign.start_date else None,
                'end_date': campaign.end_date.isoformat() if campaign.end_date else None,
                'days_remaining': campaign.days_remaining
            }
        }

    def _get_segment_distribution(self) -> Dict[str, int]:
        """Get distribution of users by segment."""
        distribution = defaultdict(int)
        for profile in self._engagement_profiles.values():
            distribution[profile.segment.value] += 1
        return dict(distribution)
