"""PostgreSQL campaign repository implementation."""

import psycopg2
import psycopg2.extensions
from typing import Optional, List, Dict
from datetime import datetime
import json

from ...domain.entities.campaign import Campaign, CampaignStatus
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import CampaignId, Money, Url

# Register adapter for CampaignId
def adapt_campaign_id(campaign_id):
    print(f"DEBUG: Adapting CampaignId {campaign_id} to {campaign_id.value}")
    return psycopg2.extensions.adapt(campaign_id.value)

psycopg2.extensions.register_adapter(CampaignId, adapt_campaign_id)


class PostgresCampaignRepository(CampaignRepository):
    """PostgreSQL implementation of CampaignRepository."""

    def __init__(self, container):
        self._container = container
        self._connection = None
        self._db_initialized = False

    def _extract_value(self, obj):
        """Extract string value from value objects or return the object if it's already a basic type."""
        if hasattr(obj, 'value'):
            return obj.value
        return obj

    def _get_connection(self):
        self._container = container
        self._connection = None
        self._db_initialized = False

    def _get_connection(self):


        """Get database connection."""


        if self._connection is None:


            self._connection = self._container.get_db_connection()


        if not self._db_initialized:


            self._initialize_db()


            self._db_initialized = True


        return self._connection

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        conn = None
        try:
            conn = self._container.get_db_connection()
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
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def _row_to_campaign(self, row) -> Campaign:
        """Convert database row to Campaign entity."""
        try:
            # Safely parse Money objects
            def safe_money_from_float(amount, currency, default_amount=0.0, default_currency="USD"):
                try:
                    if amount is not None and amount != "":
                        return Money.from_float(float(amount), currency or default_currency)
                except (ValueError, TypeError):
                    pass
                return Money.from_float(default_amount, default_currency)

            # Safely create URLs
            def safe_url(url_str):
                try:
                    if url_str and url_str.strip():
                        return Url(url_str.strip())
                except Exception:
                    pass
                return None

            return Campaign(
                id=CampaignId.from_string(str(row["id"])),
                name=str(row["name"] or ""),
                description=row["description"],
                status=CampaignStatus(str(row["status"] or "draft")),
                cost_model=str(row["cost_model"] or "CPA").upper(),
                payout=safe_money_from_float(row["payout_amount"], row["payout_currency"]) if row["payout_amount"] is not None else None,
                safe_page_url=safe_url(row["safe_page_url"]),
                offer_page_url=safe_url(row["offer_page_url"]),
                daily_budget=safe_money_from_float(row["daily_budget_amount"], row["daily_budget_currency"]) if row["daily_budget_amount"] is not None else None,
                total_budget=safe_money_from_float(row["total_budget_amount"], row["total_budget_currency"]) if row["total_budget_amount"] is not None else None,
                start_date=row["start_date"],
                end_date=row["end_date"],
                clicks_count=int(row["clicks_count"] or 0),
                conversions_count=int(row["conversions_count"] or 0),
                spent_amount=safe_money_from_float(row["spent_amount"], row["spent_currency"], 0.0, "USD"),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        except Exception as e:
            raise ValueError(f"Failed to convert database row to Campaign: {e}") from e

    def save(self, campaign: Campaign) -> None:
        """Save a campaign."""
        conn = None
        try:
            conn = self._container.get_db_connection()
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
                campaign.id.value, campaign.name, campaign.description, campaign.status.value,
                campaign.cost_model,
                campaign.payout.amount if campaign.payout else None,
                campaign.payout.currency if campaign.payout else None,
                campaign.safe_page_url.value if campaign.safe_page_url else None,
                campaign.offer_page_url.value if campaign.offer_page_url else None,
                campaign.daily_budget.amount if campaign.daily_budget else None,
                campaign.daily_budget.currency if campaign.daily_budget else None,
                campaign.total_budget.amount if campaign.total_budget else None,
                campaign.total_budget.currency if campaign.total_budget else None,
                campaign.start_date, campaign.end_date,
                campaign.clicks_count, campaign.conversions_count,
                campaign.spent_amount.amount if campaign.spent_amount else 0.0,
                campaign.spent_amount.currency if campaign.spent_amount else "USD",
                campaign.created_at, campaign.updated_at, False
            ))

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_id(self, campaign_id: CampaignId) -> Optional[Campaign]:
        """Find campaign by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
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
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_all(self, limit: int = 50, offset: int = 0) -> List[Campaign]:
        """Find all campaigns with pagination."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM campaigns
                WHERE is_deleted = FALSE
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

            campaigns = []
            columns = [desc[0] for desc in cursor.description]
            for i, row in enumerate(cursor.fetchall()):
                try:
                    row_dict = dict(zip(columns, row))
                    campaign = self._row_to_campaign(row_dict)
                    campaigns.append(campaign)
                except Exception as row_error:
                    print(f"Error processing campaign row {i} with ID {row[0] if row else 'unknown'}: {row_error}")
                    # Skip this row and continue
                    continue

            return campaigns
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def exists_by_id(self, campaign_id: CampaignId) -> bool:
        """Check if campaign exists by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 1 FROM campaigns
                WHERE id = %s AND is_deleted = FALSE
            """, (campaign_id.value,))

            return cursor.fetchone() is not None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def delete_by_id(self, campaign_id: CampaignId) -> None:
        """Delete campaign by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE campaigns SET is_deleted = TRUE, updated_at = %s
                WHERE id = %s
            """, (datetime.now(), campaign_id.value))

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def count_all(self) -> int:
        """Count total campaigns with caching."""
        import time

        # Простое кеширование на 30 секунд
        current_time = time.time()
        if hasattr(self, '_count_cache') and hasattr(self, '_count_cache_time'):
            if current_time - self._count_cache_time < 30:  # 30 секунд TTL
                return self._count_cache

        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM campaigns
                WHERE is_deleted = FALSE
            """)

            count = cursor.fetchone()[0]

            # Кешируем результат
            self._count_cache = count
            self._count_cache_time = current_time

            return count
        finally:
            if conn:
                self._container.release_db_connection(conn)
