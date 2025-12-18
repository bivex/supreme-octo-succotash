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

"""Analytics handler."""

from datetime import datetime, timedelta
from typing import Dict, Any

from loguru import logger


class AnalyticsHandler:
    """Handler for analytics operations."""

    def __init__(self, click_repository=None, campaign_repository=None, analytics_repository=None):
        """Initialize analytics handler."""
        self._click_repository = click_repository
        self._campaign_repository = campaign_repository
        self._analytics_repository = analytics_repository

    def get_real_time_analytics(self) -> Dict[str, Any]:
        """Get real-time analytics data for the last 5 minutes.

        Returns:
            Dict containing real-time analytics data
        """
        try:
            logger.info("Generating real-time analytics data")

            current_time = datetime.now()
            five_minutes_ago = current_time - timedelta(minutes=5)

            # Get real-time metrics from repositories
            total_clicks = 0
            total_conversions = 0
            total_revenue = 0.0
            active_users = 0
            fraud_events = 0
            blocked_clicks = 0

            top_campaigns = []
            top_landing_pages = []

            # Get active campaigns for real-time analysis
            if self._campaign_repository:
                try:
                    campaigns = self._campaign_repository.find_all(limit=10)
                    for campaign in campaigns[:3]:  # Top 3 campaigns
                        # In real implementation, would get real-time metrics for each campaign
                        campaign_clicks = campaign.clicks_count if hasattr(campaign, 'clicks_count') else 0
                        campaign_conversions = campaign.conversions_count if hasattr(campaign,
                                                                                     'conversions_count') else 0

                        top_campaigns.append({
                            "campaignId": str(campaign.id),
                            "campaignName": campaign.name,
                            "clicks": campaign_clicks,
                            "conversions": campaign_conversions
                        })

                        total_clicks += campaign_clicks
                        total_conversions += campaign_conversions

                        # Calculate revenue from campaign data
                        if hasattr(campaign, 'payout') and campaign.payout and campaign_conversions > 0:
                            total_revenue += float(campaign.payout.amount) * campaign_conversions

                except Exception as e:
                    logger.warning(f"Could not load campaign data for real-time analytics: {e}")

            # Estimate active users (simplified - would need real session tracking)
            active_users = max(1, total_clicks // 3)  # Rough estimate: 1 active user per 3 clicks

            result = {
                "timeRange": {
                    "startTime": five_minutes_ago.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "endTime": current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                "activeUsers": active_users,
                "clicks": total_clicks,
                "conversions": total_conversions,
                "revenue": {
                    "amount": round(total_revenue, 2),
                    "currency": "USD"
                },
                "topCampaigns": top_campaigns,
                "topLandingPages": top_landing_pages,  # Would need landing page repository
                "fraudEvents": fraud_events,  # Would need fraud monitoring
                "blockedClicks": blocked_clicks  # Would need fraud monitoring
            }

            logger.info(
                f"Real-time analytics generated: {total_clicks} clicks, {total_conversions} conversions, ${total_revenue} revenue")

            return result

        except Exception as e:
            logger.error(f"Error generating real-time analytics: {e}", exc_info=True)
            # Return fallback data
            return {
                "timeRange": {
                    "startTime": (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "endTime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                "activeUsers": 0,
                "clicks": 0,
                "conversions": 0,
                "revenue": {"amount": 0.00, "currency": "USD"},
                "topCampaigns": [],
                "topLandingPages": [],
                "fraudEvents": 0,
                "blockedClicks": 0,
                "error": "Failed to generate real-time analytics"
            }
