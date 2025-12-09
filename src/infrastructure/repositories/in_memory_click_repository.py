"""In-memory click repository implementation."""

from typing import Optional, List
from datetime import datetime, timezone, date

from ...domain.entities.click import Click
from ...domain.repositories.click_repository import ClickRepository
from ...domain.value_objects import ClickId


class InMemoryClickRepository(ClickRepository):
    """In-memory implementation of ClickRepository for testing and development."""

    def __init__(self):
        self._clicks: List[Click] = []
        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        """Initialize with mock click data."""
        from ...domain.value_objects import ClickId

        mock_clicks = [
            Click(
                id=ClickId.from_string("123e4567-e89b-12d3-a456-426614174000"),
                campaign_id="camp_123",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                referrer="https://facebook.com/ad/123",
                is_valid=True,
                sub1="fb_ad_15",
                sub2="facebook",
                sub3="adset_12",
                sub4="video1",
                sub5="lookalike78",
                click_id_param="USERCLICK123",
                affiliate_sub="aff_sub_123",
                landing_page_id=456,
                campaign_offer_id=789,
                traffic_source_id=101,
                conversion_type=None,
                created_at=datetime.fromtimestamp(1640995200, tz=timezone.utc),
            ),
            Click(
                id=ClickId.from_string("456e7890-e89b-12d3-a456-426614174001"),
                campaign_id="camp_456",
                ip_address="10.0.0.50",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                referrer="https://google.com/search?q=test",
                is_valid=True,
                sub1="google_search",
                sub2="google",
                sub3="brand_campaign",
                sub4="text_ad",
                sub5="keyword_123",
                click_id_param="GOOGLE_CLICK_456",
                affiliate_sub="network_a",
                affiliate_sub2="sub_a1",
                landing_page_id=457,
                campaign_offer_id=790,
                traffic_source_id=102,
                conversion_type="lead",
                converted_at=datetime.now(timezone.utc),
                created_at=datetime.fromtimestamp(1641081600, tz=timezone.utc),
            )
        ]

        self._clicks.extend(mock_clicks)

    def save(self, click: Click) -> None:
        """Save a click."""
        # Check if click already exists
        existing_index = None
        for i, existing_click in enumerate(self._clicks):
            if existing_click.id == click.id:
                existing_index = i
                break

        if existing_index is not None:
            self._clicks[existing_index] = click
        else:
            self._clicks.append(click)

    def find_by_id(self, click_id: ClickId) -> Optional[Click]:
        """Find click by ID."""
        for click in self._clicks:
            if click.id == click_id:
                return click
        return None

    def find_by_campaign_id(self, campaign_id: str, limit: int = 100,
                           offset: int = 0) -> List[Click]:
        """Find clicks by campaign ID."""
        matching_clicks = [c for c in self._clicks if c.campaign_id == campaign_id]
        # Sort by creation time descending
        matching_clicks.sort(key=lambda x: x.created_at, reverse=True)
        return matching_clicks[offset:offset + limit]

    def find_by_filters(self, filters) -> List[Click]:
        """Find clicks by filter criteria."""
        filtered_clicks = self._clicks.copy()

        if filters.campaign_id is not None:
            filtered_clicks = [c for c in filtered_clicks if c.campaign_id == filters.campaign_id]

        if filters.is_valid is not None:
            filtered_clicks = [c for c in filtered_clicks if c.is_valid == filters.is_valid]

        if filters.start_date is not None:
            filtered_clicks = [c for c in filtered_clicks if c.created_at >= filters.start_date]

        if filters.end_date is not None:
            filtered_clicks = [c for c in filtered_clicks if c.created_at <= filters.end_date]

        # Sort by creation time descending
        filtered_clicks.sort(key=lambda x: x.created_at, reverse=True)
        return filtered_clicks[filters.offset:filters.offset + filters.limit]

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count clicks for a campaign."""
        return len([c for c in self._clicks if c.campaign_id == campaign_id])

    def count_conversions(self, campaign_id: str) -> int:
        """Count conversions for a campaign."""
        return len([c for c in self._clicks
                   if c.campaign_id == campaign_id and c.has_conversion])

    def get_clicks_in_date_range(self, campaign_id: str,
                                start_date: date, end_date: date) -> List[Click]:
        """Get clicks within date range for analytics."""
        start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        return [c for c in self._clicks
                if c.campaign_id == campaign_id
                and start_datetime <= c.created_at <= end_datetime]
