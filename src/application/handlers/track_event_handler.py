"""Track event handler."""

import json
from typing import Dict, Any
from loguru import logger
from ...domain.repositories.event_repository import EventRepository
from ...domain.services.event.event_service import EventService
from ...domain.entities.event import Event


class TrackEventHandler:
    """Handler for tracking user events."""

    def __init__(
        self,
        event_repository: EventRepository,
        event_service: EventService
    ):
        self.event_repository = event_repository
        self.event_service = event_service

    def handle(self, event_data: Dict[str, Any], request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track a user event."""
        try:
            logger.debug(f"Tracking event: {event_data.get('event_type')} - {event_data.get('event_name')}")

            # Enrich event data with request context
            enriched_data = self.event_service.enrich_event_data(event_data, request_context)

            # Validate event data
            if not self.event_service.validate_event_data(enriched_data):
                logger.warning("Invalid event data received")
                return {
                    "status": "error",
                    "message": "Invalid event data",
                    "event_id": None
                }

            # Create event entity
            event = Event.create_from_request(enriched_data)

            # Check for fraud
            fraud_reason = self.event_service.detect_fraudulent_event(event)
            if fraud_reason:
                logger.warning(f"Fraudulent event detected: {fraud_reason}")
                # Still save the event but mark it as fraudulent
                event.properties['fraud_reason'] = fraud_reason
                event.properties['is_fraudulent'] = True

            # Categorize event
            categories = self.event_service.categorize_event(event)
            event.properties['categories'] = categories

            # Save event
            self.event_repository.save(event)
            logger.info(f"Event tracked successfully: {event.id}")

            return {
                "status": "success",
                "event_id": event.id,
                "categories": categories,
                "fraud_detected": fraud_reason is not None
            }

        except Exception as e:
            logger.error(f"Error tracking event: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "event_id": None
            }
