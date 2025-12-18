# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:40
# Last Updated: 2025-12-18T12:12:40
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Unit tests for Campaign domain entity."""

import pytest
from decimal import Decimal

from src.domain.entities.campaign import Campaign
from src.domain.value_objects import CampaignId, CampaignStatus, Money


class TestCampaign:
    """Test cases for Campaign entity."""

    def test_campaign_creation(self):
        """Test basic campaign creation."""
        campaign_id = CampaignId.from_string("test_campaign")
        payout = Money.from_float(25.50, "USD")

        campaign = Campaign(
            id=campaign_id,
            name="Test Campaign",
            description="A test campaign",
            cost_model="CPA",
            payout=payout,
        )

        assert campaign.id == campaign_id
        assert campaign.name == "Test Campaign"
        assert campaign.description == "A test campaign"
        assert campaign.status == CampaignStatus.DRAFT
        assert campaign.cost_model == "CPA"
        assert campaign.payout == payout

    def test_campaign_validation(self):
        """Test campaign validation."""
        # Test empty name
        with pytest.raises(ValueError, match="Campaign name is required"):
            Campaign(
                id=CampaignId.generate(),
                name="",
                cost_model="CPA",
                payout=Money.from_float(10.0, "USD"),
            )

        # Test invalid cost model
        with pytest.raises(ValueError, match="Cost model must be"):
            Campaign(
                id=CampaignId.generate(),
                name="Test Campaign",
                cost_model="INVALID",
                payout=Money.from_float(10.0, "USD"),
            )

    def test_campaign_status_transitions(self):
        """Test campaign status transitions."""
        campaign = Campaign(
            id=CampaignId.generate(),
            name="Test Campaign",
            cost_model="CPA",
            payout=Money.from_float(10.0, "USD"),
        )

        # Should start as draft
        assert campaign.status == CampaignStatus.DRAFT

        # Can activate from draft
        campaign.activate()
        assert campaign.status == CampaignStatus.ACTIVE

        # Can pause when active
        campaign.pause()
        assert campaign.status == CampaignStatus.PAUSED

        # Can activate when paused
        campaign.activate()
        assert campaign.status == CampaignStatus.ACTIVE

    def test_campaign_performance_calculation(self):
        """Test campaign performance calculations."""
        campaign = Campaign(
            id=CampaignId.generate(),
            name="Test Campaign",
            cost_model="CPA",
            payout=Money.from_float(10.0, "USD"),
        )

        # Initially zero
        assert campaign.clicks_count == 0
        assert campaign.conversions_count == 0
        assert campaign.ctr == 0.0
        assert campaign.cr == 0.0

        # Update performance
        campaign.update_performance(clicks_increment=100, conversions_increment=10)

        assert campaign.clicks_count == 100
        assert campaign.conversions_count == 10
        assert campaign.cr == 0.1  # 10%

    def test_campaign_budget_validation(self):
        """Test campaign budget validation."""
        # Valid budget
        campaign = Campaign(
            id=CampaignId.generate(),
            name="Test Campaign",
            cost_model="CPA",
            payout=Money.from_float(10.0, "USD"),
            daily_budget=Money.from_float(100.0, "USD"),
            total_budget=Money.from_float(1000.0, "USD"),
        )

        assert campaign.daily_budget.amount == Decimal('100.00')
        assert campaign.total_budget.amount == Decimal('1000.00')

        # Invalid: daily budget > total budget
        with pytest.raises(ValueError):
            Campaign(
                id=CampaignId.generate(),
                name="Test Campaign",
                cost_model="CPA",
                payout=Money.from_float(10.0, "USD"),
                daily_budget=Money.from_float(2000.0, "USD"),  # Too high
                total_budget=Money.from_float(1000.0, "USD"),
            )
