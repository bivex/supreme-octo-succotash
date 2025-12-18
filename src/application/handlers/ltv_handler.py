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

"""LTV analysis handler."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from ...domain.repositories.ltv_repository import LTVRepository
from ...domain.services.ltv.ltv_service import LTVService


class LTVHandler:
    """Handler for LTV analysis operations."""

    def __init__(self, ltv_repository: LTVRepository):
        self._ltv_repository = ltv_repository
        self._ltv_service = LTVService()

    def get_ltv_analysis(self, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get LTV analysis data.

        Args:
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)

        Returns:
            Dict containing LTV analysis data
        """
        try:
            logger.info("Generating LTV analysis data")

            # Use provided dates or default to last 12 months
            if not start_date:
                start_date = datetime.now().replace(day=1, month=datetime.now().month - 11)
            if not end_date:
                end_date = datetime.now()

            # Get LTV analytics from repository
            analytics = self._ltv_repository.get_ltv_analytics(start_date, end_date)

            # Get all cohorts for cohort analysis
            cohorts = self._ltv_repository.get_all_cohorts(limit=12)

            # Format cohort analysis data
            cohort_analysis = {}
            for cohort in cohorts:
                month_key = f"month_{(cohort.acquisition_date - start_date).days // 30 + 1}"
                if month_key not in cohort_analysis:
                    cohort_analysis[month_key] = {
                        "customers": 0,
                        "revenue": 0.0
                    }
                cohort_analysis[month_key]["customers"] += cohort.customer_count
                cohort_analysis[month_key]["revenue"] += float(cohort.total_revenue.amount)

            result = {
                "status": "success",
                "average_ltv": analytics.get('avg_predicted_clv', 0.0),
                "total_customers": analytics.get('total_customers', 0),
                "total_revenue": analytics.get('total_predicted_clv', 0.0),
                "cohort_analysis": cohort_analysis,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "segment_distribution": analytics.get('segment_distribution', {})
            }

            logger.info(f"LTV analysis generated: {result['total_customers']} customers, ${result['total_revenue']} revenue")

            return result

        except Exception as e:
            logger.error(f"Error generating LTV analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate LTV analysis: {str(e)}",
                "average_ltv": 0.0,
                "total_customers": 0,
                "total_revenue": 0.0,
                "cohort_analysis": {},
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }

    def get_customer_ltv_details(self, customer_id: str) -> Dict[str, Any]:
        """
        Get detailed LTV information for a specific customer.

        Args:
            customer_id: Customer identifier

        Returns:
            Dict containing customer LTV details
        """
        try:
            logger.info(f"Getting LTV details for customer: {customer_id}")

            customer_ltv = self._ltv_repository.get_customer_ltv(customer_id)

            if not customer_ltv:
                return {
                    "status": "not_found",
                    "message": f"Customer {customer_id} not found",
                    "customer_id": customer_id
                }

            # Get customer's cohort if available
            cohort_info = None
            if customer_ltv.cohort_id:
                cohort = self._ltv_repository.get_cohort(customer_ltv.cohort_id)
                if cohort:
                    cohort_info = {
                        "cohort_id": cohort.id,
                        "cohort_name": cohort.name,
                        "acquisition_date": cohort.acquisition_date.isoformat(),
                        "cohort_size": cohort.customer_count,
                        "cohort_avg_ltv": float(cohort.average_ltv.amount)
                    }

            result = {
                "status": "success",
                "customer_id": customer_ltv.customer_id,
                "ltv_metrics": {
                    "predicted_clv": float(customer_ltv.predicted_clv.amount),
                    "actual_clv": float(customer_ltv.actual_clv.amount),
                    "total_revenue": float(customer_ltv.total_revenue.amount),
                    "total_purchases": customer_ltv.total_purchases,
                    "average_order_value": float(customer_ltv.average_order_value.amount),
                    "purchase_frequency": customer_ltv.purchase_frequency,
                    "customer_lifetime_months": customer_ltv.customer_lifetime_months
                },
                "segment": customer_ltv.segment,
                "cohort_info": cohort_info,
                "dates": {
                    "first_purchase": customer_ltv.first_purchase_date.isoformat(),
                    "last_purchase": customer_ltv.last_purchase_date.isoformat(),
                    "created_at": customer_ltv.created_at.isoformat(),
                    "updated_at": customer_ltv.updated_at.isoformat()
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error getting LTV details for customer {customer_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get LTV details: {str(e)}",
                "customer_id": customer_id
            }

    def get_ltv_segments_overview(self) -> Dict[str, Any]:
        """
        Get overview of all LTV segments.

        Returns:
            Dict containing LTV segments overview
        """
        try:
            logger.info("Getting LTV segments overview")

            segments = self._ltv_repository.get_all_ltv_segments()

            segment_data = []
            for segment in segments:
                segment_data.append({
                    "segment_id": segment.id,
                    "segment_name": segment.name,
                    "customer_count": segment.customer_count,
                    "total_value": float(segment.total_value.amount),
                    "average_ltv": float(segment.average_ltv.amount),
                    "retention_rate": segment.retention_rate,
                    "ltv_range": {
                        "min": float(segment.min_ltv.amount) if segment.min_ltv else None,
                        "max": float(segment.max_ltv.amount) if segment.max_ltv else None
                    },
                    "description": segment.description
                })

            result = {
                "status": "success",
                "total_segments": len(segments),
                "segments": segment_data
            }

            return result

        except Exception as e:
            logger.error(f"Error getting LTV segments overview: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get LTV segments overview: {str(e)}",
                "total_segments": 0,
                "segments": []
            }
