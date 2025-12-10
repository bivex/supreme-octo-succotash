"""PostgreSQL conversion repository implementation."""

import psycopg2
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...domain.entities.conversion import Conversion
from ...domain.repositories.conversion_repository import ConversionRepository


class PostgresConversionRepository(ConversionRepository):
    """PostgreSQL implementation of ConversionRepository."""

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                id TEXT PRIMARY KEY,
                click_id TEXT NOT NULL,
                campaign_id TEXT NOT NULL,
                conversion_type TEXT NOT NULL,
                conversion_value DECIMAL(10,2) DEFAULT 0.0,
                currency TEXT DEFAULT 'USD',
                status TEXT NOT NULL,
                external_id TEXT,
                metadata JSONB,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversions_click_id ON conversions(click_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversions_campaign_id ON conversions(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversions_type ON conversions(conversion_type)")

        conn.commit()

    def _row_to_conversion(self, row) -> Conversion:
        """Convert database row to Conversion entity."""
        return Conversion(
            id=row["id"],
            click_id=row["click_id"],
            campaign_id=row["campaign_id"],
            conversion_type=row["conversion_type"],
            conversion_value=float(row["conversion_value"]),
            currency=row["currency"],
            status=row["status"],
            external_id=row["external_id"],
            metadata=row["metadata"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save(self, conversion: Conversion) -> None:
        """Save a conversion."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO conversions
            (id, click_id, campaign_id, conversion_type, conversion_value,
             currency, status, external_id, metadata, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                click_id = EXCLUDED.click_id,
                campaign_id = EXCLUDED.campaign_id,
                conversion_type = EXCLUDED.conversion_type,
                conversion_value = EXCLUDED.conversion_value,
                currency = EXCLUDED.currency,
                status = EXCLUDED.status,
                external_id = EXCLUDED.external_id,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at
        """, (
            conversion.id, conversion.click_id, conversion.campaign_id,
            conversion.conversion_type, conversion.conversion_value,
            conversion.currency, conversion.status, conversion.external_id,
            json.dumps(conversion.metadata), conversion.created_at, conversion.updated_at
        ))

        conn.commit()

    def get_by_id(self, conversion_id: str) -> Optional[Conversion]:
        """Get conversion by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM conversions WHERE id = %s", (conversion_id,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_conversion(row_dict)
        return None

    def get_by_click_id(self, click_id: str) -> List[Conversion]:
        """Get conversions by click ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversions
            WHERE click_id = %s
            ORDER BY created_at DESC
        """, (click_id,))

        conversions = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            conversions.append(self._row_to_conversion(row_dict))

        return conversions

    def get_by_order_id(self, order_id: str) -> Optional[Conversion]:
        """Get conversion by order ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM conversions WHERE external_id = %s", (order_id,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_conversion(row_dict)
        return None

    def get_unprocessed(self, limit: int = 100) -> List[Conversion]:
        """Get unprocessed conversions for postback sending."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversions
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT %s
        """, (limit,))

        conversions = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            conversions.append(self._row_to_conversion(row_dict))

        return conversions

    def mark_processed(self, conversion_id: str) -> None:
        """Mark conversion as processed (postbacks sent)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE conversions SET status = 'processed', updated_at = %s
            WHERE id = %s
        """, (datetime.now(), conversion_id))

        conn.commit()

    def get_conversions_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        conversion_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Conversion]:
        """Get conversions within a time range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if conversion_type:
            cursor.execute("""
                SELECT * FROM conversions
                WHERE created_at >= %s AND created_at <= %s AND conversion_type = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (start_time, end_time, conversion_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM conversions
                WHERE created_at >= %s AND created_at <= %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (start_time, end_time, limit))

        conversions = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            conversions.append(self._row_to_conversion(row_dict))

        return conversions

    def get_conversion_stats(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = 'conversion_type'
    ) -> Dict[str, Any]:
        """Get conversion statistics grouped by specified field."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if group_by == 'conversion_type':
            cursor.execute("""
                SELECT conversion_type, COUNT(*) as count,
                       SUM(conversion_value) as total_value
                FROM conversions
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY conversion_type
            """, (start_time, end_time))
        elif group_by == 'campaign_id':
            cursor.execute("""
                SELECT campaign_id, COUNT(*) as count,
                       SUM(conversion_value) as total_value
                FROM conversions
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY campaign_id
            """, (start_time, end_time))
        elif group_by == 'status':
            cursor.execute("""
                SELECT status, COUNT(*) as count,
                       SUM(conversion_value) as total_value
                FROM conversions
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY status
            """, (start_time, end_time))
        else:
            # Default to conversion_type
            cursor.execute("""
                SELECT conversion_type, COUNT(*) as count,
                       SUM(conversion_value) as total_value
                FROM conversions
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY conversion_type
            """, (start_time, end_time))

        result = {}
        for row in cursor.fetchall():
            key = row[0] if row[0] is not None else 'unknown'
            result[key] = {
                'count': row[1],
                'total_value': float(row[2]) if row[2] else 0.0
            }

        return result

    def get_total_revenue(
        self,
        start_time: datetime,
        end_time: datetime,
        conversion_type: Optional[str] = None
    ) -> float:
        """Get total revenue from conversions in time range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if conversion_type:
            cursor.execute("""
                SELECT SUM(conversion_value) as total_revenue
                FROM conversions
                WHERE created_at >= %s AND created_at <= %s AND conversion_type = %s
            """, (start_time, end_time, conversion_type))
        else:
            cursor.execute("""
                SELECT SUM(conversion_value) as total_revenue
                FROM conversions
                WHERE created_at >= %s AND created_at <= %s
            """, (start_time, end_time))

        row = cursor.fetchone()
        return float(row[0]) if row[0] else 0.0
