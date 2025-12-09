"""Goal management service."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from ...entities.goal import Goal, GoalType, GoalTrigger
from ...repositories.goal_repository import GoalRepository


class GoalService:
    """Service for managing conversion goals."""

    def __init__(self, goal_repository: GoalRepository):
        self.goal_repository = goal_repository

    def validate_goal_data(self, goal_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate goal configuration data."""
        try:
            required_fields = ['campaign_id', 'name', 'goal_type', 'trigger_type']

            for field in required_fields:
                if field not in goal_data:
                    return False, f"Missing required field: {field}"

            # Validate goal type
            try:
                GoalType(goal_data['goal_type'])
            except ValueError:
                return False, f"Invalid goal_type: {goal_data['goal_type']}"

            # Validate trigger type
            try:
                GoalTrigger(goal_data['trigger_type'])
            except ValueError:
                return False, f"Invalid trigger_type: {goal_data['trigger_type']}"

            # Validate trigger config based on trigger type
            trigger_type = GoalTrigger(goal_data['trigger_type'])
            trigger_config = goal_data.get('trigger_config', {})

            if trigger_type == GoalTrigger.EVENT:
                if not trigger_config:
                    return False, "trigger_config required for event-based goals"
                # At least event_type or event_name should be specified
                if 'event_type' not in trigger_config and 'event_name' not in trigger_config:
                    return False, "event_type or event_name required in trigger_config for event goals"

            elif trigger_type == GoalTrigger.URL:
                if 'url_pattern' not in trigger_config and 'domain' not in trigger_config:
                    return False, "url_pattern or domain required in trigger_config for URL goals"

            elif trigger_type == GoalTrigger.TIME_SPENT:
                if 'min_seconds' not in trigger_config:
                    return False, "min_seconds required in trigger_config for time-based goals"

            # Validate attribution window
            attribution_window = goal_data.get('attribution_window_days', 30)
            if not isinstance(attribution_window, int) or attribution_window < 1 or attribution_window > 365:
                return False, "attribution_window_days must be between 1 and 365"

            # Validate priority
            priority = goal_data.get('priority', 1)
            if not isinstance(priority, int) or priority < 1 or priority > 100:
                return False, "priority must be between 1 and 100"

            # Validate value config if provided
            value_config = goal_data.get('value_config')
            if value_config:
                if not isinstance(value_config, dict):
                    return False, "value_config must be an object"

                # Should have at least one value calculation method
                value_methods = ['fixed_value', 'value_field', 'revenue_field']
                if not any(method in value_config for method in value_methods):
                    return False, f"value_config must contain one of: {', '.join(value_methods)}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def evaluate_event_against_goals(self, event_data: Dict[str, Any], campaign_id: int) -> List[Dict[str, Any]]:
        """Evaluate an event against all active goals for a campaign."""
        goals = self.goal_repository.get_active_goals_for_campaign(campaign_id)

        matches = []
        for goal in goals:
            if goal.matches_event(event_data):
                goal_value = goal.calculate_value(event_data)
                matches.append({
                    'goal_id': goal.id,
                    'goal_name': goal.name,
                    'goal_type': goal.goal_type.value,
                    'value': goal_value,
                    'attribution_window_days': goal.attribution_window_days,
                    'priority': goal.priority,
                    'tags': goal.tags
                })

        # Sort by priority (highest first)
        matches.sort(key=lambda m: m['priority'], reverse=True)
        return matches

    def evaluate_url_against_goals(self, url: str, campaign_id: int) -> List[Dict[str, Any]]:
        """Evaluate a URL visit against all active goals for a campaign."""
        goals = self.goal_repository.get_active_goals_for_campaign(campaign_id)

        matches = []
        for goal in goals:
            if goal.matches_url(url):
                matches.append({
                    'goal_id': goal.id,
                    'goal_name': goal.name,
                    'goal_type': goal.goal_type.value,
                    'value': None,  # URL goals typically don't have dynamic values
                    'attribution_window_days': goal.attribution_window_days,
                    'priority': goal.priority,
                    'tags': goal.tags
                })

        matches.sort(key=lambda m: m['priority'], reverse=True)
        return matches

    def evaluate_time_spent_against_goals(self, time_spent_seconds: int, campaign_id: int) -> List[Dict[str, Any]]:
        """Evaluate time spent against all active goals for a campaign."""
        goals = self.goal_repository.get_active_goals_for_campaign(campaign_id)

        matches = []
        for goal in goals:
            if goal.matches_time_spent(time_spent_seconds):
                matches.append({
                    'goal_id': goal.id,
                    'goal_name': goal.name,
                    'goal_type': goal.goal_type.value,
                    'value': None,  # Time goals typically don't have monetary values
                    'attribution_window_days': goal.attribution_window_days,
                    'priority': goal.priority,
                    'tags': goal.tags
                })

        matches.sort(key=lambda m: m['priority'], reverse=True)
        return matches

    def get_goal_templates(self) -> List[Dict[str, Any]]:
        """Get predefined goal templates for common use cases."""
        return [
            {
                'name': 'Lead Form Submission',
                'description': 'Track when visitors submit lead capture forms',
                'goal_type': 'lead',
                'trigger_type': 'event',
                'trigger_config': {
                    'event_type': 'form_submit',
                    'event_name': 'lead_form_submit'
                },
                'value_config': {
                    'value_field': 'lead_value'
                },
                'attribution_window_days': 30,
                'tags': ['form', 'lead', 'conversion']
            },
            {
                'name': 'Product Purchase',
                'description': 'Track completed product purchases',
                'goal_type': 'sale',
                'trigger_type': 'event',
                'trigger_config': {
                    'event_type': 'conversion',
                    'event_name': 'purchase_complete'
                },
                'value_config': {
                    'revenue_field': 'revenue'
                },
                'attribution_window_days': 30,
                'tags': ['ecommerce', 'purchase', 'revenue']
            },
            {
                'name': 'Newsletter Signup',
                'description': 'Track newsletter or email list subscriptions',
                'goal_type': 'signup',
                'trigger_type': 'event',
                'trigger_config': {
                    'event_type': 'form_submit',
                    'event_name': 'newsletter_signup'
                },
                'value_config': {
                    'fixed_value': 0.10  # Small value for email marketing
                },
                'attribution_window_days': 30,
                'tags': ['email', 'marketing', 'signup']
            },
            {
                'name': 'Thank You Page Visit',
                'description': 'Track visits to post-conversion thank you pages',
                'goal_type': 'conversion',
                'trigger_type': 'url',
                'trigger_config': {
                    'url_pattern': '/thank-you|/success|/confirmed'
                },
                'value_config': None,
                'attribution_window_days': 30,
                'tags': ['confirmation', 'conversion', 'landing']
            },
            {
                'name': 'High Engagement',
                'description': 'Track visitors who spend significant time on page',
                'goal_type': 'engagement',
                'trigger_type': 'time_spent',
                'trigger_config': {
                    'min_seconds': 180  # 3 minutes
                },
                'value_config': None,
                'attribution_window_days': 7,
                'tags': ['engagement', 'time', 'interest']
            }
        ]

    def calculate_goal_performance(self, goal_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate performance metrics for a specific goal."""
        goal = self.goal_repository.get_by_id(goal_id)
        if not goal:
            return {'error': 'Goal not found'}

        # This would typically query conversion/event repositories
        # For now, return mock performance data
        return {
            'goal_id': goal_id,
            'goal_name': goal.name,
            'achievements': 0,  # Would be calculated from actual data
            'conversion_rate': 0.0,
            'average_value': 0.0,
            'total_value': 0.0,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }

    def duplicate_goal(self, goal_id: str, new_campaign_id: Optional[int] = None) -> Optional[Goal]:
        """Create a duplicate of an existing goal."""
        original_goal = self.goal_repository.get_by_id(goal_id)
        if not original_goal:
            return None

        import uuid
        from datetime import datetime

        # Create duplicate with new ID
        duplicate = Goal(
            id=str(uuid.uuid4()),
            campaign_id=new_campaign_id or original_goal.campaign_id,
            name=f"{original_goal.name} (Copy)",
            description=original_goal.description,
            goal_type=original_goal.goal_type,
            trigger_type=original_goal.trigger_type,
            trigger_config=original_goal.trigger_config.copy(),
            value_config=original_goal.value_config.copy() if original_goal.value_config else None,
            is_active=False,  # Start as inactive
            attribution_window_days=original_goal.attribution_window_days,
            priority=original_goal.priority,
            tags=original_goal.tags.copy(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.goal_repository.save(duplicate)
        return duplicate
