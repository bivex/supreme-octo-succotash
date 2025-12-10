"""PostgreSQL click repository implementation."""

import psycopg2
from typing import Optional, List
from datetime import datetime, date

from ...domain.entities.click import Click
from ...domain.repositories.click_repository import ClickRepository
from ...domain.value_objects import ClickId


class PostgresClickRepository(ClickRepository):
    """PostgreSQL implementation of ClickRepository."""

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

        # Create clicks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
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
                click_id_param TEXT,
                affiliate_sub TEXT,
                affiliate_sub2 TEXT,
                landing_page_id INTEGER,
                campaign_offer_id INTEGER,
                traffic_source_id INTEGER,
                conversion_type TEXT,
                converted_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL
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
            is_valid=row["is_valid"],
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
            converted_at=row["converted_at"],
            created_at=row["created_at"],
        )

    def save(self, click: Click) -> None:
        """Save a click."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clicks
            (id, campaign_id, ip_address, user_agent, referrer, is_valid,
             sub1, sub2, sub3, sub4, sub5, click_id_param, affiliate_sub, affiliate_sub2,
             landing_page_id, campaign_offer_id, traffic_source_id,
             conversion_type, converted_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                click_id_param = EXCLUDED.click_id_param,
                affiliate_sub = EXCLUDED.affiliate_sub,
                affiliate_sub2 = EXCLUDED.affiliate_sub2,
                landing_page_id = EXCLUDED.landing_page_id,
                campaign_offer_id = EXCLUDED.campaign_offer_id,
                traffic_source_id = EXCLUDED.traffic_source_id,
                conversion_type = EXCLUDED.conversion_type,
                converted_at = EXCLUDED.converted_at
        """, (
            click.id.value, click.campaign_id, click.ip_address, click.user_agent, click.referrer,
            click.is_valid, click.sub1, click.sub2, click.sub3, click.sub4, click.sub5,
            click.click_id_param, click.affiliate_sub, click.affiliate_sub2,
            click.landing_page_id, click.campaign_offer_id, click.traffic_source_id,
            click.conversion_type, click.converted_at, click.created_at
        ))

        conn.commit()

    def find_by_id(self, click_id: ClickId) -> Optional[Click]:
        """Find click by ID."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clicks WHERE id = %s", (click_id.value,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_click(row_dict)
        return None

    def find_by_campaign_id(self, campaign_id: str, limit: int = 100,
                           offset: int = 0) -> List[Click]:
        """Find clicks by campaign ID."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM clicks
            WHERE campaign_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (campaign_id, limit, offset))

        clicks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            clicks.append(self._row_to_click(row_dict))

        return clicks

    def find_by_filters(self, filters) -> List[Click]:
        """Find clicks by filter criteria."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM clicks WHERE 1=1"
        params = []

        if filters.campaign_id is not None:
            query += " AND campaign_id = %s"
            params.append(filters.campaign_id)

        if filters.is_valid is not None:
            query += " AND is_valid = %s"
            params.append(filters.is_valid)

        if filters.start_date is not None:
            query += " AND created_at >= %s"
            params.append(filters.start_date)

        if filters.end_date is not None:
            query += " AND created_at <= %s"
            params.append(filters.end_date)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([filters.limit, filters.offset])

        cursor.execute(query, params)

        clicks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            clicks.append(self._row_to_click(row_dict))

        return clicks

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count clicks for a campaign."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM clicks WHERE campaign_id = %s", (campaign_id,))
        return cursor.fetchone()[0]

    def count_conversions(self, campaign_id: str) -> int:
        """Count conversions for a campaign."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM clicks
            WHERE campaign_id = %s AND conversion_type IS NOT NULL
        """, (campaign_id,))
        return cursor.fetchone()[0]

    def get_clicks_in_date_range(self, campaign_id: str,
                                start_date: date, end_date: date) -> List[Click]:
        """Get clicks within date range for analytics."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM clicks
            WHERE campaign_id = %s AND DATE(created_at) >= %s AND DATE(created_at) <= %s
            ORDER BY created_at DESC
        """, (campaign_id, start_date, end_date))

        clicks = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            clicks.append(self._row_to_click(row_dict))

        return clicks
