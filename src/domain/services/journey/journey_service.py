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

"""Customer journey service."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ...entities.journey import CustomerJourney


class JourneyService:
    """Service for customer journey analysis and tracking."""

    def __init__(self):
        self._journeys: Dict[str, CustomerJourney] = {}

    def get_or_create_journey(self, user_id: str, initial_touchpoint: Dict[str, Any]) -> CustomerJourney:
        """Get existing journey or create new one."""
        if user_id in self._journeys:
            return self._journeys[user_id]

        journey = CustomerJourney.create_from_user(user_id, initial_touchpoint)
        self._journeys[user_id] = journey
        return journey

    def create_journey_from_click(self, click_data: Dict[str, Any]) -> CustomerJourney:
        """Create a customer journey from click data."""
        user_id = click_data.get('user_id') or click_data.get('click_id') or str(click_data.get('id', 'unknown'))

        initial_touchpoint = {
            'type': 'click',
            'campaign_id': click_data.get('campaign_id'),
            'source': 'paid',
            'channel': 'affiliate',
            'timestamp': click_data.get('created_at'),
            'metadata': {
                'ip_address': click_data.get('ip_address'),
                'user_agent': click_data.get('user_agent'),
                'referrer': click_data.get('referrer')
            }
        }

        return self.get_or_create_journey(user_id, initial_touchpoint)

    def create_journey_from_impression(self, impression_data: Dict[str, Any]) -> CustomerJourney:
        """Create a customer journey from impression data."""
        user_id = impression_data.get('user_id') or impression_data.get('impression_id') or str(impression_data.get('id', 'unknown'))

        initial_touchpoint = {
            'type': 'impression',
            'campaign_id': impression_data.get('campaign_id'),
            'source': 'paid',
            'channel': 'display',
            'timestamp': impression_data.get('created_at'),
            'metadata': {
                'ip_address': impression_data.get('ip_address'),
                'user_agent': impression_data.get('user_agent'),
                'referrer': impression_data.get('referrer')
            }
        }

        return self.get_or_create_journey(user_id, initial_touchpoint)

    def update_journey(self, user_id: str, touchpoint: Dict[str, Any]) -> Optional[CustomerJourney]:
        """Update customer journey with new touchpoint."""
        if user_id not in self._journeys:
            return None

        journey = self._journeys[user_id]
        journey.add_touchpoint(touchpoint)
        return journey

    def record_conversion(self, user_id: str, conversion_event: Dict[str, Any]) -> Optional[CustomerJourney]:
        """Record conversion in customer journey."""
        if user_id not in self._journeys:
            return None

        journey = self._journeys[user_id]
        journey.add_conversion(conversion_event)
        return journey

    def get_journey(self, user_id: str) -> Optional[CustomerJourney]:
        """Get customer journey by user ID."""
        return self._journeys.get(user_id)

    def get_journey_funnel(self, campaign_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get funnel analysis for journeys."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        relevant_journeys = []
        for journey in self._journeys.values():
            if journey.journey_start >= cutoff_date:
                if campaign_id is None or journey.campaign_id == campaign_id:
                    relevant_journeys.append(journey)

        # Calculate funnel metrics
        funnel = {
            'awareness': 0,
            'interest': 0,
            'consideration': 0,
            'purchase': 0,
            'retention': 0
        }

        for journey in relevant_journeys:
            funnel[journey.funnel_stage] += 1

        # Calculate conversion rates
        total_users = len(relevant_journeys)
        conversion_rates = {}
        if total_users > 0:
            conversion_rates = {
                'awareness_to_interest': funnel['interest'] / total_users if funnel['awareness'] > 0 else 0,
                'interest_to_consideration': funnel['consideration'] / funnel['interest'] if funnel['interest'] > 0 else 0,
                'consideration_to_purchase': funnel['purchase'] / funnel['consideration'] if funnel['consideration'] > 0 else 0,
            }

        return {
            'period_days': days,
            'total_journeys': total_users,
            'funnel_stages': funnel,
            'conversion_rates': conversion_rates
        }

    def get_drop_off_points(self, campaign_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Identify common drop-off points in customer journeys."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        journeys = [
            j for j in self._journeys.values()
            if j.journey_start >= cutoff_date and
            (campaign_id is None or j.campaign_id == campaign_id)
        ]

        # Simple drop-off analysis
        drop_offs = []

        # Check where users drop off before conversion
        unconverted_journeys = [j for j in journeys if not j.is_converted]

        stage_counts = {}
        for journey in unconverted_journeys:
            stage = journey.funnel_stage
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        for stage, count in stage_counts.items():
            if count > 0:
                drop_offs.append({
                    'stage': stage,
                    'users_dropped': count,
                    'percentage': count / len(unconverted_journeys) if unconverted_journeys else 0
                })

        return drop_offs
