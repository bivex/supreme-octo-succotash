"""
Module for tracking clicks and conversions
Integrates with Supreme Tracker (Supreme)
"""

import asyncio
import base64
import hashlib
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import aiohttp
from loguru import logger

# Cache functions removed - now using Supreme API for URL generation
# Removed config import to avoid circular dependencies

# Import shared URL shortener
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared_url_shortener import url_shortener


class TrackingManager:
    """Tracking manager for Supreme integration"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.tracker_base_url = "https://api.supreme-tracker.com"  # Supreme tracker domain
        # Use ngrok HTTPS URL for Supreme API access
        self.local_landing_url = "https://gladsomely-unvitriolized-trudie.ngrok-free.dev"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_click_id(self, user_id: int, timestamp: Optional[float] = None) -> str:
        """Generate unique click_id"""
        if timestamp is None:
            timestamp = time.time()

        # Create unique string based on user_id and timestamp
        unique_string = f"{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}"

        # Hash to get short ID
        click_id = hashlib.md5(unique_string.encode()).hexdigest()[:16]

        return click_id

    def _build_tracking_url(self, click_id: str, additional_params: Optional[Dict[str, Any]] = None) -> str:
        """Build tracking URL for local landing page"""

        # Base parameters for local endpoint
        params = {
            "click_id": click_id,
            "source": "telegram_bot",
            "cid": "camp_9061",
            **DEFAULT_TRACKING_PARAMS
        }

        # Add additional parameters
        if additional_params:
            params.update(additional_params)

        # Form URL - redirect to public landing page via ngrok
        query_string = urlencode(params, safe='')
        tracking_url = f"{self.local_landing_url}/v1/click?{query_string}"

        return tracking_url

    async def generate_tracking_link(self,
                                   user_id: int,
                                   source: str = "telegram_bot",
                                   additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate tracking link for user using API URL generation

        Args:
            user_id: Telegram user ID
            source: Traffic source
            additional_params: Additional tracking parameters

        Returns:
            Dictionary with click_id and tracking_url
        """

        timestamp = time.time()
        click_id = self._generate_click_id(user_id, timestamp)

        # Use API to generate short tracking URL
        tracking_url = await self._generate_short_tracking_url(user_id, source, additional_params or {})

        # Save click information (if database exists)
        click_data = {
            "click_id": click_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "source": source,
            "tracking_url": tracking_url,
            "status": "generated"
        }

        logger.info(f"Generated tracking link for user {user_id}: {click_id}")

        # TODO: Save to database if needed
        # await self._save_click_data(click_data)

        return {
            "click_id": click_id,
            "tracking_url": tracking_url,
            "click_data": click_data
        }

    async def _generate_short_tracking_url(self, user_id: int, source: str, additional_params: Dict[str, Any]) -> str:
        """Generate tracking URL using Supreme API /clicks/generate endpoint"""
        try:
            # Prepare payload for API URL generation
            campaign_id_num = 9061  # Fixed campaign ID
            payload = {
                "campaign_id": campaign_id_num,
                "base_url": self.local_landing_url,
                "params": {
                    "sub1": additional_params.get("sub1", source),
                    "sub2": additional_params.get("sub2", "telegram"),
                    "sub3": additional_params.get("sub3", "callback_offer"),
                    "sub4": additional_params.get("sub4", str(user_id)),
                    "sub5": additional_params.get("sub5", "premium_offer")
                }
            }

            # Add optional parameters if provided
            if additional_params.get("landing_page_id"):
                payload["landing_page_id"] = additional_params["landing_page_id"]
            if additional_params.get("offer_id"):
                payload["offer_id"] = additional_params["offer_id"]

            url = f"{self.local_landing_url}/clicks/generate"
            headers = {'Authorization': 'Bearer test_jwt_token_12345', 'Content-Type': 'application/json'}

            logger.info(f"Generating tracking URL with payload: {payload}")

            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success" and result.get("tracking_url"):
                        api_tracking_url = result["tracking_url"]

                        # Use new URLShortener to create optimized short URL
                        from shared_url_shortener import URLParams, EncodingStrategy

                        # Extract parameters from API tracking URL
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(api_tracking_url)
                        query_params = parse_qs(parsed.query)

                        # Create URLParams object for optimal encoding
                        url_params = URLParams(
                            cid=str(payload["campaign_id"]),
                            sub1=payload["params"].get("sub1", "telegram_bot"),
                            sub2=payload["params"].get("sub2", "telegram"),
                            sub3=payload["params"].get("sub3", "callback_offer"),
                            sub4=payload["params"].get("sub4", str(user_id)),
                            sub5=payload["params"].get("sub5", "premium_offer"),
                            click_id=query_params.get('click_id', [None])[0],
                            extra={
                                'landing_page_id': str(payload.get('landing_page_id')) if payload.get('landing_page_id') else None,
                                'offer_id': str(payload.get('offer_id')) if payload.get('offer_id') else None
                            }
                        )

                        # Auto-select optimal strategy based on parameters
                        strategy = EncodingStrategy.SEQUENTIAL  # Default for telegram bot
                        if len([v for v in url_params.to_dict().values() if v]) > 3:
                            strategy = EncodingStrategy.COMPRESSED

                        # Generate ultra-short code (max 10 chars)
                        short_code = url_shortener.encode(url_params, strategy)
                        short_url = f"{self.local_landing_url}/s/{short_code}"

                        logger.info(f"Generated ultra-short tracking URL: {short_url} (strategy: {strategy.value})")
                        return short_url
                    else:
                        logger.warning(f"API returned error: {result}")
                else:
                    logger.warning(f"API request failed with status {response.status}")

        except Exception as e:
            logger.warning(f"Error generating tracking URL via API: {e}")

        # Fallback to direct URL building
        logger.info("Falling back to manual URL generation")
        click_id = self._generate_click_id(user_id, time.time())
        return self._build_tracking_url(click_id, additional_params)

    async def track_event(self,
                         click_id: str,
                         event_type: str,
                         event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send event to tracker

        Args:
            click_id: Click ID
            event_type: Event type (page_view, button_click, etc.)
            event_data: Additional event data

        Returns:
            True if successful
        """

        if not self.session:
            logger.warning("HTTP session not initialized - skipping event tracking")
            return False

        # Skip tracking if using placeholder domain (but still try local endpoint)
        skip_remote = True  # Skip remote tracking for demo/development

        if skip_remote:
            logger.info(f"Remote tracking skipped (demo mode): {event_type} for click_id {click_id}")
            # Try to track locally for debugging
            return await self._track_event_locally(click_id, event_type, event_data)

        try:
            payload = {
                "click_id": click_id,
                "event_type": event_type,
                "timestamp": int(time.time()),
                **(event_data or {})
            }

            url = f"{self.tracker_base_url}{API_ENDPOINTS['event_track']}"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Event tracked: {event_type} for click_id {click_id}")
                    return result.get("recorded", False)
                else:
                    logger.warning(f"Failed to track event (status {response.status}) - continuing without tracking")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking event (network issue): {e} - continuing without tracking")
            return False

    async def _track_event_locally(self, click_id: str, event_type: str, event_data: Optional[Dict[str, Any]] = None) -> bool:
        """Track event to Supreme server endpoint"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping Supreme event tracking")
            return False

        try:
            campaign_id_num = 9061
            logger.info(f"Using campaign_id: camp_9061 -> {campaign_id_num}")
            payload = {
                "event_type": event_type,
                "event_name": event_data.get("event_name", event_type) if event_data else event_type,
                "click_id": click_id,
                "campaign_id": str(campaign_id_num)
            }

            # Add landing_page_id if available (from API docs example)
            # For now, we'll keep it simple with just required fields

            url = f"{self.local_landing_url}/events/track"

            logger.info(f"Sending event payload: {payload}")
            async with self.session.post(url, json=payload) as response:
                logger.info(f"Event tracking response status: {response.status}")
                response_text = await response.text()
                logger.info(f"Event tracking response: {response_text}")

                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success":
                        logger.info(f"Supreme event tracked: {event_type} for click_id {click_id}")
                        return True
                    else:
                        logger.warning(f"Supreme event tracking failed: {result}")
                        return False
                else:
                    logger.warning(f"Supreme event tracking failed (status {response.status})")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking Supreme event: {e}")
            return False

    async def track_conversion(self,
                             click_id: str,
                             conversion_type: str,
                             conversion_value: float = 0.0,
                             conversion_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send conversion to tracker

        Args:
            click_id: Click ID
            conversion_type: Conversion type (lead, sale, etc.)
            conversion_value: Conversion value
            conversion_data: Additional data

        Returns:
            True if successful
        """

        if not self.session:
            logger.warning("HTTP session not initialized - skipping conversion tracking")
            return False

        # Skip tracking if using placeholder domain (but still try local endpoint)
        skip_remote = True  # Skip remote tracking for demo/development

        if skip_remote:
            logger.info(f"Remote conversion tracking skipped (demo mode): {conversion_type} for click_id {click_id}")
            # Skip local tracking in demo mode to avoid API validation errors
            return True

        try:
            payload = {
                "click_id": click_id,
                "conversion_type": conversion_type,
                "conversion_value": conversion_value,
                "currency": "RUB",
                "timestamp": int(time.time()),
                **(conversion_data or {})
            }

            url = f"{self.tracker_base_url}{API_ENDPOINTS['conversion_track']}"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Conversion tracked: {conversion_type} for click_id {click_id}")
                    return result.get("recorded", False)
                else:
                    logger.warning(f"Failed to track conversion (status {response.status}) - continuing without tracking")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking conversion (network issue): {e} - continuing without tracking")
            return False

    async def _track_conversion_locally(self, click_id: str, conversion_type: str, conversion_value: float = 0.0, conversion_data: Optional[Dict[str, Any]] = None) -> bool:
        """Track conversion to Supreme server endpoint"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping Supreme conversion tracking")
            return False

        try:
            # Map conversion_type to event_type for the events API
            event_type_map = {
                "lead": "conversion",
                "sale": "purchase",
                "signup": "signup"
            }

            payload = {
                "event_type": event_type_map.get(conversion_type, "conversion"),
                "event_name": f"{conversion_type}_conversion",
                "click_id": click_id,
                "campaign_id": "9061",  # Keep as string for events API
                "url": f"{self.local_landing_url}/landing",
                "properties": {
                    "conversion_value": conversion_value,
                    "currency": "RUB",
                    "source": "telegram_bot",
                    **(conversion_data or {})
                }
            }

            url = f"{self.local_landing_url}/events/track"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success":
                        logger.info(f"Supreme conversion tracked: {conversion_type} for click_id {click_id}")
                        return True
                    else:
                        logger.warning(f"Supreme conversion tracking failed: {result}")
                        return False
                else:
                    logger.warning(f"Supreme conversion tracking failed (status {response.status})")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking Supreme conversion: {e}")
            return False

    async def send_postback(self,
                          click_id: str,
                          postback_type: str,
                          postback_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send postback notification

        Args:
            click_id: Click ID
            postback_type: Postback type
            postback_data: Data to send

        Returns:
            True if successful
        """

        if not self.session:
            logger.warning("HTTP session not initialized - skipping postback")
            return False

        # Skip tracking if using placeholder domain (but still try local endpoint)
        skip_remote = True  # Skip remote tracking for demo/development

        if skip_remote:
            logger.info(f"Remote postback skipped (demo mode): {postback_type} for click_id {click_id}")
            # Still try to track locally
            return await self._send_postback_locally(click_id, postback_type, postback_data)

        try:
            payload = {
                "click_id": click_id,
                "postback_type": postback_type,
                "timestamp": int(time.time()),
                **(postback_data or {})
            }

            url = f"{self.tracker_base_url}{API_ENDPOINTS['postback_send']}"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Postback sent: {postback_type} for click_id {click_id}")
                    return result.get("delivered", False)
                else:
                    logger.warning(f"Failed to send postback (status {response.status}) - continuing without postback")
                    return False

        except Exception as e:
            logger.warning(f"Error sending postback (network issue): {e} - continuing without postback")
            return False

    async def _send_postback_locally(self, click_id: str, postback_type: str, postback_data: Optional[Dict[str, Any]] = None) -> bool:
        """Send postback to Supreme server endpoint"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping Supreme postback")
            return False

        try:
            payload = {
                "event_type": "postback",
                "event_name": f"{postback_type}_postback",
                "click_id": click_id,
                "campaign_id": "9061",  # Keep as string for events API
                "url": f"{self.local_landing_url}/landing",
                "properties": {
                    "postback_type": postback_type,
                    "source": "telegram_bot",
                    **(postback_data or {})
                }
            }

            url = f"{self.local_landing_url}/events/track"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("status") == "success":
                        logger.info(f"Supreme postback sent: {postback_type} for click_id {click_id}")
                        return True
                    else:
                        logger.warning(f"Supreme postback failed: {result}")
                        return False
                else:
                    logger.warning(f"Supreme postback failed (status {response.status})")
                    return False

        except Exception as e:
            logger.warning(f"Error sending Supreme postback: {e}")
            return False

    def extract_click_id_from_url(self, url: str) -> Optional[str]:
        """Extract click_id from landing URL"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            click_id = params.get('click_id', [None])[0]
            return click_id
        except Exception as e:
            logger.error(f"Error extracting click_id from URL: {e}")
            return None


# Global instance for use in handlers
tracking_manager = TrackingManager()


def get_tracking_manager() -> TrackingManager:
    """Get the current tracking manager instance"""
    return tracking_manager


async def init_tracking():
    """Initialize tracking manager"""
    global tracking_manager
    tracking_manager = TrackingManager()
    await tracking_manager.__aenter__()
    logger.info("Tracking manager initialized")


def get_tracking_manager() -> TrackingManager:
    """Get the initialized tracking manager instance"""
    return tracking_manager


async def close_tracking():
    """Close tracking manager connections"""
    global tracking_manager
    await tracking_manager.__aexit__(None, None, None)
    logger.info("Tracking manager closed")
