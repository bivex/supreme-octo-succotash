import psycopg2
import json
import psycopg2.extras
from typing import Optional, Dict, Any
from datetime import datetime

from ...domain.entities.pre_click_data import PreClickData
from ...domain.repositories.pre_click_data_repository import PreClickDataRepository
from ...domain.value_objects import ClickId, CampaignId


class PostgresPreClickDataRepository(PreClickDataRepository):
    """PostgreSQL implementation of PreClickDataRepository."""

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
            CREATE TABLE IF NOT EXISTS pre_click_data (
                click_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                tracking_params JSONB,
                metadata JSONB
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pre_click_data_campaign_id ON pre_click_data(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pre_click_data_timestamp ON pre_click_data(timestamp)")

        conn.commit()

    def _row_to_pre_click_data(self, row: Dict[str, Any]) -> PreClickData:
        """Convert database row to PreClickData entity."""
        return PreClickData(
            click_id=ClickId(row["click_id"]),
            campaign_id=CampaignId(row["campaign_id"]),
            timestamp=row["timestamp"],
            tracking_params=row["tracking_params"],
            metadata=row["metadata"],
        )

    async def save(self, pre_click_data: PreClickData) -> None:
        """Saves pre-click data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pre_click_data
            (click_id, campaign_id, timestamp, tracking_params, metadata)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (click_id) DO UPDATE SET
                campaign_id = EXCLUDED.campaign_id,
                timestamp = EXCLUDED.timestamp,
                tracking_params = EXCLUDED.tracking_params,
                metadata = EXCLUDED.metadata
        """, (
            pre_click_data.click_id.value,
            pre_click_data.campaign_id.value,
            pre_click_data.timestamp,
            json.dumps(pre_click_data.tracking_params),
            json.dumps(pre_click_data.metadata)
        ))

        conn.commit()

    async def find_by_click_id(self, click_id: ClickId) -> Optional[PreClickData]:
        """Finds pre-click data by click ID."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute("SELECT * FROM pre_click_data WHERE click_id = %s", (click_id.value,))

        row = cursor.fetchone()
        if row:
            return self._row_to_pre_click_data(dict(row))
        return None

    async def delete_by_click_id(self, click_id: ClickId) -> None:
        """Deletes pre-click data by click ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM pre_click_data WHERE click_id = %s", (click_id.value,))
        conn.commit()
