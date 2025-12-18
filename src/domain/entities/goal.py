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

"""Goal management entity."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class GoalType(Enum):
    """Types of conversion goals."""
    LEAD = "lead"
    SALE = "sale"
    SIGNUP = "signup"
    REGISTRATION = "registration"
    DOWNLOAD = "download"
    VIEW = "view"
    TIME_SPENT = "time_spent"
    CUSTOM = "custom"


class GoalTrigger(Enum):
    """How goals are triggered."""
    EVENT = "event"  # Triggered by events (form_submit, purchase, etc.)
    URL = "url"  # Triggered by URL visit
    TIME = "time"  # Triggered by time spent
    MANUAL = "manual"  # Manually triggered via API


@dataclass
class Goal:
    """Conversion goal entity."""

    id: str
    campaign_id: int
    name: str
    description: Optional[str]
    goal_type: GoalType
    trigger_type: GoalTrigger
    trigger_config: Dict[str, Any]  # Configuration for triggering the goal
    value_config: Optional[Dict[str, Any]]  # How to calculate goal value
    is_active: bool
    attribution_window_days: int  # Days to attribute conversions to this goal
    priority: int  # Priority for goal evaluation (higher = more important)
    tags: List[str]  # Tags for categorization
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from_request(cls, goal_data: Dict[str, Any]) -> 'Goal':
        """Create goal from API request data."""
        import uuid
        from datetime import datetime

        return cls(
            id=str(uuid.uuid4()),
            campaign_id=goal_data['campaign_id'],
            name=goal_data['name'],
            description=goal_data.get('description'),
            goal_type=GoalType(goal_data.get('goal_type', 'lead')),
            trigger_type=GoalTrigger(goal_data.get('trigger_type', 'event')),
            trigger_config=goal_data.get('trigger_config', {}),
            value_config=goal_data.get('value_config'),
            is_active=goal_data.get('is_active', True),
            attribution_window_days=goal_data.get('attribution_window_days', 30),
            priority=goal_data.get('priority', 1),
            tags=goal_data.get('tags', []),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def matches_event(self, event_data: Dict[str, Any]) -> bool:
        """Check if an event matches this goal's trigger conditions."""
        if self.trigger_type != GoalTrigger.EVENT:
            return False

        trigger_config = self.trigger_config

        # Check event type match
        if 'event_type' in trigger_config:
            if event_data.get('event_type') != trigger_config['event_type']:
                return False

        # Check event name match
        if 'event_name' in trigger_config:
            if event_data.get('event_name') != trigger_config['event_name']:
                return False

        # Check custom conditions
        if 'conditions' in trigger_config:
            conditions = trigger_config['conditions']
            for condition_key, condition_value in conditions.items():
                if event_data.get(condition_key) != condition_value:
                    return False

        return True

    def matches_url(self, url: str) -> bool:
        """Check if a URL matches this goal's trigger conditions."""
        if self.trigger_type != GoalTrigger.URL:
            return False

        trigger_config = self.trigger_config

        # Check URL pattern match
        if 'url_pattern' in trigger_config:
            import re
            pattern = trigger_config['url_pattern']
            if not re.search(pattern, url, re.IGNORECASE):
                return False

        # Check domain match
        if 'domain' in trigger_config:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.netloc != trigger_config['domain']:
                return False

        return True

    def matches_time_spent(self, time_spent_seconds: int) -> bool:
        """Check if time spent matches this goal's trigger conditions."""
        if self.trigger_type != GoalTrigger.TIME_SPENT:
            return False

        trigger_config = self.trigger_config

        # Check minimum time requirement
        if 'min_seconds' in trigger_config:
            if time_spent_seconds < trigger_config['min_seconds']:
                return False

        # Check maximum time (if specified)
        if 'max_seconds' in trigger_config:
            if time_spent_seconds > trigger_config['max_seconds']:
                return False

        return True

    def calculate_value(self, event_data: Dict[str, Any]) -> Optional[float]:
        """Calculate the monetary value of this goal achievement."""
        if not self.value_config:
            return None

        value_config = self.value_config

        # Fixed value
        if 'fixed_value' in value_config:
            return float(value_config['fixed_value'])

        # Dynamic value from event properties
        if 'value_field' in value_config:
            field_name = value_config['value_field']
            if field_name in event_data:
                try:
                    return float(event_data[field_name])
                except (ValueError, TypeError):
                    pass

        # Revenue calculation
        if 'revenue_field' in value_config:
            field_name = value_config['revenue_field']
            if field_name in event_data and 'properties' in event_data:
                props = event_data['properties']
                if field_name in props:
                    try:
                        return float(props[field_name])
                    except (ValueError, TypeError):
                        pass

        return None
