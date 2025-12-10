"""
Module for tracking clicks and conversions
Integrates with Supreme Tracker (Supreme)
"""

import asyncio
import hashlib
import time
import uuid
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import aiohttp
from loguru import logger

from config import settings, DEFAULT_TRACKING_PARAMS, API_ENDPOINTS


class TrackingManager:
    """Tracking manager for Supreme integration"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.tracker_base_url = f"https://{settings.tracker_domain}"
        # Use ngrok HTTPS URL for public access
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
            "campaign_id": settings.campaign_id,
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
        Generate tracking link for user

        Args:
            user_id: Telegram user ID
            source: Traffic source
            additional_params: Additional tracking parameters

        Returns:
            Dictionary with click_id and tracking_url
        """

        timestamp = time.time()
        click_id = self._generate_click_id(user_id, timestamp)

        # Update parameters with source
        tracking_params = {
            "sub1": source,
            "sub2": "telegram",
            "ts": int(timestamp),
            **(additional_params or {})
        }

        tracking_url = self._build_tracking_url(click_id, tracking_params)

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
        skip_remote = "yourdomain.com" in settings.tracker_domain or "example.com" in settings.tracker_domain

        if skip_remote:
            logger.info(f"Remote tracking skipped (demo mode): {event_type} for click_id {click_id}")
            # Still try to track locally
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
        """Track event to local endpoint"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping local event tracking")
            return False

        try:
            payload = {
                "click_id": click_id,
                "event_type": event_type,
                "timestamp": int(time.time()),
                "source": "telegram_bot",
                **(event_data or {})
            }

            url = f"{self.local_landing_url}/v1/event"

            async with self.session.post(url, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"Local event tracked: {event_type} for click_id {click_id}")
                    return True
                else:
                    logger.warning(f"Local event tracking failed (status {response.status})")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking local event: {e}")
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
        skip_remote = "yourdomain.com" in settings.tracker_domain or "example.com" in settings.tracker_domain

        if skip_remote:
            logger.info(f"Remote conversion tracking skipped (demo mode): {conversion_type} for click_id {click_id}")
            # Still try to track locally
            return await self._track_conversion_locally(click_id, conversion_type, conversion_value, conversion_data)

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
        """Track conversion to local endpoint"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping local conversion tracking")
            return False

        try:
            payload = {
                "click_id": click_id,
                "conversion_type": conversion_type,
                "conversion_value": conversion_value,
                "currency": "RUB",
                "timestamp": int(time.time()),
                "source": "telegram_bot",
                **(conversion_data or {})
            }

            url = f"{self.local_landing_url}/v1/conversion"

            async with self.session.post(url, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"Local conversion tracked: {conversion_type} for click_id {click_id}")
                    return True
                else:
                    logger.warning(f"Local conversion tracking failed (status {response.status})")
                    return False

        except Exception as e:
            logger.warning(f"Error tracking local conversion: {e}")
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
        skip_remote = "yourdomain.com" in settings.tracker_domain or "example.com" in settings.tracker_domain

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
        """Send postback to local endpoint"""
        if not self.session:
            logger.warning("HTTP session not initialized - skipping local postback")
            return False

        try:
            payload = {
                "click_id": click_id,
                "postback_type": postback_type,
                "timestamp": int(time.time()),
                "source": "telegram_bot",
                **(postback_data or {})
            }

            url = f"{self.local_landing_url}/v1/postback"

            async with self.session.post(url, json=payload) as response:
                if response.status in [200, 201]:
                    logger.info(f"Local postback sent: {postback_type} for click_id {click_id}")
                    return True
                else:
                    logger.warning(f"Local postback failed (status {response.status})")
                    return False

        except Exception as e:
            logger.warning(f"Error sending local postback: {e}")
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


async def close_tracking():
    """Close tracking manager connections"""
    global tracking_manager
    await tracking_manager.__aexit__(None, None, None)
    logger.info("Tracking manager closed")
