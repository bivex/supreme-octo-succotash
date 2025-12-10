"""SQLite conversion repository implementation."""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from ...domain.entities.conversion import Conversion
from ...domain.repositories.conversion_repository import ConversionRepository


class SQLiteConversionRepository(ConversionRepository):
    """SQLite implementation of ConversionRepository for stress testing."""

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                id TEXT PRIMARY KEY,
                click_id TEXT NOT NULL,
                campaign_id TEXT NOT NULL,
                conversion_type TEXT NOT NULL,
                conversion_value REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'USD',
                status TEXT NOT NULL,
                external_id TEXT,
                metadata TEXT,  -- JSON string
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversions_click_id ON conversions(click_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversions_campaign_id ON conversions(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversions_type ON conversions(conversion_type)")

        conn.commit()

    def save(self, conversion: Conversion) -> None:
        """Save a conversion."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO conversions
            (id, click_id, campaign_id, conversion_type, conversion_value, currency,
             status, external_id, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conversion.id.value, conversion.click_id, conversion.campaign_id,
            conversion.conversion_type, conversion.conversion_value,
            conversion.currency, conversion.status, conversion.external_id,
            json.dumps(conversion.metadata) if conversion.metadata else None,
            conversion.created_at.isoformat(), conversion.updated_at.isoformat()
        ))

        conn.commit()

    def find_by_id(self, conversion_id: str) -> Optional[Conversion]:
        """Find conversion by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM conversions WHERE id = ?", (conversion_id,))

        row = cursor.fetchone()
        return self._row_to_conversion(row) if row else None

    def find_by_click_id(self, click_id: str) -> List[Conversion]:
        """Find conversions by click ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversions
            WHERE click_id = ?
            ORDER BY created_at DESC
        """, (click_id,))

        return [self._row_to_conversion(row) for row in cursor.fetchall()]

    def find_by_campaign_id(self, campaign_id: str, limit: int = 100) -> List[Conversion]:
        """Find conversions by campaign ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversions
            WHERE campaign_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (campaign_id, limit))

        return [self._row_to_conversion(row) for row in cursor.fetchall()]

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count conversions for a campaign."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM conversions WHERE campaign_id = ?", (campaign_id,))
        return cursor.fetchone()[0]

    def get_by_id(self, conversion_id: str) -> Optional[Conversion]:
        """Get conversion by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM conversions WHERE id = ?", (conversion_id,))

        row = cursor.fetchone()
        return self._row_to_conversion(row) if row else None

    def get_by_click_id(self, click_id: str) -> List[Conversion]:
        """Get conversions by click ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversions
            WHERE click_id = ?
            ORDER BY created_at DESC
        """, (click_id,))

        return [self._row_to_conversion(row) for row in cursor.fetchall()]

    def get_by_order_id(self, order_id: str) -> Optional[Conversion]:
        """Get conversion by order ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM conversions WHERE external_id = ?", (order_id,))

        row = cursor.fetchone()
        return self._row_to_conversion(row) if row else None

    def get_unprocessed(self, limit: int = 100) -> List[Conversion]:
        """Get unprocessed conversions for postback sending."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversions
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))

        return [self._row_to_conversion(row) for row in cursor.fetchall()]

    def mark_processed(self, conversion_id: str) -> None:
        """Mark conversion as processed (postbacks sent)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE conversions
            SET status = 'processed', updated_at = ?
            WHERE id = ?
        """, (datetime.now(timezone.utc).isoformat(), conversion_id))

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

        query = """
            SELECT * FROM conversions
            WHERE created_at >= ? AND created_at <= ?
        """
        params = [start_time.isoformat(), end_time.isoformat()]

        if conversion_type:
            query += " AND conversion_type = ?"
            params.append(conversion_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_conversion(row) for row in cursor.fetchall()]

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
                SELECT conversion_type, COUNT(*) as count, SUM(conversion_value) as total_value
                FROM conversions
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY conversion_type
            """, (start_time.isoformat(), end_time.isoformat()))
        elif group_by == 'campaign_id':
            cursor.execute("""
                SELECT campaign_id, COUNT(*) as count, SUM(conversion_value) as total_value
                FROM conversions
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY campaign_id
            """, (start_time.isoformat(), end_time.isoformat()))
        else:
            return {}

        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                'count': row[1],
                'total_value': row[2] or 0.0
            }

        return stats

    def get_total_revenue(
        self,
        start_time: datetime,
        end_time: datetime,
        conversion_type: Optional[str] = None
    ) -> float:
        """Get total revenue from conversions in time range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT SUM(conversion_value) as total
            FROM conversions
            WHERE created_at >= ? AND created_at <= ?
        """
        params = [start_time.isoformat(), end_time.isoformat()]

        if conversion_type:
            query += " AND conversion_type = ?"
            params.append(conversion_type)

        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] or 0.0

    def _row_to_conversion(self, row) -> Conversion:
        """Convert database row to Conversion entity."""
        import json
        from ...domain.value_objects.identifiers import ConversionId

        return Conversion(
            id=ConversionId.from_string(row["id"]),
            click_id=row["click_id"],
            campaign_id=row["campaign_id"],
            conversion_type=row["conversion_type"],
            conversion_value=row["conversion_value"],
            currency=row["currency"],
            status=row["status"],
            external_id=row["external_id"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
