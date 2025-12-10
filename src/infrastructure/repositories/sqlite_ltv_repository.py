"""SQLite LTV repository implementation."""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...domain.entities.ltv import Cohort, CustomerLTV, LTVSegment
from ...domain.repositories.ltv_repository import LTVRepository


class SQLiteLTVRepository(LTVRepository):
    """SQLite implementation of LTVRepository for stress testing."""

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

        # Create customer_ltv table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_ltv (
                customer_id TEXT PRIMARY KEY,
                total_revenue REAL NOT NULL,
                total_purchases INTEGER NOT NULL,
                average_order_value REAL NOT NULL,
                purchase_frequency REAL NOT NULL,
                customer_lifetime_months INTEGER NOT NULL,
                predicted_clv REAL NOT NULL,
                actual_clv REAL NOT NULL,
                segment TEXT NOT NULL,
                cohort_id TEXT,
                first_purchase_date TEXT NOT NULL,
                last_purchase_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create cohorts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cohorts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                acquisition_date TEXT NOT NULL,
                customer_count INTEGER NOT NULL,
                total_revenue REAL NOT NULL,
                average_ltv REAL NOT NULL,
                retention_rates TEXT NOT NULL,  -- JSON string
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create ltv_segments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ltv_segments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                min_ltv REAL NOT NULL,
                max_ltv REAL,
                customer_count INTEGER NOT NULL,
                total_value REAL NOT NULL,
                average_ltv REAL NOT NULL,
                retention_rate REAL NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_ltv_segment ON customer_ltv(segment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_ltv_cohort ON customer_ltv(cohort_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cohorts_acquisition ON cohorts(acquisition_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ltv_segments_min_ltv ON ltv_segments(min_ltv)")

        conn.commit()

    def save_customer_ltv(self, customer_ltv: CustomerLTV) -> None:
        """Save customer LTV data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO customer_ltv
            (customer_id, total_revenue, total_purchases, average_order_value,
             purchase_frequency, customer_lifetime_months, predicted_clv, actual_clv,
             segment, cohort_id, first_purchase_date, last_purchase_date,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_ltv.customer_id,
            customer_ltv.total_revenue.amount,
            customer_ltv.total_purchases,
            customer_ltv.average_order_value.amount,
            customer_ltv.purchase_frequency,
            customer_ltv.customer_lifetime_months,
            customer_ltv.predicted_clv.amount,
            customer_ltv.actual_clv.amount,
            customer_ltv.segment,
            customer_ltv.cohort_id,
            customer_ltv.first_purchase_date.isoformat(),
            customer_ltv.last_purchase_date.isoformat(),
            customer_ltv.created_at.isoformat(),
            customer_ltv.updated_at.isoformat()
        ))

        conn.commit()

    def get_customer_ltv(self, customer_id: str) -> Optional[CustomerLTV]:
        """Get customer LTV by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM customer_ltv WHERE customer_id = ?", (customer_id,))

        row = cursor.fetchone()
        return self._row_to_customer_ltv(row) if row else None

    def get_customers_by_segment(self, segment: str, limit: int = 100) -> List[CustomerLTV]:
        """Get customers by LTV segment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customer_ltv
            WHERE segment = ?
            ORDER BY predicted_clv DESC
            LIMIT ?
        """, (segment, limit))

        return [self._row_to_customer_ltv(row) for row in cursor.fetchall()]

    def get_customers_by_cohort(self, cohort_id: str) -> List[CustomerLTV]:
        """Get customers by cohort ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customer_ltv
            WHERE cohort_id = ?
            ORDER BY predicted_clv DESC
        """, (cohort_id,))

        return [self._row_to_customer_ltv(row) for row in cursor.fetchall()]

    def save_cohort(self, cohort: Cohort) -> None:
        """Save cohort data."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO cohorts
            (id, name, acquisition_date, customer_count, total_revenue,
             average_ltv, retention_rates, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cohort.id,
            cohort.name,
            cohort.acquisition_date.isoformat(),
            cohort.customer_count,
            cohort.total_revenue.amount,
            cohort.average_ltv.amount,
            json.dumps(cohort.retention_rates),
            cohort.created_at.isoformat(),
            cohort.updated_at.isoformat()
        ))

        conn.commit()

    def get_cohort(self, cohort_id: str) -> Optional[Cohort]:
        """Get cohort by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cohorts WHERE id = ?", (cohort_id,))

        row = cursor.fetchone()
        return self._row_to_cohort(row) if row else None

    def get_all_cohorts(self, limit: int = 100) -> List[Cohort]:
        """Get all cohorts."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM cohorts
            ORDER BY acquisition_date DESC
            LIMIT ?
        """, (limit,))

        return [self._row_to_cohort(row) for row in cursor.fetchall()]

    def save_ltv_segment(self, segment: LTVSegment) -> None:
        """Save LTV segment data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO ltv_segments
            (id, name, min_ltv, max_ltv, customer_count, total_value,
             average_ltv, retention_rate, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            segment.id,
            segment.name,
            segment.min_ltv.amount,
            segment.max_ltv.amount if segment.max_ltv else None,
            segment.customer_count,
            segment.total_value.amount,
            segment.average_ltv.amount,
            segment.retention_rate,
            segment.description,
            segment.created_at.isoformat(),
            segment.updated_at.isoformat()
        ))

        conn.commit()

    def get_ltv_segment(self, segment_id: str) -> Optional[LTVSegment]:
        """Get LTV segment by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ltv_segments WHERE id = ?", (segment_id,))

        row = cursor.fetchone()
        return self._row_to_ltv_segment(row) if row else None

    def get_all_ltv_segments(self) -> List[LTVSegment]:
        """Get all LTV segments."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ltv_segments ORDER BY min_ltv DESC")

        return [self._row_to_ltv_segment(row) for row in cursor.fetchall()]

    def get_ltv_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get LTV analytics for date range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get total metrics
        cursor.execute("""
            SELECT
                COUNT(*) as total_customers,
                SUM(predicted_clv) as total_predicted_clv,
                AVG(predicted_clv) as avg_predicted_clv,
                SUM(actual_clv) as total_actual_clv,
                AVG(actual_clv) as avg_actual_clv
            FROM customer_ltv
            WHERE first_purchase_date >= ? AND first_purchase_date <= ?
        """, (start_date.isoformat(), end_date.isoformat()))

        row = cursor.fetchone()
        analytics = {
            'total_customers': row[0] or 0,
            'total_predicted_clv': row[1] or 0.0,
            'avg_predicted_clv': row[2] or 0.0,
            'total_actual_clv': row[3] or 0.0,
            'avg_actual_clv': row[4] or 0.0,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }

        # Get segment distribution
        cursor.execute("""
            SELECT segment, COUNT(*) as count, AVG(predicted_clv) as avg_clv
            FROM customer_ltv
            WHERE first_purchase_date >= ? AND first_purchase_date <= ?
            GROUP BY segment
            ORDER BY avg_clv DESC
        """, (start_date.isoformat(), end_date.isoformat()))

        analytics['segment_distribution'] = [
            {'segment': row[0], 'count': row[1], 'avg_clv': row[2]}
            for row in cursor.fetchall()
        ]

        return analytics

    def _row_to_customer_ltv(self, row) -> CustomerLTV:
        """Convert database row to CustomerLTV entity."""
        from ...value_objects.financial import Money

        return CustomerLTV(
            customer_id=row["customer_id"],
            total_revenue=Money.from_float(row["total_revenue"], "USD"),
            total_purchases=row["total_purchases"],
            average_order_value=Money.from_float(row["average_order_value"], "USD"),
            purchase_frequency=row["purchase_frequency"],
            customer_lifetime_months=row["customer_lifetime_months"],
            predicted_clv=Money.from_float(row["predicted_clv"], "USD"),
            actual_clv=Money.from_float(row["actual_clv"], "USD"),
            segment=row["segment"],
            cohort_id=row["cohort_id"],
            first_purchase_date=datetime.fromisoformat(row["first_purchase_date"]),
            last_purchase_date=datetime.fromisoformat(row["last_purchase_date"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

    def _row_to_cohort(self, row) -> Cohort:
        """Convert database row to Cohort entity."""
        import json
        from ...value_objects.financial import Money

        return Cohort(
            id=row["id"],
            name=row["name"],
            acquisition_date=datetime.fromisoformat(row["acquisition_date"]),
            customer_count=row["customer_count"],
            total_revenue=Money.from_float(row["total_revenue"], "USD"),
            average_ltv=Money.from_float(row["average_ltv"], "USD"),
            retention_rates=json.loads(row["retention_rates"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

    def _row_to_ltv_segment(self, row) -> LTVSegment:
        """Convert database row to LTVSegment entity."""
        from ...value_objects.financial import Money

        return LTVSegment(
            id=row["id"],
            name=row["name"],
            min_ltv=Money.from_float(row["min_ltv"], "USD"),
            max_ltv=Money.from_float(row["max_ltv"], "USD") if row["max_ltv"] else None,
            customer_count=row["customer_count"],
            total_value=Money.from_float(row["total_value"], "USD"),
            average_ltv=Money.from_float(row["average_ltv"], "USD"),
            retention_rate=row["retention_rate"],
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
