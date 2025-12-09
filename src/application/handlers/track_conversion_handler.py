"""Track conversion handler."""

import json
from typing import Dict, Any
from loguru import logger
from ...domain.repositories.conversion_repository import ConversionRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.services.conversion.conversion_service import ConversionService
from ...domain.entities.conversion import Conversion


class TrackConversionHandler:
    """Handler for tracking conversions."""

    def __init__(
        self,
        conversion_repository: ConversionRepository,
        click_repository: ClickRepository,
        conversion_service: ConversionService
    ):
        self.conversion_repository = conversion_repository
        self.click_repository = click_repository
        self.conversion_service = conversion_service

    def handle(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track a conversion."""
        try:
            logger.info(f"Tracking conversion: {conversion_data.get('conversion_type')} for click {conversion_data.get('click_id')}")

            # Validate conversion data
            is_valid, error_message = self.conversion_service.validate_conversion_data(conversion_data)
            if not is_valid:
                logger.warning(f"Invalid conversion data: {error_message}")
                return {
                    "status": "error",
                    "message": error_message,
                    "conversion_id": None
                }

            # Get the original click
            click = self.click_repository.get_by_id(conversion_data['click_id'])
            if not click:
                return {
                    "status": "error",
                    "message": "Click not found",
                    "conversion_id": None
                }

            # Enrich conversion data with click information
            enriched_data = self.conversion_service.enrich_conversion_data(conversion_data, click)

            # Create conversion entity
            conversion = Conversion.create_from_request(enriched_data)

            # Check for duplicates
            if self.conversion_service.detect_duplicate_conversion(conversion):
                logger.warning(f"Duplicate conversion detected for click {conversion.click_id}")
                return {
                    "status": "duplicate",
                    "message": "Conversion already tracked",
                    "conversion_id": None
                }

            # Calculate attribution
            attribution = self.conversion_service.calculate_attribution(conversion, click)
            conversion.metadata['attribution'] = attribution

            # Check for fraud
            fraud_reason = self.conversion_service.validate_fraud_risk(conversion, click)
            if fraud_reason:
                logger.warning(f"Fraud detected in conversion: {fraud_reason}")
                conversion.metadata['fraud_reason'] = fraud_reason
                conversion.metadata['is_fraudulent'] = True

            # Save conversion
            self.conversion_repository.save(conversion)
            logger.info(f"Conversion tracked successfully: {conversion.id}")

            # Check if postback should be triggered
            should_postback = self.conversion_service.should_trigger_postback(conversion)

            return {
                "status": "success",
                "conversion_id": conversion.id,
                "attribution": attribution,
                "fraud_detected": fraud_reason is not None,
                "postback_triggered": should_postback
            }

        except Exception as e:
            logger.error(f"Error tracking conversion: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "conversion_id": None
            }
