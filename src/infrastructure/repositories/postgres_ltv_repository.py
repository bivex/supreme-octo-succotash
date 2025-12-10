"""PostgreSQL LTV repository implementation."""

import psycopg2
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...domain.entities.ltv import Cohort, CustomerLTV, LTVSegment
from ...domain.repositories.ltv_repository import LTVRepository


class PostgresLTVRepository(LTVRepository):
    """PostgreSQL implementation of LTVRepository."""

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
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create customer_ltv table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_ltv (
                customer_id TEXT PRIMARY KEY,
                total_revenue DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                total_purchases INTEGER NOT NULL DEFAULT 0,
                average_order_value DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                purchase_frequency DECIMAL(5,2) NOT NULL DEFAULT 0.0,
                customer_lifetime_months INTEGER NOT NULL DEFAULT 0,
                predicted_clv DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                actual_clv DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                segment TEXT NOT NULL DEFAULT 'unknown',
                cohort_id TEXT,
                first_purchase_date DATE,
                last_purchase_date DATE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create cohorts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cohorts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                acquisition_date DATE NOT NULL,
                customer_count INTEGER NOT NULL DEFAULT 0,
                total_revenue DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                average_ltv DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                retention_rates JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create ltv_segments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ltv_segments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                min_ltv DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                max_ltv DECIMAL(10,2),
                customer_count INTEGER NOT NULL DEFAULT 0,
                total_value DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                average_ltv DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                retention_rate DECIMAL(5,2) NOT NULL DEFAULT 0.0,
                description TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_ltv_segment ON customer_ltv(segment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_ltv_cohort ON customer_ltv(cohort_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_ltv_dates ON customer_ltv(first_purchase_date, last_purchase_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cohorts_acquisition ON cohorts(acquisition_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ltv_segments_min_ltv ON ltv_segments(min_ltv)")

        conn.commit()
        cursor.close()
        conn.close()

    def save_customer_ltv(self, customer_ltv: CustomerLTV) -> None:
        """Save customer LTV data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO customer_ltv
            (customer_id, total_revenue, total_purchases, average_order_value,
             purchase_frequency, customer_lifetime_months, predicted_clv, actual_clv,
             segment, cohort_id, first_purchase_date, last_purchase_date,
             created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue,
                total_purchases = EXCLUDED.total_purchases,
                average_order_value = EXCLUDED.average_order_value,
                purchase_frequency = EXCLUDED.purchase_frequency,
                customer_lifetime_months = EXCLUDED.customer_lifetime_months,
                predicted_clv = EXCLUDED.predicted_clv,
                actual_clv = EXCLUDED.actual_clv,
                segment = EXCLUDED.segment,
                cohort_id = EXCLUDED.cohort_id,
                first_purchase_date = EXCLUDED.first_purchase_date,
                last_purchase_date = EXCLUDED.last_purchase_date,
                updated_at = CURRENT_TIMESTAMP
        """, (
            customer_ltv.customer_id,
            float(customer_ltv.total_revenue.amount),
            customer_ltv.total_purchases,
            float(customer_ltv.average_order_value.amount),
            customer_ltv.purchase_frequency,
            customer_ltv.customer_lifetime_months,
            float(customer_ltv.predicted_clv.amount),
            float(customer_ltv.actual_clv.amount),
            customer_ltv.segment,
            customer_ltv.cohort_id,
            customer_ltv.first_purchase_date.date(),
            customer_ltv.last_purchase_date.date(),
            customer_ltv.created_at,
            customer_ltv.updated_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_customer_ltv(self, customer_id: str) -> Optional[CustomerLTV]:
        """Get customer LTV by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM customer_ltv WHERE customer_id = %s", (customer_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return self._row_to_customer_ltv(row) if row else None

    def get_customers_by_segment(self, segment: str, limit: int = 100) -> List[CustomerLTV]:
        """Get customers by LTV segment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customer_ltv
            WHERE segment = %s
            ORDER BY predicted_clv DESC
            LIMIT %s
        """, (segment, limit))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_customer_ltv(row) for row in rows]

    def get_customers_by_cohort(self, cohort_id: str) -> List[CustomerLTV]:
        """Get customers by cohort ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customer_ltv
            WHERE cohort_id = %s
            ORDER BY predicted_clv DESC
        """, (cohort_id,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_customer_ltv(row) for row in rows]

    def save_cohort(self, cohort: Cohort) -> None:
        """Save cohort data."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO cohorts
            (id, name, acquisition_date, customer_count, total_revenue,
             average_ltv, retention_rates, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                acquisition_date = EXCLUDED.acquisition_date,
                customer_count = EXCLUDED.customer_count,
                total_revenue = EXCLUDED.total_revenue,
                average_ltv = EXCLUDED.average_ltv,
                retention_rates = EXCLUDED.retention_rates,
                updated_at = CURRENT_TIMESTAMP
        """, (
            cohort.id,
            cohort.name,
            cohort.acquisition_date,
            cohort.customer_count,
            float(cohort.total_revenue.amount),
            float(cohort.average_ltv.amount),
            json.dumps(cohort.retention_rates),
            cohort.created_at,
            cohort.updated_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_cohort(self, cohort_id: str) -> Optional[Cohort]:
        """Get cohort by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cohorts WHERE id = %s", (cohort_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return self._row_to_cohort(row) if row else None

    def get_all_cohorts(self, limit: int = 100) -> List[Cohort]:
        """Get all cohorts."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM cohorts
            ORDER BY acquisition_date DESC
            LIMIT %s
        """, (limit,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_cohort(row) for row in rows]

    def save_ltv_segment(self, segment: LTVSegment) -> None:
        """Save LTV segment data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ltv_segments
            (id, name, min_ltv, max_ltv, customer_count, total_value,
             average_ltv, retention_rate, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                min_ltv = EXCLUDED.min_ltv,
                max_ltv = EXCLUDED.max_ltv,
                customer_count = EXCLUDED.customer_count,
                total_value = EXCLUDED.total_value,
                average_ltv = EXCLUDED.average_ltv,
                retention_rate = EXCLUDED.retention_rate,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
        """, (
            segment.id,
            segment.name,
            float(segment.min_ltv.amount) if segment.min_ltv else 0.0,
            float(segment.max_ltv.amount) if segment.max_ltv else None,
            segment.customer_count,
            float(segment.total_value.amount),
            float(segment.average_ltv.amount),
            segment.retention_rate,
            segment.description,
            segment.created_at,
            segment.updated_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_ltv_segment(self, segment_id: str) -> Optional[LTVSegment]:
        """Get LTV segment by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ltv_segments WHERE id = %s", (segment_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return self._row_to_ltv_segment(row) if row else None

    def get_all_ltv_segments(self) -> List[LTVSegment]:
        """Get all LTV segments."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ltv_segments ORDER BY min_ltv DESC")

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_ltv_segment(row) for row in rows]

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
            WHERE first_purchase_date >= %s AND first_purchase_date <= %s
        """, (start_date.date(), end_date.date()))

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
            WHERE first_purchase_date >= %s AND first_purchase_date <= %s
            GROUP BY segment
            ORDER BY avg_clv DESC
        """, (start_date.date(), end_date.date()))

        analytics['segment_distribution'] = [
            {'segment': row[0], 'count': row[1], 'avg_clv': float(row[2])}
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return analytics

    def _row_to_customer_ltv(self, row) -> CustomerLTV:
        """Convert database row to CustomerLTV entity."""
        from ...value_objects.financial import Money

        return CustomerLTV(
            customer_id=row[0],
            total_revenue=Money.from_float(row[1], "USD"),
            total_purchases=row[2],
            average_order_value=Money.from_float(row[3], "USD"),
            purchase_frequency=row[4],
            customer_lifetime_months=row[5],
            predicted_clv=Money.from_float(row[6], "USD"),
            actual_clv=Money.from_float(row[7], "USD"),
            segment=row[8],
            cohort_id=row[9],
            first_purchase_date=datetime.combine(row[10], datetime.min.time()) if row[10] else datetime.now(),
            last_purchase_date=datetime.combine(row[11], datetime.min.time()) if row[11] else datetime.now(),
            created_at=row[12],
            updated_at=row[13]
        )

    def _row_to_cohort(self, row) -> Cohort:
        """Convert database row to Cohort entity."""
        import json
        from ...value_objects.financial import Money

        return Cohort(
            id=row[0],
            name=row[1],
            acquisition_date=row[2],
            customer_count=row[3],
            total_revenue=Money.from_float(row[4], "USD"),
            average_ltv=Money.from_float(row[5], "USD"),
            retention_rates=json.loads(row[6]) if row[6] else {},
            created_at=row[7],
            updated_at=row[8]
        )

    def _row_to_ltv_segment(self, row) -> LTVSegment:
        """Convert database row to LTVSegment entity."""
        from ...value_objects.financial import Money

        return LTVSegment(
            id=row[0],
            name=row[1],
            min_ltv=Money.from_float(row[2], "USD") if row[2] else Money.from_float(0, "USD"),
            max_ltv=Money.from_float(row[3], "USD") if row[3] else None,
            customer_count=row[4],
            total_value=Money.from_float(row[5], "USD"),
            average_ltv=Money.from_float(row[6], "USD"),
            retention_rate=row[7],
            description=row[8],
            created_at=row[9],
            updated_at=row[10]
        )
