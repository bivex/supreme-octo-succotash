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

"""Customer journey entity."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class CustomerJourney:
    """Customer journey tracking entity."""

    id: str
    user_id: str
    campaign_id: Optional[int]
    touchpoints: List[Dict[str, Any]]
    funnel_stage: str  # 'awareness', 'interest', 'consideration', 'purchase', 'retention'
    conversion_events: List[Dict[str, Any]]
    total_value: float
    journey_start: datetime
    last_activity: datetime
    is_converted: bool
    attribution_model: str  # 'first_click', 'last_click', 'linear', etc.
    channel_breakdown: Dict[str, float]  # Percentage attribution by channel

    @classmethod
    def create_from_user(cls, user_id: str, initial_touchpoint: Dict[str, Any]) -> 'CustomerJourney':
        """Create new journey from initial user interaction."""
        import uuid
        from datetime import datetime

        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            campaign_id=initial_touchpoint.get('campaign_id'),
            touchpoints=[initial_touchpoint],
            funnel_stage='awareness',
            conversion_events=[],
            total_value=0.0,
            journey_start=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            is_converted=False,
            attribution_model='last_click',
            channel_breakdown={}
        )

    def add_touchpoint(self, touchpoint: Dict[str, Any]) -> None:
        """Add a new touchpoint to the journey."""
        from datetime import datetime
        self.touchpoints.append(touchpoint)
        self.last_activity = datetime.utcnow()

        # Update funnel stage based on touchpoint
        self._update_funnel_stage(touchpoint)

    def add_conversion(self, conversion_event: Dict[str, Any]) -> None:
        """Add a conversion event to the journey."""
        self.conversion_events.append(conversion_event)
        self.is_converted = True
        self.total_value += conversion_event.get('value', 0)

        # Move to purchase stage
        self.funnel_stage = 'purchase'

    def calculate_attribution(self) -> Dict[str, float]:
        """Calculate attribution for each touchpoint."""
        if not self.touchpoints:
            return {}

        attribution = {}

        if self.attribution_model == 'last_click':
            # Give 100% credit to last touchpoint
            last_touchpoint = self.touchpoints[-1]
            touchpoint_id = last_touchpoint.get('id', str(len(self.touchpoints)))
            attribution[touchpoint_id] = 1.0

        elif self.attribution_model == 'first_click':
            # Give 100% credit to first touchpoint
            first_touchpoint = self.touchpoints[0]
            touchpoint_id = first_touchpoint.get('id', '1')
            attribution[touchpoint_id] = 1.0

        elif self.attribution_model == 'linear':
            # Distribute credit equally
            credit = 1.0 / len(self.touchpoints)
            for i, touchpoint in enumerate(self.touchpoints):
                touchpoint_id = touchpoint.get('id', str(i + 1))
                attribution[touchpoint_id] = credit

        return attribution

    def _update_funnel_stage(self, touchpoint: Dict[str, Any]) -> None:
        """Update funnel stage based on touchpoint characteristics."""
        event_type = touchpoint.get('event_type', '')

        # Define stage progression logic
        stage_progression = {
            'awareness': ['page_view', 'click'],
            'interest': ['time_spent', 'scroll', 'form_start'],
            'consideration': ['form_submit', 'download'],
            'purchase': ['conversion', 'purchase', 'sale'],
            'retention': ['login', 'repeat_visit']
        }

        # Move to next stage if current touchpoint indicates progression
        for stage, events in stage_progression.items():
            if event_type in events:
                # Only progress forward in funnel (don't go backwards)
                stage_order = ['awareness', 'interest', 'consideration', 'purchase', 'retention']
                current_index = stage_order.index(self.funnel_stage)
                new_index = stage_order.index(stage)
                if new_index > current_index:
                    self.funnel_stage = stage
                break
