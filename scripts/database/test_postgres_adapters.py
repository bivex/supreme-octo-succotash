#!/usr/bin/env python3
"""
Test script for PostgreSQL adapters in DDD architecture.
Tests all repository implementations to ensure they work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from src.infrastructure.repositories.postgres_ltv_repository import PostgresLTVRepository
from src.infrastructure.repositories.postgres_retention_repository import PostgresRetentionRepository
from src.infrastructure.repositories.postgres_form_repository import PostgresFormRepository
from src.domain.entities.ltv import CustomerLTV
from src.domain.entities.retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, UserSegment, RetentionCampaignStatus
from src.domain.entities.form import Lead, FormSubmission, LeadScore, LeadStatus, LeadSource
from src.domain.value_objects.financial.money import Money


def test_postgres_ltv_repository():
    """Test PostgreSQL LTV repository."""
    print("🧪 Testing PostgresLTVRepository...")

    repo = PostgresLTVRepository()

    # Create test customer LTV
    customer_ltv = CustomerLTV(
        customer_id="test_customer_001",
        total_revenue=Money.from_float(1250.50, "USD"),
        total_purchases=5,
        average_order_value=Money.from_float(250.10, "USD"),
        purchase_frequency=1.2,
        customer_lifetime_months=12,
        predicted_clv=Money.from_float(1500.00, "USD"),
        actual_clv=Money.from_float(1250.50, "USD"),
        segment="high_value",
        cohort_id="cohort_2024_q1",
        first_purchase_date=datetime.now() - timedelta(days=365),
        last_purchase_date=datetime.now() - timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Test save and retrieve
    repo.save_customer_ltv(customer_ltv)
    retrieved = repo.get_customer_ltv("test_customer_001")

    assert retrieved is not None, "Customer LTV not saved/retrieved"
    assert retrieved.customer_id == "test_customer_001", "Customer ID mismatch"
    assert float(retrieved.total_revenue.amount) == 1250.50, "Revenue mismatch"

    print("✅ PostgresLTVRepository tests passed")


def test_postgres_retention_repository():
    """Test PostgreSQL retention repository."""
    print("🧪 Testing PostgresRetentionRepository...")

    repo = PostgresRetentionRepository()

    # Create test retention campaign
    campaign = RetentionCampaign(
        id="test_campaign_001",
        name="Test Retention Campaign",
        description="Test campaign for retention",
        target_segment=UserSegment.AT_RISK,
        status=RetentionCampaignStatus.DRAFT,
        triggers=[],  # Simplified
        message_template="Welcome back! We miss you.",
        target_user_count=100,
        sent_count=0,
        opened_count=0,
        clicked_count=0,
        converted_count=0,
        budget=500.0,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Test save and retrieve
    repo.save_retention_campaign(campaign)
    retrieved = repo.get_retention_campaign("test_campaign_001")

    assert retrieved is not None, "Retention campaign not saved/retrieved"
    assert retrieved.id == "test_campaign_001", "Campaign ID mismatch"
    assert retrieved.name == "Test Retention Campaign", "Campaign name mismatch"

    print("✅ PostgresRetentionRepository tests passed")


def test_postgres_form_repository():
    """Test PostgreSQL form repository."""
    print("🧪 Testing PostgresFormRepository...")

    repo = PostgresFormRepository()

    # Create test form submission
    submission = FormSubmission(
        id="test_submission_001",
        form_id="contact_form",
        campaign_id="camp_123",
        click_id="click_456",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        referrer="https://example.com",
        form_data={
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "company": "Test Corp"
        },
        validation_errors=[],
        is_valid=True,
        is_duplicate=False,
        duplicate_of=None,
        submitted_at=datetime.now(),
        processed_at=datetime.now()
    )

    # Test save and retrieve
    repo.save_form_submission(submission)
    retrieved = repo.get_form_submission("test_submission_001")

    assert retrieved is not None, "Form submission not saved/retrieved"
    assert retrieved.id == "test_submission_001", "Submission ID mismatch"
    assert retrieved.form_data["email"] == "test@example.com", "Form data mismatch"

    print("✅ PostgresFormRepository tests passed")


def main():
    """Run all PostgreSQL adapter tests."""
    print("🚀 Testing PostgreSQL Adapters for DDD Architecture\n")

    try:
        test_postgres_ltv_repository()
        test_postgres_retention_repository()
        test_postgres_form_repository()

        print("\n🎉 All PostgreSQL adapter tests passed!")
        print("✅ Your DDD project now supports PostgreSQL as the primary database!")

        # Show usage example
        print("\n📝 Usage Example:")
        print("""
# In your container.py, use PostgreSQL repositories:
from infrastructure.repositories import PostgresLTVRepository

def get_ltv_repository(self):
    return PostgresLTVRepository(
        host="localhost",
        port=5432,
        database="supreme_octosuccotash_db",
        user="app_user",
        password="app_password"
    )
        """)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure PostgreSQL is running and the database/user exists.")
        sys.exit(1)


if __name__ == "__main__":
    main()
