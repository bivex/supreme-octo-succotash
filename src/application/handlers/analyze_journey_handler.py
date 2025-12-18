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

"""Customer journey analysis handler."""

from typing import Dict, Any, Optional, List

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
                "period_days": days,
                "analysis_type": "funnel_drop_off",
                "total_drop_off_points": len(drop_offs)
            }
        except Exception as e:
            logger.error(f"Error getting drop-off analysis: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def populate_journeys_from_data(self, click_data: List[Dict[str, Any]] = None,
                                    impression_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Populate journey data from clicks and impressions for analysis."""
        try:
            journeys_created = 0

            if click_data:
                for click in click_data:
                    try:
                        journey = self.journey_service.create_journey_from_click(click)
                        journeys_created += 1
                    except Exception as e:
                        logger.warning(f"Failed to create journey from click {click.get('id')}: {e}")

            if impression_data:
                for impression in impression_data:
                    try:
                        journey = self.journey_service.create_journey_from_impression(impression)
                        journeys_created += 1
                    except Exception as e:
                        logger.warning(f"Failed to create journey from impression {impression.get('id')}: {e}")

            return {
                "status": "success",
                "journeys_created": journeys_created,
                "total_journeys": len(self.journey_service._journeys)
            }
        except Exception as e:
            logger.error(f"Error populating journeys: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
