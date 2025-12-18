
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Test script for PostgreSQL adapters in DDD architecture.
Tests all repository implementations to ensure they work correctly.
"""

import sys
import os
from unittest.mock import MagicMock
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from src.infrastructure.repositories.postgres_ltv_repository import PostgresLTVRepository
from src.infrastructure.repositories.postgres_retention_repository import PostgresRetentionRepository
from src.infrastructure.repositories.postgres_form_repository import PostgresFormRepository
from src.domain.entities.ltv import CustomerLTV
from src.domain.entities.retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, UserSegment, RetentionCampaignStatus
from src.domain.entities.form import Lead, FormSubmission, LeadScore, LeadStatus, LeadSource
from src.domain.value_objects.financial.money import Money


class MockRow:
    def __init__(self, data, columns):
        self._data = data
        self._columns = columns
        self._col_map = {col: i for i, col in enumerate(columns)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[key]
        elif isinstance(key, str):
            return self._data[self._col_map[key]]
        raise TypeError("Key must be an integer index or a string column name")

    def __len__(self):
        return len(self._data)


class MockContainer:
    def get_db_connection(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Mock for PostgresLTVRepository
        ltv_columns = [
            "customer_id", "total_revenue", "total_purchases", "average_order_value",
            "purchase_frequency", "customer_lifetime_months", "predicted_clv", "actual_clv",
            "segment", "cohort_id", "first_purchase_date", "last_purchase_date",
            "created_at", "updated_at"
        ]
        ltv_row_data = [
            "test_customer_001", "1250.50", 5, "250.10", 1.2, 12, "1500.00", "1250.50",
            "high_value", "cohort_2024_q1", (datetime.now() - timedelta(days=365)).date(),
            (datetime.now() - timedelta(days=30)).date(), datetime.now(), datetime.now()
        ]
        
        # Mock for PostgresRetentionRepository
        retention_columns = [
            "id", "name", "description", "target_segment", "status", "triggers",
            "message_template", "target_user_count", "sent_count", "opened_count",
            "clicked_count", "converted_count", "budget", "start_date", "end_date",
            "created_at", "updated_at"
        ]
        retention_row_data = [
            "test_campaign_001", "Test Retention Campaign", "Test campaign for retention",
            "at_risk", "draft", "[]", "Welcome back! We miss you.", 100, 0, 0, 0, 0, 500.0,
            (datetime.now() + timedelta(days=1)).date(), (datetime.now() + timedelta(days=30)).date(),
            datetime.now(), datetime.now()
        ]

        # Mock for PostgresFormRepository
        form_columns = [
            "id", "form_id", "campaign_id", "click_id", "ip_address", "user_agent",
            "referrer", "form_data", "validation_errors", "is_valid", "is_duplicate",
            "duplicate_of", "submitted_at", "processed_at"
        ]
        form_row_data = [
            "test_submission_001", "contact_form", "camp_123", "click_456", "192.168.1.100",
            "Mozilla/5.0 Test Browser", "https://example.com", json.dumps({"email": "test@example.com", "first_name": "John"}),
            "[]", True, False, None, datetime.now(), datetime.now()
        ]

        def _choose_row_for_query():
            """Return a row matching the last executed query."""
            query = getattr(mock_cursor, "_last_query", "") or ""
            q_lower = query.lower()
            if "retention" in q_lower:
                return MockRow(retention_row_data, retention_columns)
            if "form" in q_lower:
                return MockRow(form_row_data, form_columns)
            return MockRow(ltv_row_data, ltv_columns)

        def _execute_side_effect(query, *args, **kwargs):
            mock_cursor._last_query = query
            return None

        mock_cursor.execute.side_effect = _execute_side_effect
        mock_cursor.fetchone.side_effect = _choose_row_for_query
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn

    def release_db_connection(self, conn):
        pass

container = MockContainer()

def test_postgres_ltv_repository():
    """Test PostgreSQL LTV repository."""
    print("🧪 Testing PostgresLTVRepository...")

    repo = PostgresLTVRepository(container)

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

    repo = PostgresRetentionRepository(container)

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

    repo = PostgresFormRepository(container)

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