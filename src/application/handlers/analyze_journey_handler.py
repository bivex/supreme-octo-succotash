"""Customer journey analysis handler."""

import json
from typing import Dict, Any, Optional
from loguru import logger
from ...domain.services.journey.journey_service import JourneyService


class AnalyzeJourneyHandler:
    """Handler for customer journey analysis."""

    def __init__(self, journey_service: JourneyService):
        self.journey_service = journey_service

    def get_journey_funnel(self, campaign_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get funnel analysis."""
        try:
            funnel_data = self.journey_service.get_journey_funnel(campaign_id, days)
            return {
                "status": "success",
                **funnel_data
            }
        except Exception as e:
            logger.error(f"Error getting journey funnel: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_drop_off_analysis(self, campaign_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get drop-off analysis."""
        try:
            drop_offs = self.journey_service.get_drop_off_points(campaign_id, days)
            return {
                "status": "success",
                "drop_off_points": drop_offs,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error getting drop-off analysis: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
