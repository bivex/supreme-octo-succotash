"""In-memory campaign repository implementation."""

from typing import Optional, List, Dict
from datetime import datetime, timezone

from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignId, Money, Url


class InMemoryCampaignRepository(CampaignRepository):
    """In-memory implementation of CampaignRepository for testing and development."""

    def __init__(self):
        self._campaigns: Dict[str, Campaign] = {}
        self._deleted_campaigns: set[str] = set()
        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        """Initialize with mock campaign data."""
        # Create mock campaigns
        mock_campaigns = [
            Campaign(
                id=CampaignId.from_string("camp_123"),
                name="Summer Sale Campaign",
                description="High-converting summer promotion",
                status="active",
                cost_model="CPA",
                payout=Money.from_float(25.50, "USD"),
                safe_page_url=Url("https://example.com/safe-landing"),
                offer_page_url=Url("https://example.com/offer"),
                daily_budget=Money.from_float(500.00, "USD"),
                total_budget=Money.from_float(15000.00, "USD"),
                start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
                end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
                clicks_count=5000,
                conversions_count=150,
                spent_amount=Money.from_float(1250.75, "USD"),
                created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 15, 15, 0, 0, tzinfo=timezone.utc),
            ),
            Campaign(
                id=CampaignId.from_string("camp_456"),
                name="Winter Promotion",
                description="Holiday season marketing campaign",
                status="active",
                cost_model="CPC",
                payout=Money.from_float(15.00, "USD"),
                safe_page_url=Url("https://example.com/winter-landing"),
                offer_page_url=Url("https://example.com/winter-offer"),
                daily_budget=Money.from_float(300.00, "USD"),
                total_budget=Money.from_float(9000.00, "USD"),
                start_date=datetime(2024, 11, 1, tzinfo=timezone.utc),
                end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
                clicks_count=8000,
                conversions_count=240,
                spent_amount=Money.from_float(2100.00, "USD"),
                created_at=datetime(2024, 11, 1, 8, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 11, 20, 12, 0, 0, tzinfo=timezone.utc),
            )
        ]

        for campaign in mock_campaigns:
            self._campaigns[campaign.id.value] = campaign

    def save(self, campaign: Campaign) -> None:
        """Save a campaign."""
        self._campaigns[campaign.id.value] = campaign

    def find_by_id(self, campaign_id: CampaignId) -> Optional[Campaign]:
        """Find campaign by ID."""
        if campaign_id.value in self._deleted_campaigns:
            return None
        return self._campaigns.get(campaign_id.value)

    def find_all(self, limit: int = 50, offset: int = 0) -> List[Campaign]:
        """Find all campaigns with pagination."""
        campaigns = list(self._campaigns.values())
        # Filter out deleted campaigns
        campaigns = [c for c in campaigns if c.id.value not in self._deleted_campaigns]
        return campaigns[offset:offset + limit]

    def exists_by_id(self, campaign_id: CampaignId) -> bool:
        """Check if campaign exists by ID."""
        return (campaign_id.value in self._campaigns and
                campaign_id.value not in self._deleted_campaigns)

    def delete_by_id(self, campaign_id: CampaignId) -> None:
        """Delete campaign by ID."""
        self._deleted_campaigns.add(campaign_id.value)

    def count_all(self) -> int:
        """Count total campaigns."""
        return len([c for c in self._campaigns.values()
                   if c.id.value not in self._deleted_campaigns])
