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

"""PostgreSQL landing page repository implementation."""

import psycopg2
from typing import Optional, List
from datetime import datetime

from ...domain.entities.landing_page import LandingPage
from ...domain.repositories.landing_page_repository import LandingPageRepository
from ...domain.value_objects import Url


class PostgresLandingPageRepository(LandingPageRepository):
    """PostgreSQL implementation of LandingPageRepository."""

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
                CREATE TABLE IF NOT EXISTS landing_pages (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    page_type TEXT NOT NULL,
                    weight INTEGER DEFAULT 100,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_control BOOLEAN DEFAULT FALSE,
                    impressions INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_landing_pages_campaign_id ON landing_pages(campaign_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_landing_pages_active ON landing_pages(is_active)")

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def _row_to_landing_page(self, row) -> LandingPage:
        """Convert database row to LandingPage entity."""
        return LandingPage(
            id=row["id"],
            campaign_id=row["campaign_id"],
            name=row["name"],
            url=Url(row["url"]),
            page_type=row["page_type"],
            weight=row["weight"],
            is_active=row["is_active"],
            is_control=row["is_control"],
            impressions=row["impressions"],
            clicks=row["clicks"],
            conversions=row["conversions"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save(self, landing_page: LandingPage) -> None:
        """Save a landing page."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO landing_pages
                (id, campaign_id, name, url, page_type, weight, is_active, is_control,
                 impressions, clicks, conversions, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    url = EXCLUDED.url,
                    page_type = EXCLUDED.page_type,
                    weight = EXCLUDED.weight,
                    is_active = EXCLUDED.is_active,
                    is_control = EXCLUDED.is_control,
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    conversions = EXCLUDED.conversions,
                    updated_at = EXCLUDED.updated_at
            """, (
                landing_page.id, landing_page.campaign_id, landing_page.name,
                landing_page.url.value, landing_page.page_type, landing_page.weight,
                landing_page.is_active, landing_page.is_control,
                landing_page.impressions, landing_page.clicks, landing_page.conversions,
                landing_page.created_at, landing_page.updated_at
            ))

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_id(self, landing_page_id: str) -> Optional[LandingPage]:
        """Get landing page by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM landing_pages WHERE id = %s", (landing_page_id,))

            row = cursor.fetchone()
            if row:
                # Convert tuple to dict for easier access
                columns = [desc[0] for desc in cursor.description]
                row_dict = dict(zip(columns, row))
                return self._row_to_landing_page(row_dict)
            return None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def find_by_campaign_id(self, campaign_id: str) -> List[LandingPage]:
        """Get landing pages by campaign ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM landing_pages
                WHERE campaign_id = %s
                ORDER BY weight DESC, created_at DESC
            """, (campaign_id,))

            landing_pages = []
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                landing_pages.append(self._row_to_landing_page(row_dict))

            return landing_pages
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def update(self, landing_page: LandingPage) -> None:
        """Update a landing page."""
        self.save(landing_page)  # UPSERT handles updates

    def delete_by_id(self, landing_page_id: str) -> bool:
        """Delete landing page by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM landing_pages WHERE id = %s", (landing_page_id,))

            deleted = cursor.rowcount > 0
            conn.commit()

            return deleted
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def exists_by_id(self, landing_page_id: str) -> bool:
        """Check if landing page exists by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM landing_pages WHERE id = %s", (landing_page_id,))

            return cursor.fetchone() is not None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def count_by_campaign_id(self, campaign_id: str) -> int:
        """Count landing pages by campaign ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM landing_pages WHERE campaign_id = %s", (campaign_id,))

            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            if conn:
                self._container.release_db_connection(conn)