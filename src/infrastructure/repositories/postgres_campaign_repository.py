"""PostgreSQL campaign repository implementation."""

import psycopg2
from typing import Optional, List, Dict
from datetime import datetime
import json

from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignId, Money, Url


class PostgresCampaignRepository(CampaignRepository):
    """PostgreSQL implementation of CampaignRepository."""

    def __init__(self, host: str = "localhost", port: int = 5432, database: str = "supreme_octosuccotash_db",
                 user: str = "app_user", password: str = "app_password"):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'client_encoding': 'utf8'
        }
        self._connection = None
        self._initialize_db()

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = psycopg2.connect(**self.connection_params)
        return self._connection

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create campaigns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                cost_model TEXT NOT NULL,
                payout_amount DECIMAL(10,2) NOT NULL,
                payout_currency TEXT NOT NULL,
                safe_page_url TEXT NOT NULL,
                offer_page_url TEXT NOT NULL,
                daily_budget_amount DECIMAL(10,2) NOT NULL,
                daily_budget_currency TEXT NOT NULL,
                total_budget_amount DECIMAL(10,2) NOT NULL,
                total_budget_currency TEXT NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                clicks_count INTEGER DEFAULT 0,
                conversions_count INTEGER DEFAULT 0,
                spent_amount DECIMAL(10,2) DEFAULT 0.0,
                spent_currency TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)

        conn.commit()

    def _row_to_campaign(self, row) -> Campaign:
        """Convert database row to Campaign entity."""
        return Campaign(
            id=CampaignId.from_string(row["id"]),
            name=row["name"],
            description=row["description"],
            status=row["status"],
            cost_model=row["cost_model"],
            payout=Money.from_float(float(row["payout_amount"]), row["payout_currency"]),
            safe_page_url=Url(row["safe_page_url"]),
            offer_page_url=Url(row["offer_page_url"]),
            daily_budget=Money.from_float(float(row["daily_budget_amount"]), row["daily_budget_currency"]),
            total_budget=Money.from_float(float(row["total_budget_amount"]), row["total_budget_currency"]),
            start_date=row["start_date"],
            end_date=row["end_date"],
            clicks_count=row["clicks_count"],
            conversions_count=row["conversions_count"],
            spent_amount=Money.from_float(float(row["spent_amount"] or 0.0), row["spent_currency"] or "USD"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save(self, campaign: Campaign) -> None:
        """Save a campaign."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO campaigns
            (id, name, description, status, cost_model, payout_amount, payout_currency,
             safe_page_url, offer_page_url, daily_budget_amount, daily_budget_currency,
             total_budget_amount, total_budget_currency, start_date, end_date,
             clicks_count, conversions_count, spent_amount, spent_currency,
             created_at, updated_at, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                cost_model = EXCLUDED.cost_model,
                payout_amount = EXCLUDED.payout_amount,
                payout_currency = EXCLUDED.payout_currency,
                safe_page_url = EXCLUDED.safe_page_url,
                offer_page_url = EXCLUDED.offer_page_url,
                daily_budget_amount = EXCLUDED.daily_budget_amount,
                daily_budget_currency = EXCLUDED.daily_budget_currency,
                total_budget_amount = EXCLUDED.total_budget_amount,
                total_budget_currency = EXCLUDED.total_budget_currency,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                clicks_count = EXCLUDED.clicks_count,
                conversions_count = EXCLUDED.conversions_count,
                spent_amount = EXCLUDED.spent_amount,
                spent_currency = EXCLUDED.spent_currency,
                updated_at = EXCLUDED.updated_at,
                is_deleted = EXCLUDED.is_deleted
        """, (
            campaign.id.value, campaign.name, campaign.description, campaign.status,
            campaign.cost_model, campaign.payout.amount, campaign.payout.currency.value,
            campaign.safe_page_url.value, campaign.offer_page_url.value,
            campaign.daily_budget.amount, campaign.daily_budget.currency.value,
            campaign.total_budget.amount, campaign.total_budget.currency.value,
            campaign.start_date, campaign.end_date,
            campaign.clicks_count, campaign.conversions_count,
            campaign.spent_amount.amount if campaign.spent_amount else 0.0,
            campaign.spent_amount.currency.value if campaign.spent_amount else "USD",
            campaign.created_at, campaign.updated_at, False
        ))

        conn.commit()

    def find_by_id(self, campaign_id: CampaignId) -> Optional[Campaign]:
        """Find campaign by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM campaigns
            WHERE id = %s AND is_deleted = FALSE
        """, (campaign_id.value,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_campaign(row_dict)
        return None

    def find_all(self, limit: int = 50, offset: int = 0) -> List[Campaign]:
        """Find all campaigns with pagination."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM campaigns
            WHERE is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        campaigns = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            campaigns.append(self._row_to_campaign(row_dict))

        return campaigns

    def exists_by_id(self, campaign_id: CampaignId) -> bool:
        """Check if campaign exists by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM campaigns
            WHERE id = %s AND is_deleted = FALSE
        """, (campaign_id.value,))

        return cursor.fetchone() is not None

    def delete_by_id(self, campaign_id: CampaignId) -> None:
        """Delete campaign by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE campaigns SET is_deleted = TRUE, updated_at = %s
            WHERE id = %s
        """, (datetime.now(), campaign_id.value))

        conn.commit()

    def count_all(self) -> int:
        """Count total campaigns."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM campaigns
            WHERE is_deleted = FALSE
        """)

        return cursor.fetchone()[0]
