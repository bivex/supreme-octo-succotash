"""Click Entity."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Click:
    """
    Click Entity.

    Represents a tracked click event.
    """

    # Identity
    id: str
    campaign_id: str

    # Tracking data
    ip_address: str
    user_agent: str
    source: Optional[str] = None
    medium: Optional[str] = None
    utm_campaign: Optional[str] = None

    # Metadata
    created_at: Optional[str] = None

    def __str__(self) -> str:
        return f"Click(id={self.id}, campaign={self.campaign_id})"
