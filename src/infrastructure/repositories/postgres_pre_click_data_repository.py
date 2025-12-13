import psycopg2
import json
import psycopg2.extras
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import functools
from loguru import logger

from ...domain.entities.pre_click_data import PreClickData
from ...domain.repositories.pre_click_data_repository import PreClickDataRepository
from ...domain.value_objects import ClickId, CampaignId


class PostgresPreClickDataRepository(PreClickDataRepository):
    """PostgreSQL implementation of PreClickDataRepository."""

    def __init__(self, container):
        logger.info(f"🟢 PostgresPreClickDataRepository.__init__ called - NEW CODE LOADED v2")
        logger.info(f"🔍 __init__ called from file: {__file__}")
        self._container = container
        self._db_initialized_event = asyncio.Event()  # Use asyncio.Event for lazy async initialization

    async def _get_blocking_connection(self):
        """Get a blocking database connection from the container pool in a thread pool."""
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            logger.warning("Attempted to get blocking connection outside of a running event loop. This might be a problem if not handled by a background task.")

        # Ensure pool is initialized in the async context, then get sync connection in executor
        await self._container.get_db_connection_pool()
        pool = self._container.get_db_connection_pool_sync()

        # Log pool state before attempting to get connection
        try:
            logger.info(f"🔍 Attempting to get connection from pool (id: {id(pool)})")
            logger.info(f"🔍 Pool type: {type(pool._pool).__name__}")
            logger.info(f"🔍 Pool config: minconn={getattr(pool._pool, '_minconn', '?')}, maxconn={getattr(pool._pool, '_maxconn', '?')}")

            # Get pool stats safely
            try:
                stats = pool.get_stats()
                logger.info(f"🔍 Pool stats BEFORE getconn: {stats}")
            except Exception as stats_error:
                logger.warning(f"Could not get pool stats: {stats_error}")

            # Attempt to get connection
            conn = await loop.run_in_executor(None, pool.getconn)
            logger.info(f"✅ Successfully got connection from pool")
            return conn

        except Exception as e:
            logger.error(f"❌ FAILED to get connection from pool!")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Exception message: {str(e)}")
            logger.error(f"❌ Pool instance id: {id(pool)}")
            logger.error(f"❌ Pool._pool type: {type(pool._pool).__name__}")

            # Try to get final stats
            try:
                final_stats = pool.get_stats()
                logger.error(f"❌ Pool stats AFTER failure: {final_stats}")
            except Exception as final_stats_error:
                logger.error(f"❌ Could not get final pool stats: {final_stats_error}")

            raise

    async def _initialize_db(self) -> None:
        """Initialize database schema (runs once in background)."""
        if self._db_initialized_event.is_set():
            logger.debug("Database schema already initialized (via event).")
            return

        conn = None
        try:
            logger.info("Starting database schema initialization for pre_click_data...")
            # Get a dedicated blocking connection for initialization
            conn = await self._get_blocking_connection()
            cursor = await asyncio.get_event_loop().run_in_executor(None, conn.cursor)
            
            logger.info("Attempting to create pre_click_data table if not exists...")
            await asyncio.get_event_loop().run_in_executor(None, functools.partial(cursor.execute, """
                CREATE TABLE IF NOT EXISTS pre_click_data (
                    click_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    tracking_params JSONB,
                    metadata JSONB
                )
            """))
            logger.info("Table pre_click_data created or already exists.")

            logger.info("Attempting to create indexes for pre_click_data table...")
            await asyncio.get_event_loop().run_in_executor(None, functools.partial(cursor.execute, "CREATE INDEX IF NOT EXISTS idx_pre_click_data_campaign_id ON pre_click_data(campaign_id)"))
            await asyncio.get_event_loop().run_in_executor(None, functools.partial(cursor.execute, "CREATE INDEX IF NOT EXISTS idx_pre_click_data_timestamp ON pre_click_data(timestamp)"))
            logger.info("Indexes for pre_click_data table created or already exist.")

            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info("Database schema initialization committed.")
            self._db_initialized_event.set()  # Mark as initialized
            logger.info("Database schema initialization completed.")
        except Exception as e:
            logger.error(f"Error initializing pre_click_data database schema: {e}", exc_info=True)
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, conn.rollback)  # Rollback on error
            # Even if initialization fails, set the event to prevent indefinite blocking,
            # but operations will likely fail later if the schema isn't right.
            self._db_initialized_event.set()
            raise
        finally:
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, functools.partial(self._container.get_db_connection_pool_sync().putconn, conn))

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
        logger.info(f"🟢 save() method called for click_id: {pre_click_data.click_id.value} - NEW CODE LOADED")
        await self._db_initialized_event.wait()  # Wait for DB to be initialized
        conn = None
        try:
            conn = await self._get_blocking_connection()
            cursor = await asyncio.get_event_loop().run_in_executor(None, conn.cursor)
            
            logger.info(f"Saving PreClickData for click_id: {pre_click_data.click_id.value}")
            await asyncio.get_event_loop().run_in_executor(None, functools.partial(cursor.execute, """
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
            )))
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info(f"PreClickData saved and committed for click_id: {pre_click_data.click_id.value}")
        except Exception as e:
            logger.error(f"Error saving PreClickData for click_id {pre_click_data.click_id.value}: {e}", exc_info=True)
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, conn.rollback)
            raise
        finally:
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, functools.partial(self._container.get_db_connection_pool_sync().putconn, conn))

    async def find_by_click_id(self, click_id: ClickId) -> Optional[PreClickData]:
        """Finds pre-click data by click ID."""
        await self._db_initialized_event.wait()  # Wait for DB to be initialized
        conn = None
        try:
            conn = await self._get_blocking_connection()
            cursor = await asyncio.get_event_loop().run_in_executor(None, functools.partial(conn.cursor, cursor_factory=psycopg2.extras.DictCursor))
            
            logger.info(f"Attempting to find PreClickData for click_id: {click_id.value}")
            await asyncio.get_event_loop().run_in_executor(None, functools.partial(cursor.execute, "SELECT * FROM pre_click_data WHERE click_id = %s", (click_id.value,)))

            row = await asyncio.get_event_loop().run_in_executor(None, cursor.fetchone)
            if row:
                pre_click_data = self._row_to_pre_click_data(dict(row))
                logger.info(f"PreClickData found for click_id: {click_id.value}. Data: {pre_click_data.tracking_params}")
                return pre_click_data
            logger.warning(f"No PreClickData found for click_id: {click_id.value} in DB.")
            return None
        except Exception as e:
            logger.error(f"Error finding PreClickData for click_id {click_id.value}: {e}", exc_info=True)
            raise
        finally:
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, functools.partial(self._container.get_db_connection_pool_sync().putconn, conn))

    async def delete_by_click_id(self, click_id: ClickId) -> None:
        """Deletes pre-click data by click ID."""
        await self._db_initialized_event.wait()  # Wait for DB to be initialized
        conn = None
        try:
            conn = await self._get_blocking_connection()
            cursor = await asyncio.get_event_loop().run_in_executor(None, conn.cursor)
            
            logger.info(f"Attempting to delete PreClickData for click_id: {click_id.value}")
            await asyncio.get_event_loop().run_in_executor(None, functools.partial(cursor.execute, "DELETE FROM pre_click_data WHERE click_id = %s", (click_id.value,)))
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info(f"PreClickData deleted and committed for click_id: {click_id.value}")
        except Exception as e:
            logger.error(f"Error deleting PreClickData for click_id {click_id.value}: {e}", exc_info=True)
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, conn.rollback)
            raise
        finally:
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, functools.partial(self._container.get_db_connection_pool_sync().putconn, conn))
