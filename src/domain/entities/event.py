"""Event tracking entity."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Event:
    """User event tracking entity."""

    id: str
    event_type: str  # 'page_view', 'click', 'form_submit', 'conversion', etc.
    event_name: str  # Specific event name like 'button_click', 'form_submit'
    user_id: Optional[str]  # Anonymous user identifier
    session_id: Optional[str]  # Session identifier
    click_id: Optional[str]  # Associated click ID if from traffic
    campaign_id: Optional[int]
    landing_page_id: Optional[int]
    url: Optional[str]  # Current page URL
    referrer: Optional[str]  # Referrer URL
    user_agent: Optional[str]
    ip_address: Optional[str]
    properties: Dict[str, Any]  # Custom event properties
    event_data: Optional[Dict[str, Any]]  # Additional event data
    timestamp: datetime

    @classmethod
    def create_from_request(cls, event_data: Dict[str, Any]) -> 'Event':
        """Create event from API request data."""
        import uuid
        from datetime import datetime

        return cls(
            id=str(uuid.uuid4()),
            event_type=event_data.get('event_type', 'custom'),
            event_name=event_data.get('event_name', 'unknown'),
            user_id=event_data.get('user_id'),
            session_id=event_data.get('session_id'),
            click_id=event_data.get('click_id'),
            campaign_id=event_data.get('campaign_id'),
            landing_page_id=event_data.get('landing_page_id'),
            url=event_data.get('url'),
            referrer=event_data.get('referrer'),
            user_agent=event_data.get('user_agent'),
            ip_address=event_data.get('ip_address'),
            properties=event_data.get('properties', {}),
            event_data=event_data.get('event_data'),
            timestamp=datetime.utcnow()
        )
