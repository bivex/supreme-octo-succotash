"""Conversion tracking service."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from ...entities.conversion import Conversion
from ...entities.click import Click
from ...repositories.click_repository import ClickRepository
from ...value_objects.identifiers.click_id import ClickId


class ConversionService:
    """Service for processing and validating conversions."""

    def __init__(self, click_repository: ClickRepository):
        self.click_repository = click_repository
        self._valid_conversion_types = {
            'lead', 'sale', 'install', 'registration', 'signup'
        }

    def validate_conversion_data(self, conversion_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate conversion tracking data."""
        try:
            required_fields = ['click_id', 'conversion_type']

            for field in required_fields:
                if field not in conversion_data:
                    return False, f"Missing required field: {field}"

            # Validate conversion type
            if conversion_data['conversion_type'] not in self._valid_conversion_types:
                return False, f"Invalid conversion_type: {conversion_data['conversion_type']}"

            # Validate click_id exists
            click_id = ClickId.from_string(conversion_data['click_id'])
            click = self.click_repository.find_by_id(click_id)
            if not click:
                return False, f"Click ID not found: {conversion_data['click_id']}"

            # Validate monetary value if provided
            if 'conversion_value' in conversion_data and conversion_data['conversion_value']:
                value_data = conversion_data['conversion_value']
                if not isinstance(value_data, dict) or 'amount' not in value_data:
                    return False, "Invalid conversion_value format"

                if not isinstance(value_data['amount'], (int, float)) or value_data['amount'] < 0:
                    return False, "Invalid conversion_value amount"

            # Validate order_id uniqueness if provided
            if 'order_id' in conversion_data and conversion_data['order_id']:
                # This would need to be checked against existing conversions
                # For now, we'll assume it's unique
                pass

            return True, None

        except Exception as e:
            logger.error(f"Error validating conversion data: {e}")
            return False, str(e)

    def enrich_conversion_data(self, conversion_data: Dict[str, Any], click: Click) -> Dict[str, Any]:
        """Enrich conversion data with information from the original click."""
        enriched = conversion_data.copy()

        # Add click-derived information
        if 'campaign_id' not in enriched:
            enriched['campaign_id'] = click.campaign_id

        if 'landing_page_id' not in enriched:
            enriched['landing_page_id'] = click.landing_page_id

        if 'offer_id' not in enriched:
            enriched['offer_id'] = click.campaign_offer_id

        # Add user tracking info
        enriched['ip_address'] = click.ip_address
        enriched['user_agent'] = click.user_agent
        enriched['referrer'] = click.referrer

        # Add sub-tracking parameters
        enriched.setdefault('metadata', {}).update({
            'sub1': click.sub1,
            'sub2': click.sub2,
            'sub3': click.sub3,
            'sub4': click.sub4,
            'sub5': click.sub5,
            'click_timestamp': click.ts,
            'fraud_score': click.fraudScore
        })

        return enriched

    def detect_duplicate_conversion(self, conversion: Conversion) -> bool:
        """Check if this conversion might be a duplicate."""
        # Simple duplicate detection based on order_id
        if conversion.order_id:
            # In a real implementation, you'd check against existing conversions
            # For now, we'll assume no duplicates
            return False

        # Check for conversions from same click_id with same type in short time window
        # This would require access to existing conversions
        return False

    def calculate_attribution(self, conversion: Conversion, click: Click) -> Dict[str, Any]:
        """Calculate attribution data for the conversion."""
        attribution = {
            'attribution_model': 'last_click',  # Simple last-click attribution
            'attribution_confidence': 1.0,
            'time_to_conversion': None,
            'touchpoints': 1
        }

        # Calculate time to conversion
        if click.ts:
            time_to_conversion = conversion.timestamp.timestamp() - click.ts
            attribution['time_to_conversion'] = time_to_conversion

            # Attribution confidence decreases with time
            if time_to_conversion > 30 * 24 * 60 * 60:  # 30 days
                attribution['attribution_confidence'] = 0.5
            elif time_to_conversion > 7 * 24 * 60 * 60:  # 7 days
                attribution['attribution_confidence'] = 0.8
            else:
                attribution['attribution_confidence'] = 1.0

        return attribution

    def validate_fraud_risk(self, conversion: Conversion, click: Click) -> Optional[str]:
        """Validate conversion for potential fraud."""
        # Check if click was marked as fraudulent
        if click.isValid == 0:
            return "conversion_from_invalid_click"

        if click.fraudScore and click.fraudScore > 0.7:
            return "high_fraud_score_click"

        # Check for suspicious conversion patterns
        if conversion.conversion_value and conversion.conversion_value.amount > 10000:
            return "unusually_high_value"

        # Check time to conversion (too fast might be suspicious)
        if hasattr(conversion, 'metadata') and 'time_to_conversion' in conversion.metadata:
            time_to_conversion = conversion.metadata['time_to_conversion']
            if time_to_conversion < 10:  # Less than 10 seconds
                return "suspiciously_fast_conversion"

        return None  # No fraud detected

    def should_trigger_postback(self, conversion: Conversion) -> bool:
        """Determine if this conversion should trigger postback notifications."""
        # Don't send postbacks for test conversions
        if conversion.metadata.get('is_test', False):
            return False

        # Send postbacks for all valid conversions
        return True
