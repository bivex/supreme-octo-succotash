"""API Client Adapter - Infrastructure Layer."""

from typing import Dict, Any, Optional, List
from advertising_platform_sdk import AdvertisingPlatformClient

DEFAULT_API_TIMEOUT_SECONDS = 30.0


class AdvertisingAPIClient:
    """
    Adapter for the Advertising Platform API Client.

    Wraps the SDK client to isolate infrastructure from domain.
    """

    def __init__(
        self,
        base_url: str,
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_API_TIMEOUT_SECONDS
    ):
        """Initialize API client."""
        self._client = AdvertisingPlatformClient(
            base_url=base_url,
            bearer_token=bearer_token,
            api_key=api_key,
            timeout=timeout
        )

    # Health
    def get_health(self) -> Dict[str, Any]:
        """Get API health status."""
        return self._client.get_health()

    # Campaigns
    def get_campaigns(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get campaigns list."""
        return self._client.get_campaigns(
            page=page,
            page_size=page_size,
            status=status
        )

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get single campaign."""
        return self._client.get_campaign(campaign_id)

    def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new campaign."""
        return self._client.create_campaign(data)

    def update_campaign(self, campaign_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update campaign."""
        return self._client.update_campaign(campaign_id, data)

    def delete_campaign(self, campaign_id: str) -> None:
        """Delete campaign."""
        self._client.delete_campaign(campaign_id)

    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause campaign."""
        return self._client.pause_campaign(campaign_id)

    def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Resume campaign."""
        return self._client.resume_campaign(campaign_id)

    # Goals
    def get_goals(
        self,
        campaign_id: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get goals list."""
        return self._client.get_goals(
            campaign_id=campaign_id,
            page=page,
            page_size=page_size
        )

    def get_goal(self, goal_id: str) -> Dict[str, Any]:
        """Get single goal."""
        return self._client.get_goal(goal_id)

    def create_goal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new goal."""
        return self._client.create_goal(data)

    def update_goal(self, goal_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update goal."""
        return self._client.update_goal(goal_id, data)

    def delete_goal(self, goal_id: str) -> None:
        """Delete goal."""
        self._client.delete_goal(goal_id)

    def get_goal_templates(self) -> List[Dict[str, Any]]:
        """Get goal templates."""
        return self._client.get_goal_templates()

    # Analytics
    def get_real_time_analytics(
        self,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get real-time analytics."""
        return self._client.get_real_time_analytics(campaign_id=campaign_id)

    def get_campaign_analytics(
        self,
        campaign_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get campaign analytics."""
        return self._client.get_campaign_analytics(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date
        )

    # Clicks
    def get_clicks(
        self,
        campaign_id: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get clicks list."""
        return self._client.get_clicks(
            campaign_id=campaign_id,
            page=page,
            page_size=page_size
        )

    def generate_click(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate click URL."""
        return self._client.generate_click(data)

    # Conversions
    def track_conversion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track conversion."""
        return self._client.track_conversion(data)

    def close(self) -> None:
        """Close the client."""
        self._client.close()
