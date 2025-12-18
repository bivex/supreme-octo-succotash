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

"""Event tracking service."""

from datetime import datetime
from typing import Dict, Any, Optional, List

from loguru import logger

from ...entities.event import Event


class EventService:
    """Service for processing and analyzing events."""

    def __init__(self):
        self._valid_event_types = {
            'page_view', 'click', 'form_submit', 'form_start', 'form_complete',
            'scroll', 'time_spent', 'conversion', 'purchase', 'signup',
            'download', 'share', 'search', 'video_play', 'video_complete',
            'custom'
        }

    def validate_event_data(self, event_data: Dict[str, Any]) -> bool:
        """Validate event tracking data."""
        try:
            required_fields = ['event_type', 'event_name']

            for field in required_fields:
                if field not in event_data:
                    logger.warning(f"Missing required field: {field}")
                    return False

            # Validate event type
            if event_data['event_type'] not in self._valid_event_types:
                logger.warning(f"Invalid event type: {event_data['event_type']}")
                return False

            # Validate URLs if provided
            if 'url' in event_data and event_data['url']:
                if not self._is_valid_url(event_data['url']):
                    logger.warning(f"Invalid URL format: {event_data['url']}")
                    return False

            if 'referrer' in event_data and event_data['referrer']:
                if not self._is_valid_url(event_data['referrer']):
                    logger.warning(f"Invalid referrer URL: {event_data['referrer']}")
                    return False

            # Validate campaign/landing page IDs if provided
            if 'campaign_id' in event_data and event_data['campaign_id'] is not None:
                if not isinstance(event_data['campaign_id'], str) or not event_data['campaign_id'].strip():
                    logger.warning(f"Invalid campaign_id: {event_data['campaign_id']}")
                    return False

            if 'landing_page_id' in event_data and event_data['landing_page_id'] is not None:
                if not isinstance(event_data['landing_page_id'], str) or not event_data['landing_page_id'].strip():
                    logger.warning(f"Invalid landing_page_id: {event_data['landing_page_id']}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating event data: {e}")
            return False

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation."""
        if not url or not isinstance(url, str):
            return False

        # Basic checks
        if not (url.startswith('http://') or url.startswith('https://')):
            return False

        if len(url) > 2000:  # Reasonable URL length limit
            return False

        return True

    def enrich_event_data(self, event_data: Dict[str, Any], request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich event data with additional context."""
        enriched = event_data.copy()

        # Add IP address from request
        if 'ip_address' not in enriched and 'ip' in request_context:
            enriched['ip_address'] = request_context['ip']

        # Add user agent from request
        if 'user_agent' not in enriched and 'user_agent' in request_context:
            enriched['user_agent'] = request_context['user_agent']

        # Generate session ID if not provided
        if 'session_id' not in enriched:
            enriched['session_id'] = self._generate_session_id(enriched)

        # Generate user ID if not provided
        if 'user_id' not in enriched:
            enriched['user_id'] = self._generate_user_id(enriched)

        return enriched

    def _generate_session_id(self, event_data: Dict[str, Any]) -> str:
        """Generate session ID based on available data."""
        import hashlib

        # Use IP + User Agent + timestamp for session identification
        components = [
            str(event_data.get('ip_address') or ''),
            str(event_data.get('user_agent') or ''),
            str(datetime.utcnow().date())  # Same session for same day
        ]

        session_hash = hashlib.md5('|'.join(components).encode()).hexdigest()[:16]
        return f"session_{session_hash}"

    def _generate_user_id(self, event_data: Dict[str, Any]) -> str:
        """Generate anonymous user ID."""
        import hashlib

        # Use IP + User Agent for user identification (anonymous)
        components = [
            str(event_data.get('ip_address') or ''),
            str(event_data.get('user_agent') or ''),
        ]

        user_hash = hashlib.md5('|'.join(components).encode()).hexdigest()[:16]
        return f"user_{user_hash}"

    def detect_fraudulent_event(self, event: Event) -> Optional[str]:
        """Detect potentially fraudulent events."""
        # Basic fraud detection rules
        if not event.ip_address:
            return "missing_ip_address"

        if not event.user_agent:
            return "missing_user_agent"

        # Check for suspicious user agents
        suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
        if event.user_agent and any(agent in event.user_agent.lower() for agent in suspicious_agents):
            return "suspicious_user_agent"

        # Check for rapid-fire events (would need more context for this)
        # This is a simplified version

        return None  # No fraud detected

    def categorize_event(self, event: Event) -> List[str]:
        """Categorize event for analytics."""
        categories = []

        # Event type categories
        if event.event_type in ['page_view', 'scroll', 'time_spent']:
            categories.append('engagement')
        elif event.event_type in ['click', 'form_start', 'search']:
            categories.append('interaction')
        elif event.event_type in ['form_submit', 'form_complete', 'conversion', 'purchase', 'signup']:
            categories.append('conversion')
        elif event.event_type in ['video_play', 'video_complete', 'download', 'share']:
            categories.append('content')

        # Custom categories based on event name
        event_name = event.event_name or ''
        if 'button' in event_name.lower():
            categories.append('cta_interaction')
        elif 'form' in event_name.lower():
            categories.append('lead_generation')
        elif 'purchase' in event_name.lower() or 'buy' in event_name.lower():
            categories.append('revenue')

        return categories
