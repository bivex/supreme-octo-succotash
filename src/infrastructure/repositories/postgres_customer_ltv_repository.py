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

"""PostgreSQL Customer LTV repository implementation."""

import psycopg2
from typing import Optional
from ...domain.entities.customer_ltv import CustomerLtv
from ...domain.repositories.customer_ltv_repository import CustomerLtvRepository


class PostgresCustomerLtvRepository(CustomerLtvRepository):
    """PostgreSQL implementation of CustomerLtvRepository."""

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
        """Initialize database schema if needed."""
        # Table should already exist from the main LTV repository
        pass

    def save(self, customer_ltv: CustomerLtv) -> None:
        """Save customer LTV data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO customer_ltv (
                    customer_id, total_revenue, total_purchases, average_order_value,
                    purchase_frequency, customer_lifetime_months, predicted_clv,
                    actual_clv, segment, cohort_id, first_purchase_date,
                    last_purchase_date, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    updated_at = EXCLUDED.updated_at
            """, (
                customer_ltv.customer_id,
                customer_ltv.total_revenue,
                customer_ltv.total_purchases,
                customer_ltv.average_order_value,
                customer_ltv.purchase_frequency,
                customer_ltv.customer_lifetime_months,
                customer_ltv.predicted_clv,
                customer_ltv.actual_clv,
                customer_ltv.segment,
                customer_ltv.cohort_id,
                customer_ltv.first_purchase_date,
                customer_ltv.last_purchase_date,
                customer_ltv.created_at,
                customer_ltv.updated_at
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def find_by_customer_id(self, customer_id: str) -> Optional[CustomerLtv]:
        """Get customer LTV by customer ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT customer_id, total_revenue, total_purchases, average_order_value,
                       purchase_frequency, customer_lifetime_months, predicted_clv,
                       actual_clv, segment, cohort_id, first_purchase_date,
                       last_purchase_date, created_at, updated_at
                FROM customer_ltv
                WHERE customer_id = %s
            """, (customer_id,))

            row = cursor.fetchone()
            if row:
                return CustomerLtv(
                    customer_id=row[0],
                    total_revenue=row[1],
                    total_purchases=row[2],
                    average_order_value=row[3],
                    purchase_frequency=row[4],
                    customer_lifetime_months=row[5],
                    predicted_clv=row[6],
                    actual_clv=row[7],
                    segment=row[8],
                    cohort_id=row[9],
                    first_purchase_date=row[10],
                    last_purchase_date=row[11],
                    created_at=row[12],
                    updated_at=row[13]
                )
            return None

        finally:
            cursor.close()

    def update_revenue(self, customer_id: str, additional_revenue: float) -> None:
        """Update customer total revenue."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE customer_ltv
                SET total_revenue = total_revenue + %s,
                    total_purchases = total_purchases + 1,
                    average_order_value = (total_revenue + %s) / (total_purchases + 1),
                    actual_clv = total_revenue + %s,
                    last_purchase_date = CURRENT_DATE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = %s
            """, (additional_revenue, additional_revenue, additional_revenue, customer_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()