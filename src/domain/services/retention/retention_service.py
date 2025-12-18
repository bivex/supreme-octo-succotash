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

"""Retention campaign domain service."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from ...entities.retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, UserSegment, RetentionCampaignStatus
from ...entities.click import Click
from ...entities.conversion import Conversion


class RetentionService:
    """Domain service for retention campaign management and churn prediction."""

    def __init__(self):
        pass

    def analyze_user_engagement(self, clicks: List[Click],
                               conversions: List[Conversion],
                               user_id: str) -> UserEngagementProfile:
        """
        Analyze user engagement based on click and conversion history.

        Args:
            clicks: List of user clicks
            conversions: List of user conversions
            user_id: User identifier

        Returns:
            UserEngagementProfile with engagement metrics
        """
        if not clicks:
            # Return minimal profile for users with no activity
            return UserEngagementProfile(
                customer_id=user_id,
                total_sessions=0,
                total_clicks=0,
                total_conversions=0,
                avg_session_duration=0.0,
                last_session_date=datetime.now(),
                engagement_score=0.0,
                segment=UserSegment.LOW_ENGAGEMENT,
                interests=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

        # Calculate engagement metrics
        total_clicks = len(clicks)
        total_conversions = len(conversions)

        # Group clicks by sessions (simplified: clicks within 30 minutes)
        sessions = self._group_clicks_into_sessions(clicks)
        total_sessions = len(sessions)

        # Calculate average session duration
        session_durations = []
        for session_clicks in sessions.values():
            if len(session_clicks) > 1:
                first_click = min(session_clicks, key=lambda x: x.created_at)
                last_click = max(session_clicks, key=lambda x: x.created_at)
                duration_minutes = (last_click.created_at - first_click.created_at).total_seconds() / 60
                session_durations.append(duration_minutes)

        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0.0

        # Calculate engagement score (0-100)
        engagement_score = self._calculate_engagement_score(
            total_sessions, total_clicks, total_conversions, avg_session_duration
        )

        # Determine user segment
        segment = self._determine_user_segment(engagement_score, total_conversions, clicks)

        # Extract interests based on clicked content (simplified)
        interests = self._extract_user_interests(clicks)

        # Get last session date
        last_session_date = max(click.created_at for click in clicks)

        return UserEngagementProfile(
            customer_id=user_id,
            total_sessions=total_sessions,
            total_clicks=total_clicks,
            total_conversions=total_conversions,
            avg_session_duration=avg_session_duration,
            last_session_date=last_session_date,
            engagement_score=engagement_score,
            segment=segment,
            interests=interests,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def predict_churn_risk(self, user_profile: UserEngagementProfile,
                          historical_patterns: List[UserEngagementProfile]) -> ChurnPrediction:
        """
        Predict churn risk based on user profile and historical patterns.

        Uses simple ML-like approach based on engagement patterns.
        """
        # Calculate churn probability based on multiple factors
        churn_probability = 0.0
        reasons = []

        # Factor 1: Days since last activity
        days_inactive = (datetime.now() - user_profile.last_session_date).days
        if days_inactive > 90:
            churn_probability += 0.8
            reasons.append("Inactive for 90+ days")
        elif days_inactive > 60:
            churn_probability += 0.6
            reasons.append("Inactive for 60+ days")
        elif days_inactive > 30:
            churn_probability += 0.4
            reasons.append("Inactive for 30+ days")

        # Factor 2: Low engagement score
        if user_profile.engagement_score < 30:
            churn_probability += 0.3
            reasons.append("Low engagement score")
        elif user_profile.engagement_score < 50:
            churn_probability += 0.2
            reasons.append("Below average engagement")

        # Factor 3: Low conversion rate
        if user_profile.conversion_rate < 0.01:
            churn_probability += 0.2
            reasons.append("Very low conversion rate")

        # Factor 4: Segment-based risk
        if user_profile.segment == UserSegment.AT_RISK:
            churn_probability += 0.3
            reasons.append("At-risk segment")
        elif user_profile.segment == UserSegment.LOW_ENGAGEMENT:
            churn_probability += 0.4
            reasons.append("Low engagement segment")

        # Cap probability at 0.95
        churn_probability = min(churn_probability, 0.95)

        # Determine risk level
        if churn_probability >= 0.7:
            risk_level = "high"
        elif churn_probability >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Predict churn date (simplified)
        predicted_churn_date = None
        if churn_probability > 0.5:
            days_to_churn = int((1 - churn_probability) * 180)  # Up to 6 months
            predicted_churn_date = datetime.now() + timedelta(days=days_to_churn)

        return ChurnPrediction(
            customer_id=user_profile.customer_id,
            churn_probability=churn_probability,
            risk_level=risk_level,
            predicted_churn_date=predicted_churn_date,
            reasons=reasons,
            last_activity_date=user_profile.last_session_date,
            engagement_score=user_profile.engagement_score,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def create_retention_campaigns(self, churn_predictions: List[ChurnPrediction],
                                  user_profiles: List[UserEngagementProfile]) -> List[RetentionCampaign]:
        """
        Create automated retention campaigns based on churn predictions and user profiles.

        Args:
            churn_predictions: List of churn predictions
            user_profiles: List of user engagement profiles

        Returns:
            List of recommended retention campaigns
        """
        campaigns = []

        # Group users by risk level and segment
        high_risk_users = [p for p in churn_predictions if p.risk_level == "high"]
        medium_risk_users = [p for p in churn_predictions if p.risk_level == "medium"]

        # Create high-risk campaign
        if high_risk_users:
            campaign = self._create_targeted_campaign(
                "High-Risk Retention Campaign",
                "Urgent retention campaign for users at high churn risk",
                high_risk_users,
                UserSegment.AT_RISK
            )
            campaigns.append(campaign)

        # Create medium-risk campaign
        if medium_risk_users:
            campaign = self._create_targeted_campaign(
                "Medium-Risk Retention Campaign",
                "Proactive retention campaign for users showing churn signs",
                medium_risk_users,
                UserSegment.ACTIVE_USERS
            )
            campaigns.append(campaign)

        # Create segment-specific campaigns
        segment_groups = defaultdict(list)
        for profile in user_profiles:
            segment_groups[profile.segment].append(profile)

        for segment, profiles in segment_groups.items():
            if segment in [UserSegment.LOW_ENGAGEMENT, UserSegment.AT_RISK] and len(profiles) >= 10:
                campaign = self._create_segment_campaign(segment, profiles)
                campaigns.append(campaign)

        return campaigns

    def optimize_campaign_performance(self, campaign: RetentionCampaign,
                                    performance_data: Dict) -> Dict[str, any]:
        """
        Optimize campaign performance based on A/B testing and performance data.

        Args:
            campaign: Retention campaign to optimize
            performance_data: Performance metrics

        Returns:
            Optimization recommendations
        """
        recommendations = {
            'message_optimization': [],
            'timing_optimization': [],
            'segment_refinement': [],
            'budget_adjustments': []
        }

        # Analyze open rates
        open_rate = performance_data.get('open_rate', 0)
        if open_rate < 0.1:
            recommendations['message_optimization'].append("Subject line needs improvement")
        elif open_rate > 0.3:
            recommendations['message_optimization'].append("Subject line performing well")

        # Analyze click rates
        click_rate = performance_data.get('click_rate', 0)
        if click_rate < 0.02:
            recommendations['message_optimization'].append("Call-to-action needs improvement")
        elif click_rate > 0.1:
            recommendations['message_optimization'].append("Call-to-action highly effective")

        # Analyze timing
        best_hour = performance_data.get('best_send_hour', 10)
        if best_hour != campaign.start_date.hour:
            recommendations['timing_optimization'].append(f"Consider sending at {best_hour}:00")

        # Analyze segment performance
        segment_conversion = performance_data.get('segment_conversion_rate', 0)
        if segment_conversion < 0.01:
            recommendations['segment_refinement'].append("Consider refining target segment")

        return recommendations

    def _group_clicks_into_sessions(self, clicks: List[Click]) -> Dict[str, List[Click]]:
        """Group clicks into sessions based on time proximity."""
        sorted_clicks = sorted(clicks, key=lambda x: x.created_at)
        sessions = {}
        session_id = 0

        for click in sorted_clicks:
            # Check if this click belongs to an existing session
            found_session = False
            for sid, session_clicks in sessions.items():
                last_click_time = max(c.created_at for c in session_clicks)
                if (click.created_at - last_click_time).total_seconds() < 1800:  # 30 minutes
                    sessions[sid].append(click)
                    found_session = True
                    break

            # Create new session if not found
            if not found_session:
                session_id += 1
                sessions[f"session_{session_id}"] = [click]

        return sessions

    def _calculate_engagement_score(self, sessions: int, clicks: int,
                                   conversions: int, avg_duration: float) -> float:
        """Calculate user engagement score (0-100)."""
        score = 0.0

        # Sessions factor (max 30 points)
        if sessions >= 10:
            score += 30
        elif sessions >= 5:
            score += 20
        elif sessions >= 2:
            score += 10
        elif sessions >= 1:
            score += 5

        # Clicks factor (max 25 points)
        if clicks >= 50:
            score += 25
        elif clicks >= 20:
            score += 15
        elif clicks >= 5:
            score += 10
        elif clicks >= 1:
            score += 5

        # Conversions factor (max 30 points)
        if conversions >= 5:
            score += 30
        elif conversions >= 2:
            score += 20
        elif conversions >= 1:
            score += 10

        # Duration factor (max 15 points)
        if avg_duration >= 10:
            score += 15
        elif avg_duration >= 5:
            score += 10
        elif avg_duration >= 2:
            score += 5

        return min(100.0, score)

    def _determine_user_segment(self, engagement_score: float,
                               conversions: int, clicks: List[Click]) -> UserSegment:
        """Determine user segment based on engagement and behavior."""
        if engagement_score >= 70:
            return UserSegment.HIGH_VALUE
        elif engagement_score >= 50:
            return UserSegment.ACTIVE_USERS
        elif conversions > 0:
            return UserSegment.NEW_USERS
        elif engagement_score >= 20:
            return UserSegment.AT_RISK
        else:
            return UserSegment.LOW_ENGAGEMENT

    def _extract_user_interests(self, clicks: List[Click]) -> List[str]:
        """Extract user interests from click patterns (simplified)."""
        interests = set()

        for click in clicks:
            # Extract interests from sub1-sub5 parameters
            for sub in [click.sub1, click.sub2, click.sub3, click.sub4, click.sub5]:
                if sub and len(sub) > 2:
                    # Simple categorization
                    if any(keyword in sub.lower() for keyword in ['tech', 'software', 'app']):
                        interests.add('technology')
                    elif any(keyword in sub.lower() for keyword in ['finance', 'money', 'invest']):
                        interests.add('finance')
                    elif any(keyword in sub.lower() for keyword in ['health', 'fitness', 'medical']):
                        interests.add('health')
                    elif any(keyword in sub.lower() for keyword in ['fashion', 'style', 'clothing']):
                        interests.add('fashion')

        return list(interests)

    def _create_targeted_campaign(self, name: str, description: str,
                                target_users: List[ChurnPrediction],
                                segment: UserSegment) -> RetentionCampaign:
        """Create a targeted retention campaign."""
        from ...entities.retention import RetentionTrigger

        triggers = [
            RetentionTrigger(
                id=f"trigger_{len(target_users)}_inactive",
                type="inactive_days",
                value=30,
                operator=">",
                created_at=datetime.now()
            )
        ]

        return RetentionCampaign(
            id=f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=name,
            description=description,
            target_segment=segment,
            status=RetentionCampaignStatus.DRAFT,
            triggers=triggers,
            message_template="We miss you! Here's a special offer to welcome you back.",
            target_user_count=len(target_users),
            sent_count=0,
            opened_count=0,
            clicked_count=0,
            converted_count=0,
            budget=None,
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=30),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def _create_segment_campaign(self, segment: UserSegment,
                                profiles: List[UserEngagementProfile]) -> RetentionCampaign:
        """Create segment-specific retention campaign."""
        from ...entities.retention import RetentionTrigger

        segment_names = {
            UserSegment.LOW_ENGAGEMENT: "Low Engagement Re-engagement",
            UserSegment.AT_RISK: "At-Risk User Retention",
            UserSegment.NEW_USERS: "New User Onboarding"
        }

        triggers = [
            RetentionTrigger(
                id=f"trigger_{segment.value}_engagement",
                type="low_engagement",
                value=30,
                operator="<",
                created_at=datetime.now()
            )
        ]

        return RetentionCampaign(
            id=f"campaign_{segment.value}_{datetime.now().strftime('%Y%m%d')}",
            name=segment_names.get(segment, f"{segment.value.title()} Campaign"),
            description=f"Automated campaign for {segment.value} users",
            target_segment=segment,
            status=RetentionCampaignStatus.DRAFT,
            triggers=triggers,
            message_template="Personalized message based on user segment",
            target_user_count=len(profiles),
            sent_count=0,
            opened_count=0,
            clicked_count=0,
            converted_count=0,
            budget=None,
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=14),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
