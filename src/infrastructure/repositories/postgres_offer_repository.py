# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""PostgreSQL offer repository implementation."""

from decimal import Decimal
from typing import Optional, List

from ...domain.entities.offer import Offer
from ...domain.repositories.offer_repository import OfferRepository
from ...domain.value_objects import Money, Url


class PostgresOfferRepository(OfferRepository):
    """PostgreSQL implementation of OfferRepository."""

    def __init__(self, container):
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

            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS offers
                           (
                               id
                               TEXT
                               PRIMARY
                               KEY,
                               campaign_id
                               TEXT
                               NOT
                               NULL,
                               name
                               TEXT
                               NOT
                               NULL,
                               url
                               TEXT
                               NOT
                               NULL,
                               offer_type
                               TEXT
                               NOT
                               NULL,
                               payout_amount
                               DECIMAL
                           (
                               10,
                               2
                           ) NOT NULL,
                               payout_currency TEXT NOT NULL,
                               revenue_share DECIMAL
                           (
                               5,
                               4
                           ) DEFAULT 0.00,
                               cost_per_click_amount DECIMAL
                           (
                               10,
                               2
                           ),
                               cost_per_click_currency TEXT,
                               weight INTEGER DEFAULT 100,
                               is_active BOOLEAN DEFAULT TRUE,
                               is_control BOOLEAN DEFAULT FALSE,
                               clicks INTEGER DEFAULT 0,
                               conversions INTEGER DEFAULT 0,
                               revenue_amount DECIMAL
                           (
                               10,
                               2
                           ) DEFAULT 0.00,
                               revenue_currency TEXT DEFAULT 'USD',
                               cost_amount DECIMAL
                           (
                               10,
                               2
                           ) DEFAULT 0.00,
                               cost_currency TEXT DEFAULT 'USD',
                               created_at TIMESTAMP NOT NULL,
                               updated_at TIMESTAMP NOT NULL
                               )
                           """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_campaign_id ON offers(campaign_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_active ON offers(is_active)")

            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing offers database: {e}")
            raise
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def _row_to_offer(self, row) -> Offer:
        """Convert database row to Offer entity."""
        return Offer(
            id=row["id"],
            campaign_id=row["campaign_id"],
            name=row["name"],
            url=Url(row["url"]),
            offer_type=row["offer_type"],
            payout=Money.from_float(float(row["payout_amount"]), row["payout_currency"]),
            revenue_share=Decimal(str(row["revenue_share"])),
            cost_per_click=Money.from_float(float(row["cost_per_click_amount"]), row["cost_per_click_currency"]) if row[
                "cost_per_click_amount"] else None,
            weight=row["weight"],
            is_active=row["is_active"],
            is_control=row["is_control"],
            clicks=row["clicks"],
            conversions=row["conversions"],
            revenue=Money.from_float(float(row["revenue_amount"]), row["revenue_currency"]),
            cost=Money.from_float(float(row["cost_amount"]), row["cost_currency"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save(self, offer: Offer) -> None:
        """Save an offer."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                           INSERT INTO offers
                           (id, campaign_id, name, url, offer_type, payout_amount, payout_currency,
                            revenue_share, cost_per_click_amount, cost_per_click_currency, weight,
                            is_active, is_control, clicks, conversions, revenue_amount, revenue_currency,
                            cost_amount, cost_currency, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                   %s) ON CONFLICT (id) DO
                           UPDATE SET
                               name = EXCLUDED.name,
                               url = EXCLUDED.url,
                               offer_type = EXCLUDED.offer_type,
                               payout_amount = EXCLUDED.payout_amount,
                               payout_currency = EXCLUDED.payout_currency,
                               revenue_share = EXCLUDED.revenue_share,
                               cost_per_click_amount = EXCLUDED.cost_per_click_amount,
                               cost_per_click_currency = EXCLUDED.cost_per_click_currency,
                               weight = EXCLUDED.weight,
                               is_active = EXCLUDED.is_active,
                               is_control = EXCLUDED.is_control,
                               clicks = EXCLUDED.clicks,
                               conversions = EXCLUDED.conversions,
                               revenue_amount = EXCLUDED.revenue_amount,
                               revenue_currency = EXCLUDED.revenue_currency,
                               cost_amount = EXCLUDED.cost_amount,
                               cost_currency = EXCLUDED.cost_currency,
                               updated_at = EXCLUDED.updated_at
                           """, (
                               offer.id, offer.campaign_id, offer.name, offer.url.value, offer.offer_type,
                               offer.payout.amount, offer.payout.currency, float(offer.revenue_share),
                               offer.cost_per_click.amount if offer.cost_per_click else None,
                               offer.cost_per_click.currency if offer.cost_per_click else None,
                               offer.weight, offer.is_active, offer.is_control,
                               offer.clicks, offer.conversions,
                               offer.revenue.amount, offer.revenue.currency,
                               offer.cost.amount, offer.cost.currency,
                               offer.created_at, offer.updated_at
                           ))

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_id(self, offer_id: str) -> Optional[Offer]:
        """Get offer by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM offers WHERE id = %s", (offer_id,))

            row = cursor.fetchone()
            if row:
                # Convert tuple to dict for easier access
                columns = [desc[0] for desc in cursor.description]
                row_dict = dict(zip(columns, row))
                return self._row_to_offer(row_dict)
            return None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_campaign_id(self, campaign_id: str) -> List[Offer]:
        """Get offers by campaign ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT *
                           FROM offers
                           WHERE campaign_id = %s
                           ORDER BY weight DESC, created_at DESC
                           """, (campaign_id,))

            offers = []
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                offers.append(self._row_to_offer(row_dict))

            return offers
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def update(self, offer: Offer) -> None:
        """Update an offer."""
        self.save(offer)  # UPSERT handles updates

    def delete_by_id(self, offer_id: str) -> bool:
        """Delete offer by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM offers WHERE id = %s", (offer_id,))

            deleted = cursor.rowcount > 0
            conn.commit()

            return deleted
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def exists_by_id(self, offer_id: str) -> bool:
        """Check if offer exists by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM offers WHERE id = %s", (offer_id,))

            return cursor.fetchone() is not None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count offers by campaign ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM offers WHERE campaign_id = %s", (campaign_id,))

            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            if conn:
                self._container.release_db_connection(conn)
