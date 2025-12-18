# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Cohort analysis handler."""

from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger

from ...domain.repositories.ltv_repository import LTVRepository
from ...domain.services.ltv.ltv_service import LTVService


class CohortAnalysisHandler:
    """Handler for cohort analysis operations."""

    def __init__(self, ltv_repository: LTVRepository):
        self._ltv_repository = ltv_repository
        self._ltv_service = LTVService()

    def get_cohort_analysis(self, period: str = "monthly",
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get comprehensive cohort analysis.

        Args:
            period: Analysis period ("monthly" or "quarterly")
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)

        Returns:
            Dict containing cohort analysis data
        """
        try:
            logger.info(f"Generating cohort analysis for period: {period}")

            # Use provided dates or default to last 12 months
            if not start_date:
                start_date = datetime.now().replace(day=1, month=datetime.now().month - 11)
            if not end_date:
                end_date = datetime.now()

            # Get all customer LTV data for analysis
            # In a real implementation, we'd have a method to get customers within date range
            # For now, we'll get all customers and filter by date
            all_customers = []
            segments = ["vip", "high_value", "medium_value", "low_value"]

            for segment in segments:
                customers = self._ltv_repository.get_customers_by_segment(segment, limit=1000)
                all_customers.extend(customers)

            # Filter customers by date range
            filtered_customers = [
                c for c in all_customers
                if start_date <= c.first_purchase_date <= end_date
            ]

            if not filtered_customers:
                return {
                    "status": "no_data",
                    "message": "No customer data found for the specified date range",
                    "period": period,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                }

            # Create cohort analysis
            cohorts = self._ltv_service.create_cohort_analysis(filtered_customers, period)

            # Format cohort data
            cohort_data = []
            for cohort in cohorts:
                cohort_data.append({
                    "cohort_id": cohort.id,
                    "cohort_name": cohort.name,
                    "acquisition_date": cohort.acquisition_date.isoformat(),
                    "customer_count": cohort.customer_count,
                    "total_revenue": float(cohort.total_revenue.amount),
                    "average_ltv": float(cohort.average_ltv.amount),
                    "retention_rates": cohort.retention_rates,
                    "currency": cohort.total_revenue.currency
                })

            # Calculate overall metrics
            total_customers = sum(cohort.customer_count for cohort in cohorts)
            total_revenue = sum(cohort.total_revenue.amount for cohort in cohorts)
            avg_ltv = total_revenue / total_customers if total_customers > 0 else 0

            result = {
                "status": "success",
                "period": period,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {
                    "total_cohorts": len(cohorts),
                    "total_customers": total_customers,
                    "total_revenue": total_revenue,
                    "average_ltv": avg_ltv,
                    "currency": cohorts[0].total_revenue.currency if cohorts else "USD"
                },
                "cohorts": cohort_data
            }

            logger.info(f"Cohort analysis generated: {len(cohorts)} cohorts, {total_customers} customers")

            return result

        except Exception as e:
            logger.error(f"Error generating cohort analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate cohort analysis: {str(e)}",
                "period": period,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }

    def get_cohort_details(self, cohort_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific cohort.

        Args:
            cohort_id: Cohort identifier

        Returns:
            Dict containing cohort details
        """
        try:
            logger.info(f"Getting details for cohort: {cohort_id}")

            cohort = self._ltv_repository.get_cohort(cohort_id)

            if not cohort:
                return {
                    "status": "not_found",
                    "message": f"Cohort {cohort_id} not found",
                    "cohort_id": cohort_id
                }

            # Get customers in this cohort
            customers = self._ltv_repository.get_customers_by_cohort(cohort_id)

            customer_data = []
            for customer in customers[:50]:  # Limit to first 50 for performance
                customer_data.append({
                    "customer_id": customer.customer_id,
                    "total_revenue": float(customer.total_revenue.amount),
                    "total_purchases": customer.total_purchases,
                    "predicted_clv": float(customer.predicted_clv.amount),
                    "actual_clv": float(customer.actual_clv.amount),
                    "segment": customer.segment,
                    "first_purchase_date": customer.first_purchase_date.isoformat(),
                    "last_purchase_date": customer.last_purchase_date.isoformat()
                })

            result = {
                "status": "success",
                "cohort_id": cohort.id,
                "cohort_name": cohort.name,
                "acquisition_date": cohort.acquisition_date.isoformat(),
                "customer_count": cohort.customer_count,
                "total_revenue": float(cohort.total_revenue.amount),
                "average_ltv": float(cohort.average_ltv.amount),
                "retention_rates": cohort.retention_rates,
                "currency": cohort.total_revenue.currency,
                "customers_sample": customer_data,
                "customers_shown": len(customer_data),
                "total_customers_in_cohort": len(customers)
            }

            return result

        except Exception as e:
            logger.error(f"Error getting cohort details for {cohort_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get cohort details: {str(e)}",
                "cohort_id": cohort_id
            }

    def get_retention_heatmap(self, period: str = "monthly",
                              max_cohorts: int = 12) -> Dict[str, Any]:
        """
        Get retention heatmap data for visualization.

        Args:
            period: Analysis period ("monthly" or "quarterly")
            max_cohorts: Maximum number of cohorts to include

        Returns:
            Dict containing retention heatmap data
        """
        try:
            logger.info(f"Generating retention heatmap for period: {period}")

            # Get recent cohorts
            cohorts = self._ltv_repository.get_all_cohorts(limit=max_cohorts)

            if not cohorts:
                return {
                    "status": "no_data",
                    "message": "No cohort data available for heatmap",
                    "period": period
                }

            # Build heatmap data
            heatmap_data = []
            cohort_labels = []

            for cohort in cohorts:
                cohort_labels.append(cohort.name)
                cohort_row = {
                    "cohort": cohort.name,
                    "size": cohort.customer_count,
                    "retention": []
                }

                # Get retention rates for different periods
                periods = [1, 3, 6, 9, 12]  # months
                for months in periods:
                    period_key = f"{months}m"
                    rate = cohort.retention_rates.get(period_key, 0.0)
                    cohort_row["retention"].append({
                        "period": period_key,
                        "rate": rate,
                        "retained_customers": int(rate * cohort.customer_count)
                    })

                heatmap_data.append(cohort_row)

            result = {
                "status": "success",
                "period": period,
                "cohorts": cohort_labels,
                "heatmap_data": heatmap_data,
                "periods": [f"{m}m" for m in [1, 3, 6, 9, 12]]
            }

            return result

        except Exception as e:
            logger.error(f"Error generating retention heatmap: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate retention heatmap: {str(e)}",
                "period": period
            }
