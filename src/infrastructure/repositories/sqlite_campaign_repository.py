"""SQLite campaign repository implementation."""

import sqlite3
from typing import Optional, List, Dict
from datetime import datetime, timezone
import json

from ...domain.entities.campaign import Campaign
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignId, Money, Url


class SQLiteCampaignRepository(CampaignRepository):
    """SQLite implementation of CampaignRepository for stress testing."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._connection = None
        self._initialize_db()

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
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
                payout_amount REAL NOT NULL,
                payout_currency TEXT NOT NULL,
                safe_page_url TEXT NOT NULL,
                offer_page_url TEXT NOT NULL,
                daily_budget_amount REAL NOT NULL,
                daily_budget_currency TEXT NOT NULL,
                total_budget_amount REAL NOT NULL,
                total_budget_currency TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                clicks_count INTEGER DEFAULT 0,
                conversions_count INTEGER DEFAULT 0,
                spent_amount REAL DEFAULT 0.0,
                spent_currency TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0
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
            cost_model=row["cost_model"].upper(),
            payout=Money.from_float(row["payout_amount"], row["payout_currency"]),
            safe_page_url=Url(row["safe_page_url"]),
            offer_page_url=Url(row["offer_page_url"]),
            daily_budget=Money.from_float(row["daily_budget_amount"], row["daily_budget_currency"]),
            total_budget=Money.from_float(row["total_budget_amount"], row["total_budget_currency"]),
            start_date=datetime.fromisoformat(row["start_date"]),
            end_date=datetime.fromisoformat(row["end_date"]),
            clicks_count=row["clicks_count"],
            conversions_count=row["conversions_count"],
            spent_amount=Money.from_float(row["spent_amount"] or 0.0, row["spent_currency"] or "USD"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def save(self, campaign: Campaign) -> None:
        """Save a campaign."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO campaigns
            (id, name, description, status, cost_model, payout_amount, payout_currency,
             safe_page_url, offer_page_url, daily_budget_amount, daily_budget_currency,
             total_budget_amount, total_budget_currency, start_date, end_date,
             clicks_count, conversions_count, spent_amount, spent_currency,
             created_at, updated_at, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign.id.value, campaign.name, campaign.description, campaign.status,
            campaign.cost_model, campaign.payout.amount, campaign.payout.currency.value,
            campaign.safe_page_url.value, campaign.offer_page_url.value,
            campaign.daily_budget.amount, campaign.daily_budget.currency.value,
            campaign.total_budget.amount, campaign.total_budget.currency.value,
            campaign.start_date.isoformat(), campaign.end_date.isoformat(),
            campaign.clicks_count, campaign.conversions_count,
            campaign.spent_amount.amount if campaign.spent_amount else 0.0,
            campaign.spent_amount.currency.value if campaign.spent_amount else "USD",
            campaign.created_at.isoformat(), campaign.updated_at.isoformat(), 0
        ))

        conn.commit()

    def find_by_id(self, campaign_id: CampaignId) -> Optional[Campaign]:
        """Find campaign by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM campaigns
            WHERE id = ? AND is_deleted = 0
        """, (campaign_id.value,))

        row = cursor.fetchone()
        return self._row_to_campaign(row) if row else None

    def find_all(self, limit: int = 50, offset: int = 0) -> List[Campaign]:
        """Find all campaigns with pagination."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM campaigns
            WHERE is_deleted = 0
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        return [self._row_to_campaign(row) for row in cursor.fetchall()]

    def exists_by_id(self, campaign_id: CampaignId) -> bool:
        """Check if campaign exists by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM campaigns
            WHERE id = ? AND is_deleted = 0
        """, (campaign_id.value,))

        return cursor.fetchone() is not None

    def delete_by_id(self, campaign_id: CampaignId) -> None:
        """Delete campaign by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE campaigns SET is_deleted = 1, updated_at = ?
            WHERE id = ?
        """, (datetime.now(timezone.utc).isoformat(), campaign_id.value))

        conn.commit()

    def count_all(self) -> int:
        """Count total campaigns."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM campaigns WHERE is_deleted = 0")
        return cursor.fetchone()[0]
