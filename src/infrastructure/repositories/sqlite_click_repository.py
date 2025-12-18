# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""SQLite click repository implementation."""

import sqlite3
from datetime import datetime, timezone, date
from typing import Optional, List

from ...domain.entities.click import Click
from ...domain.repositories.click_repository import ClickRepository
from ...domain.value_objects import ClickId


class SQLiteClickRepository(ClickRepository):
    """SQLite implementation of ClickRepository for stress testing."""

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

        # Create clicks table
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS clicks
                       (
                           id
                           TEXT
                           PRIMARY
                           KEY,
                           campaign_id
                           TEXT
                           NOT
                           NULL,
                           ip_address
                           TEXT
                           NOT
                           NULL,
                           user_agent
                           TEXT,
                           referrer
                           TEXT,
                           is_valid
                           INTEGER
                           DEFAULT
                           1,
                           sub1
                           TEXT,
                           sub2
                           TEXT,
                           sub3
                           TEXT,
                           sub4
                           TEXT,
                           sub5
                           TEXT,
                           click_id_param
                           TEXT,
                           affiliate_sub
                           TEXT,
                           affiliate_sub2
                           TEXT,
                           landing_page_id
                           INTEGER,
                           campaign_offer_id
                           INTEGER,
                           traffic_source_id
                           INTEGER,
                           conversion_type
                           TEXT,
                           converted_at
                           TEXT,
                           created_at
                           TEXT
                           NOT
                           NULL
                       )
                       """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_campaign_id ON clicks(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_created_at ON clicks(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_is_valid ON clicks(is_valid)")

        conn.commit()

    def _row_to_click(self, row) -> Click:
        """Convert database row to Click entity."""
        return Click(
            id=ClickId.from_string(row["id"]),
            campaign_id=row["campaign_id"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            referrer=row["referrer"],
            is_valid=bool(row["is_valid"]),
            sub1=row["sub1"],
            sub2=row["sub2"],
            sub3=row["sub3"],
            sub4=row["sub4"],
            sub5=row["sub5"],
            click_id_param=row["click_id_param"],
            affiliate_sub=row["affiliate_sub"],
            affiliate_sub2=row["affiliate_sub2"],
            landing_page_id=row["landing_page_id"],
            campaign_offer_id=row["campaign_offer_id"],
            traffic_source_id=row["traffic_source_id"],
            conversion_type=row["conversion_type"],
            converted_at=datetime.fromisoformat(row["converted_at"]) if row["converted_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def save(self, click: Click) -> None:
        """Save a click."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO clicks
            (id, campaign_id, ip_address, user_agent, referrer, is_valid,
             sub1, sub2, sub3, sub4, sub5, click_id_param, affiliate_sub, affiliate_sub2,
             landing_page_id, campaign_offer_id, traffic_source_id,
             conversion_type, converted_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            click.id.value, click.campaign_id, click.ip_address, click.user_agent, click.referrer,
            click.is_valid, click.sub1, click.sub2, click.sub3, click.sub4, click.sub5,
            click.click_id_param, click.affiliate_sub, click.affiliate_sub2,
            click.landing_page_id, click.campaign_offer_id, click.traffic_source_id,
            click.conversion_type, click.converted_at.isoformat() if click.converted_at else None,
            click.created_at.isoformat()
        ))

        conn.commit()

    def find_by_id(self, click_id: ClickId) -> Optional[Click]:
        """Find click by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clicks WHERE id = ?", (click_id.value,))

        row = cursor.fetchone()
        return self._row_to_click(row) if row else None

    def find_by_campaign_id(self, campaign_id: str, limit: int = 100,
                            offset: int = 0) -> List[Click]:
        """Find clicks by campaign ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT *
                       FROM clicks
                       WHERE campaign_id = ?
                       ORDER BY created_at DESC LIMIT ?
                       OFFSET ?
                       """, (campaign_id, limit, offset))

        return [self._row_to_click(row) for row in cursor.fetchall()]

    def find_by_filters(self, filters) -> List[Click]:
        """Find clicks by filter criteria."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM clicks WHERE 1=1"
        params = []

        if filters.campaign_id is not None:
            query += " AND campaign_id = ?"
            params.append(filters.campaign_id)

        if filters.is_valid is not None:
            query += " AND is_valid = ?"
            params.append(filters.is_valid)

        if filters.start_date is not None:
            query += " AND created_at >= ?"
            params.append(filters.start_date.isoformat())

        if filters.end_date is not None:
            query += " AND created_at <= ?"
            params.append(filters.end_date.isoformat())

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([filters.limit, filters.offset])

        cursor.execute(query, params)
        return [self._row_to_click(row) for row in cursor.fetchall()]

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count clicks for a campaign."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM clicks WHERE campaign_id = ?", (campaign_id,))
        return cursor.fetchone()[0]

    def count_conversions(self, campaign_id: str) -> int:
        """Count conversions for a campaign."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT COUNT(*)
                       FROM clicks
                       WHERE campaign_id = ?
                         AND conversion_type IS NOT NULL
                       """, (campaign_id,))
        return cursor.fetchone()[0]

    def get_clicks_in_date_range(self, campaign_id: str,
                                 start_date: date, end_date: date) -> List[Click]:
        """Get clicks within date range for analytics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        cursor.execute("""
                       SELECT *
                       FROM clicks
                       WHERE campaign_id = ?
                         AND created_at >= ?
                         AND created_at <= ?
                       ORDER BY created_at DESC
                       """, (campaign_id, start_datetime.isoformat(), end_datetime.isoformat()))

        return [self._row_to_click(row) for row in cursor.fetchall()]
