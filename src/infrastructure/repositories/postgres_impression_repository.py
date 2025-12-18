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

"""PostgreSQL impression repository implementation."""

import psycopg2
from typing import Optional, List
from datetime import datetime, date

from ...domain.entities.impression import Impression
from ...domain.repositories.impression_repository import ImpressionRepository
from ...domain.value_objects import ImpressionId


class PostgresImpressionRepository(ImpressionRepository):
    """PostgreSQL implementation of ImpressionRepository."""

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
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        # Create impressions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS impressions (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                ip_address INET NOT NULL,
                user_agent TEXT,
                referrer TEXT,
                is_valid BOOLEAN DEFAULT TRUE,
                sub1 TEXT,
                sub2 TEXT,
                sub3 TEXT,
                sub4 TEXT,
                sub5 TEXT,
                impression_id_param TEXT,
                affiliate_sub TEXT,
                affiliate_sub2 TEXT,
                affiliate_sub3 TEXT,
                affiliate_sub4 TEXT,
                affiliate_sub5 TEXT,
                landing_page_id INTEGER,
                campaign_offer_id INTEGER,
                traffic_source_id INTEGER,
                fraud_score DECIMAL(3,2) DEFAULT 0.0,
                fraud_reason TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_impressions_campaign_id ON impressions(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_impressions_created_at ON impressions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_impressions_is_valid ON impressions(is_valid)")

        conn.commit()

    def _row_to_impression(self, row) -> Impression:
        """Convert database row to Impression entity."""
        from ...domain.value_objects import CampaignId

        return Impression(
            id=ImpressionId.from_string(row["id"]),
            campaign_id=CampaignId(row["campaign_id"]) if row["campaign_id"] else None,
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            referrer=row["referrer"],
            is_valid=row["is_valid"],
            sub1=row["sub1"],
            sub2=row["sub2"],
            sub3=row["sub3"],
            sub4=row["sub4"],
            sub5=row["sub5"],
            impression_id_param=row["impression_id_param"],
            affiliate_sub=row["affiliate_sub"],
            affiliate_sub2=row["affiliate_sub2"],
            affiliate_sub3=row["affiliate_sub3"],
            affiliate_sub4=row["affiliate_sub4"],
            affiliate_sub5=row["affiliate_sub5"],
            landing_page_id=row["landing_page_id"],
            campaign_offer_id=row["campaign_offer_id"],
            traffic_source_id=row["traffic_source_id"],
            fraud_score=float(row["fraud_score"] or 0.0),
            fraud_reason=row["fraud_reason"],
            created_at=row["created_at"]
        )

    def _impression_to_row(self, impression: Impression) -> dict:
        """Convert Impression entity to database row."""
        return {
            'id': str(impression.id),
            'campaign_id': str(impression.campaign_id) if impression.campaign_id else None,
            'ip_address': impression.ip_address,
            'user_agent': impression.user_agent,
            'referrer': impression.referrer,
            'is_valid': impression.is_valid,
            'sub1': impression.sub1,
            'sub2': impression.sub2,
            'sub3': impression.sub3,
            'sub4': impression.sub4,
            'sub5': impression.sub5,
            'impression_id_param': impression.impression_id_param,
            'affiliate_sub': impression.affiliate_sub,
            'affiliate_sub2': impression.affiliate_sub2,
            'affiliate_sub3': impression.affiliate_sub3,
            'affiliate_sub4': impression.affiliate_sub4,
            'affiliate_sub5': impression.affiliate_sub5,
            'landing_page_id': impression.landing_page_id,
            'campaign_offer_id': impression.campaign_offer_id,
            'traffic_source_id': impression.traffic_source_id,
            'fraud_score': impression.fraud_score,
            'fraud_reason': impression.fraud_reason,
            'created_at': impression.created_at
        }

    def save(self, impression: Impression) -> None:
        """Save an impression."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            row = self._impression_to_row(impression)

            cursor.execute("""
                INSERT INTO impressions (
                    id, campaign_id, ip_address, user_agent, referrer, is_valid,
                    sub1, sub2, sub3, sub4, sub5, impression_id_param,
                    affiliate_sub, affiliate_sub2, affiliate_sub3, affiliate_sub4, affiliate_sub5,
                    landing_page_id, campaign_offer_id, traffic_source_id,
                    fraud_score, fraud_reason, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    campaign_id = EXCLUDED.campaign_id,
                    ip_address = EXCLUDED.ip_address,
                    user_agent = EXCLUDED.user_agent,
                    referrer = EXCLUDED.referrer,
                    is_valid = EXCLUDED.is_valid,
                    sub1 = EXCLUDED.sub1,
                    sub2 = EXCLUDED.sub2,
                    sub3 = EXCLUDED.sub3,
                    sub4 = EXCLUDED.sub4,
                    sub5 = EXCLUDED.sub5,
                    impression_id_param = EXCLUDED.impression_id_param,
                    affiliate_sub = EXCLUDED.affiliate_sub,
                    affiliate_sub2 = EXCLUDED.affiliate_sub2,
                    affiliate_sub3 = EXCLUDED.affiliate_sub3,
                    affiliate_sub4 = EXCLUDED.affiliate_sub4,
                    affiliate_sub5 = EXCLUDED.affiliate_sub5,
                    landing_page_id = EXCLUDED.landing_page_id,
                    campaign_offer_id = EXCLUDED.campaign_offer_id,
                    traffic_source_id = EXCLUDED.traffic_source_id,
                    fraud_score = EXCLUDED.fraud_score,
                    fraud_reason = EXCLUDED.fraud_reason
            """, (
                row['id'], row['campaign_id'], row['ip_address'], row['user_agent'], row['referrer'], row['is_valid'],
                row['sub1'], row['sub2'], row['sub3'], row['sub4'], row['sub5'], row['impression_id_param'],
                row['affiliate_sub'], row['affiliate_sub2'], row['affiliate_sub3'], row['affiliate_sub4'], row['affiliate_sub5'],
                row['landing_page_id'], row['campaign_offer_id'], row['traffic_source_id'],
                row['fraud_score'], row['fraud_reason'], row['created_at']
            ))

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_id(self, impression_id: ImpressionId) -> Optional[Impression]:
        """Find impression by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM impressions WHERE id = %s", (str(impression_id),))
            row = cursor.fetchone()

            if row:
                return self._row_to_impression(row)
            return None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_campaign_id(self, campaign_id: str, limit: int = 100,
                           offset: int = 0) -> List[Impression]:
        """Find impressions by campaign ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM impressions
                WHERE campaign_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (campaign_id, limit, offset))

            rows = cursor.fetchall()
            return [self._row_to_impression(row) for row in rows]
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_filters(self, filters) -> List[Impression]:
        """Find impressions by filter criteria."""
        # TODO: Implement filter-based queries
        return []

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count impressions for a campaign."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM impressions WHERE campaign_id = %s", (campaign_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_impressions_in_date_range(self, campaign_id: str,
                                    start_date: date, end_date: date) -> List[Impression]:
        """Get impressions within date range for analytics."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM impressions
                WHERE campaign_id = %s
                AND DATE(created_at) >= %s
                AND DATE(created_at) <= %s
                ORDER BY created_at DESC
            """, (campaign_id, start_date, end_date))

            rows = cursor.fetchall()
            return [self._row_to_impression(row) for row in rows]
        finally:
            if conn:
                self._container.release_db_connection(conn)
