"""LTV (Lifetime Value) domain service."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import math

from ...entities.ltv import Cohort, CustomerLTV, LTVSegment
from ...entities.conversion import Conversion
from ...value_objects.financial import Money


class LTVService:
    """Domain service for LTV calculations and analysis."""

    def __init__(self):
        pass

    def calculate_customer_ltv(self, conversions: List[Conversion],
                              first_purchase_date: datetime,
                              last_purchase_date: datetime) -> CustomerLTV:
        """
        Calculate Customer Lifetime Value based on conversion history.

        Uses historical LTV formula: LTV = (Average Order Value × Purchase Frequency) × Customer Lifespan
        """
        if not conversions:
            # Return zero LTV for customers with no conversions
            zero_money = Money.from_float(0.0, "USD")
            return CustomerLTV(
                customer_id="",  # Will be set by caller
                total_revenue=zero_money,
                total_purchases=0,
                average_order_value=zero_money,
                purchase_frequency=0.0,
                customer_lifetime_months=0,
                predicted_clv=zero_money,
                actual_clv=zero_money,
                segment="unknown",
                cohort_id=None,
                first_purchase_date=first_purchase_date,
                last_purchase_date=last_purchase_date,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

        # Calculate basic metrics
        total_revenue = sum(conv.conversion_value for conv in conversions)
        total_purchases = len(conversions)
        currency = conversions[0].currency if conversions else "USD"

        avg_order_value = total_revenue / total_purchases if total_purchases > 0 else 0.0

        # Calculate customer lifespan in months
        lifespan_days = (last_purchase_date - first_purchase_date).days
        lifespan_months = max(1, lifespan_days // 30)  # At least 1 month

        # Calculate purchase frequency (purchases per month)
        purchase_frequency = total_purchases / lifespan_months if lifespan_months > 0 else 0

        # Calculate actual CLV (historical)
        actual_clv = total_revenue

        # Calculate predicted CLV using standard formula
        # CLV = (Average Order Value × Purchase Frequency) × Customer Lifespan
        predicted_clv = avg_order_value * purchase_frequency * lifespan_months

        # Determine segment based on CLV
        segment = self._determine_ltv_segment(predicted_clv)

        return CustomerLTV(
            customer_id="",  # Will be set by caller
            total_revenue=Money.from_float(float(total_revenue), currency),
            total_purchases=total_purchases,
            average_order_value=Money.from_float(float(avg_order_value), currency),
            purchase_frequency=purchase_frequency,
            customer_lifetime_months=lifespan_months,
            predicted_clv=Money.from_float(float(predicted_clv), currency),
            actual_clv=Money.from_float(float(actual_clv), currency),
            segment=segment,
            cohort_id=None,  # Will be set by caller
            first_purchase_date=first_purchase_date,
            last_purchase_date=last_purchase_date,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def create_cohort_analysis(self, customers: List[CustomerLTV],
                              cohort_period: str = "monthly") -> List[Cohort]:
        """
        Create cohort analysis from customer LTV data.

        Args:
            customers: List of customer LTV data
            cohort_period: "monthly" or "quarterly"

        Returns:
            List of Cohort objects with retention analysis
        """
        if not customers:
            return []

        # Group customers by acquisition month
        cohort_groups = {}
        for customer in customers:
            if cohort_period == "monthly":
                cohort_key = customer.first_purchase_date.strftime("%Y-%m")
                cohort_name = f"Cohort {cohort_key}"
            else:  # quarterly
                quarter = ((customer.first_purchase_date.month - 1) // 3) + 1
                cohort_key = f"{customer.first_purchase_date.year}-Q{quarter}"
                cohort_name = f"Cohort {cohort_key}"

            if cohort_key not in cohort_groups:
                cohort_groups[cohort_key] = {
                    'name': cohort_name,
                    'customers': [],
                    'acquisition_date': customer.first_purchase_date.replace(day=1)
                }
            cohort_groups[cohort_key]['customers'].append(customer)

        cohorts = []
        for cohort_key, data in cohort_groups.items():
            customers_in_cohort = data['customers']

            # Calculate cohort metrics
            total_revenue = sum(c.total_revenue.amount for c in customers_in_cohort)
            avg_ltv = total_revenue / len(customers_in_cohort) if customers_in_cohort else 0

            currency = customers_in_cohort[0].total_revenue.currency if customers_in_cohort else "USD"

            # Calculate retention rates (simplified)
            retention_rates = self._calculate_retention_rates(customers_in_cohort, data['acquisition_date'])

            cohort = Cohort(
                id=f"cohort_{cohort_key}",
                name=data['name'],
                acquisition_date=data['acquisition_date'],
                customer_count=len(customers_in_cohort),
                total_revenue=Money.from_float(total_revenue, currency),
                average_ltv=Money.from_float(avg_ltv, currency),
                retention_rates=retention_rates,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            cohorts.append(cohort)

        return sorted(cohorts, key=lambda x: x.acquisition_date)

    def create_ltv_segments(self, customers: List[CustomerLTV],
                           segment_config: Optional[Dict] = None) -> List[LTVSegment]:
        """
        Create LTV segments from customer data.

        Args:
            customers: List of customer LTV data
            segment_config: Optional custom segment configuration

        Returns:
            List of LTV segments
        """
        if not customers:
            return []

        # Default segment configuration
        if segment_config is None:
            segment_config = {
                'segments': [
                    {'name': 'Low Value', 'min': 0, 'max': 50},
                    {'name': 'Medium Value', 'min': 50, 'max': 200},
                    {'name': 'High Value', 'min': 200, 'max': 1000},
                    {'name': 'VIP', 'min': 1000, 'max': None}
                ]
            }

        segments = []
        currency = customers[0].predicted_clv.currency if customers else "USD"

        for seg_config in segment_config['segments']:
            min_ltv = Money.from_float(seg_config['min'], currency)
            max_ltv = Money.from_float(seg_config['max'], currency) if seg_config['max'] else None

            # Filter customers in this segment
            segment_customers = [
                c for c in customers
                if (c.predicted_clv.amount >= min_ltv.amount and
                    (max_ltv is None or c.predicted_clv.amount < max_ltv.amount))
            ]

            if segment_customers:
                total_value = sum(c.predicted_clv.amount for c in segment_customers)
                avg_ltv = total_value / len(segment_customers)

                # Calculate retention rate for segment (simplified)
                retention_rate = sum(1 for c in segment_customers if c.is_active_customer) / len(segment_customers)

                segment = LTVSegment(
                    id=f"segment_{seg_config['name'].lower().replace(' ', '_')}",
                    name=seg_config['name'],
                    min_ltv=min_ltv,
                    max_ltv=max_ltv,
                    customer_count=len(segment_customers),
                    total_value=Money.from_float(total_value, currency),
                    average_ltv=Money.from_float(avg_ltv, currency),
                    retention_rate=retention_rate,
                    description=f"Customers with LTV {min_ltv.amount}{'+' if max_ltv is None else f'-{max_ltv.amount}'} {currency}",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                segments.append(segment)

        return segments

    def predict_customer_lifetime(self, customer: CustomerLTV,
                                historical_data: List[CustomerLTV]) -> int:
        """
        Predict customer lifetime in months using historical patterns.

        Uses survival analysis approach based on similar customers.
        """
        if not historical_data:
            return customer.customer_lifetime_months

        # Find similar customers by segment and purchase frequency
        similar_customers = [
            c for c in historical_data
            if (c.segment == customer.segment and
                abs(c.purchase_frequency - customer.purchase_frequency) < 0.5)
        ]

        if not similar_customers:
            return customer.customer_lifetime_months

        # Calculate average lifetime of similar customers
        avg_lifetime = sum(c.customer_lifetime_months for c in similar_customers) / len(similar_customers)

        # Apply some predictive adjustment based on recency
        recency_factor = min(1.0, customer.days_since_last_purchase / 90.0)
        predicted_lifetime = int(avg_lifetime * (1 - recency_factor * 0.3))

        return max(1, predicted_lifetime)

    def _determine_ltv_segment(self, clv_amount: float) -> str:
        """Determine LTV segment based on CLV amount."""
        if clv_amount >= 1000:
            return "vip"
        elif clv_amount >= 200:
            return "high_value"
        elif clv_amount >= 50:
            return "medium_value"
        else:
            return "low_value"

    def _calculate_retention_rates(self, customers: List[CustomerLTV],
                                  cohort_start: datetime) -> Dict[str, float]:
        """Calculate retention rates for different periods."""
        retention_rates = {}

        periods = [1, 3, 6, 12]  # months
        for months in periods:
            period_end = cohort_start + timedelta(days=months * 30)

            retained_customers = [
                c for c in customers
                if c.last_purchase_date >= period_end
            ]

            retention_rate = len(retained_customers) / len(customers) if customers else 0.0
            retention_rates[f"{months}m"] = retention_rate

        return retention_rates
