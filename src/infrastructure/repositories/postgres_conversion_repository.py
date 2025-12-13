"""PostgreSQL conversion repository implementation."""

import psycopg2
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...domain.entities.conversion import Conversion
from ...domain.repositories.conversion_repository import ConversionRepository

# Custom JSON encoder to handle Money and datetime objects
import json
from datetime import datetime
from decimal import Decimal

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        # Handle Money objects
        try:
            from ...domain.value_objects.financial.money import Money
            if isinstance(obj, Money):
                return {
                    "amount": float(obj.amount),
                    "currency": obj.currency
                }
        except ImportError:
            pass
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class PostgresConversionRepository(ConversionRepository):
    """PostgreSQL implementation of ConversionRepository."""

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
        from ..value_objects.financial.money import Money

        # Handle conversion value
        conversion_value = None
        if row["conversion_value"] and float(row["conversion_value"]) > 0:
            conversion_value = Money(
                amount=float(row["conversion_value"]),
                currency=row["currency"] or "USD"
            )

        # Extract metadata fields
        metadata = row["metadata"] or {}

        return Conversion(
            id=row["id"],
            click_id=row["click_id"],
            conversion_type=row["conversion_type"],
            conversion_value=conversion_value,
            order_id=metadata.get('order_id'),
            product_id=metadata.get('product_id'),
            campaign_id=int(row["campaign_id"]) if row["campaign_id"] else None,
            offer_id=metadata.get('offer_id'),
            landing_page_id=metadata.get('landing_page_id'),
            user_id=metadata.get('user_id'),
            session_id=metadata.get('session_id'),
            ip_address=metadata.get('ip_address'),
            user_agent=metadata.get('user_agent'),
            referrer=metadata.get('referrer'),
            metadata=metadata,
            timestamp=row["created_at"],
            processed=row["status"] == "processed",
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save(self, conversion: Conversion) -> None:
        """Save a conversion."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        # Prepare database fields from entity
        conversion_value = conversion.conversion_value.amount if conversion.conversion_value else 0.0
        currency = conversion.conversion_value.currency if conversion.conversion_value else "USD"
        status = "processed" if conversion.processed else "pending"
        external_id = conversion.order_id  # Use order_id as external_id

        # Store additional fields in metadata
        metadata = conversion.metadata.copy() if conversion.metadata else {}
        metadata.update({
            'order_id': conversion.order_id,
            'product_id': conversion.product_id,
            'offer_id': conversion.offer_id,
            'landing_page_id': conversion.landing_page_id,
            'user_id': conversion.user_id,
            'session_id': conversion.session_id,
            'ip_address': conversion.ip_address,
            'user_agent': conversion.user_agent,
            'referrer': conversion.referrer,
        })

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
            conversion.id, conversion.click_id, str(conversion.campaign_id) if conversion.campaign_id else None,
            conversion.conversion_type, conversion_value,
            currency, status, external_id,
            json.dumps(metadata, cls=CustomJSONEncoder), conversion.created_at, conversion.updated_at
        ))

        conn.commit()

    def get_by_id(self, conversion_id: str) -> Optional[Conversion]:
        """Get conversion by ID."""
        conn = self._container.get_db_connection()
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
        conn = self._container.get_db_connection()
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
        conn = self._container.get_db_connection()
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
        conn = self._container.get_db_connection()
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
        conn = self._container.get_db_connection()
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
        conn = self._container.get_db_connection()
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
        conn = self._container.get_db_connection()
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
        conn = self._container.get_db_connection()
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
