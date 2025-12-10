"""Retention campaign handler."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from ...domain.repositories.retention_repository import RetentionRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.conversion_repository import ConversionRepository
from ...domain.services.retention.retention_service import RetentionService


class RetentionHandler:
    """Handler for retention campaign operations."""

    def __init__(self, retention_repository: RetentionRepository,
                 click_repository: ClickRepository,
                 conversion_repository: ConversionRepository):
        self._retention_repository = retention_repository
        self._click_repository = click_repository
        self._conversion_repository = conversion_repository
        self._retention_service = RetentionService()

    def get_retention_campaigns(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Get retention campaigns.

        Args:
            status_filter: Optional status filter

        Returns:
            Dict containing retention campaigns data
        """
        try:
            logger.info("Getting retention campaigns")

            campaigns = self._retention_repository.get_all_retention_campaigns(status_filter)

            campaign_data = []
            for campaign in campaigns:
                campaign_data.append({
                    "id": campaign.id,
                    "name": campaign.name,
                    "description": campaign.description,
                    "target_segment": campaign.target_segment.value,
                    "status": campaign.status.value,
                    "target_user_count": campaign.target_user_count,
                    "sent_count": campaign.sent_count,
                    "opened_count": campaign.opened_count,
                    "clicked_count": campaign.clicked_count,
                    "converted_count": campaign.converted_count,
                    "budget": campaign.budget,
                    "open_rate": campaign.open_rate,
                    "click_rate": campaign.click_rate,
                    "conversion_rate": campaign.conversion_rate,
                    "is_active": campaign.is_active,
                    "days_remaining": campaign.days_remaining,
                    "dates": {
                        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
                        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
                        "created_at": campaign.created_at.isoformat(),
                        "updated_at": campaign.updated_at.isoformat()
                    }
                })

            result = {
                "status": "success",
                "campaigns": campaign_data,
                "total_campaigns": len(campaign_data)
            }

            logger.info(f"Retrieved {len(campaign_data)} retention campaigns")

            return result

        except Exception as e:
            logger.error(f"Error getting retention campaigns: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get retention campaigns: {str(e)}",
                "campaigns": [],
                "total_campaigns": 0
            }

    def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get detailed performance data for a specific campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Dict containing campaign performance data
        """
        try:
            logger.info(f"Getting performance data for campaign: {campaign_id}")

            performance_data = self._retention_repository.get_campaign_performance_summary(campaign_id)

            if not performance_data:
                return {
                    "status": "not_found",
                    "message": f"Campaign {campaign_id} not found",
                    "campaign_id": campaign_id
                }

            return {
                "status": "success",
                "campaign_id": campaign_id,
                **performance_data
            }

        except Exception as e:
            logger.error(f"Error getting campaign performance for {campaign_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get campaign performance: {str(e)}",
                "campaign_id": campaign_id
            }

    def analyze_user_retention(self, customer_id: str) -> Dict[str, Any]:
        """
        Analyze retention profile for a specific user.

        Args:
            customer_id: Customer identifier

        Returns:
            Dict containing user retention analysis
        """
        try:
            logger.info(f"Analyzing retention for customer: {customer_id}")

            # Get user engagement profile
            profile = self._retention_repository.get_user_engagement_profile(customer_id)

            if not profile:
                return {
                    "status": "not_found",
                    "message": f"User profile for {customer_id} not found",
                    "customer_id": customer_id
                }

            # Get churn prediction
            prediction = self._retention_repository.get_churn_prediction(customer_id)

            # Get user's clicks and conversions for detailed analysis
            clicks = self._click_repository.find_by_customer_id(customer_id, limit=100)
            conversions = self._conversion_repository.find_by_customer_id(customer_id, limit=50)

            # Analyze engagement using the service
            detailed_profile = self._retention_service.analyze_user_engagement(clicks, conversions, customer_id)

            # Predict churn risk
            churn_prediction = self._retention_service.predict_churn_risk(detailed_profile, [detailed_profile])

            result = {
                "status": "success",
                "customer_id": customer_id,
                "engagement_profile": {
                    "total_sessions": detailed_profile.total_sessions,
                    "total_clicks": detailed_profile.total_clicks,
                    "total_conversions": detailed_profile.total_conversions,
                    "avg_session_duration": detailed_profile.avg_session_duration,
                    "engagement_score": detailed_profile.engagement_score,
                    "segment": detailed_profile.segment.value,
                    "interests": detailed_profile.interests,
                    "is_engaged": detailed_profile.is_engaged,
                    "conversion_rate": detailed_profile.conversion_rate,
                    "days_since_last_activity": detailed_profile.days_since_last_activity
                },
                "churn_risk": {
                    "churn_probability": churn_prediction.churn_probability,
                    "risk_level": churn_prediction.risk_level,
                    "risk_score": churn_prediction.risk_score,
                    "is_high_risk": churn_prediction.is_high_risk,
                    "predicted_churn_date": churn_prediction.predicted_churn_date.isoformat() if churn_prediction.predicted_churn_date else None,
                    "reasons": churn_prediction.reasons
                },
                "activity_summary": {
                    "last_session_date": detailed_profile.last_session_date.isoformat(),
                    "total_clicks": len(clicks),
                    "total_conversions": len(conversions)
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error analyzing retention for customer {customer_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to analyze user retention: {str(e)}",
                "customer_id": customer_id
            }

    def get_retention_analytics(self, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get retention analytics data.

        Args:
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)

        Returns:
            Dict containing retention analytics data
        """
        try:
            logger.info("Generating retention analytics data")

            # Use provided dates or default to last 30 days
            if not start_date:
                start_date = datetime.now().replace(day=datetime.now().day - 30)
            if not end_date:
                end_date = datetime.now()

            # Get analytics from repository
            analytics = self._retention_repository.get_retention_analytics(start_date, end_date)

            result = {
                "status": "success",
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "campaign_metrics": analytics.get('campaign_metrics', {}),
                "churn_risk_distribution": analytics.get('churn_risk_distribution', {}),
                "segment_distribution": analytics.get('segment_distribution', {}),
                "high_risk_customers_count": len(self._retention_repository.get_high_risk_customers(limit=1000))
            }

            logger.info(f"Retention analytics generated for {result['date_range']['start']} to {result['date_range']['end']}")

            return result

        except Exception as e:
            logger.error(f"Error generating retention analytics: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate retention analytics: {str(e)}",
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
