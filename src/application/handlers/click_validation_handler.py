"""Click validation handler."""

import uuid
import time
from typing import Optional, Dict, Any
from loguru import logger


class ClickValidationHandler:
    """Handler for click validation operations."""

    def __init__(self):
        """Initialize click validation handler."""
        # Mock fraud patterns for demonstration
        self.fraud_patterns = {
            'user_agents': ['bot', 'crawler', 'spider', 'scraper'],
            'suspicious_ips': ['192.168.1.1', '10.0.0.1'],  # Mock suspicious IPs
            'blocked_countries': ['RU', 'CN', 'KP']  # Mock geo-blocking
        }

    def validate_click(self, click_id: str, user_agent: Optional[str] = None,
                      ip_address: Optional[str] = None, referrer: Optional[str] = None) -> Dict[str, Any]:
        """Validate a click before redirect.

        Args:
            click_id: Unique click identifier
            user_agent: Client user agent string
            ip_address: Client IP address
            referrer: HTTP referrer

        Returns:
            Dict containing validation results
        """
        try:
            logger.info(f"Validating click {click_id}")

            # Base validation result
            result = {
                "clickId": click_id,
                "isValid": True,
                "fraudScore": 0.0,
                "validationReason": "passed_all_checks",
                "blockedReason": None,
                "campaignId": "camp_123",  # Mock campaign ID
                "landingPageId": "lp_456",  # Mock landing page ID
                "offerId": "offer_789"      # Mock offer ID
            }

            # Fraud scoring logic
            fraud_score = 0.0
            blocked_reason = None

            # Check user agent for bots/crawlers
            if user_agent:
                ua_lower = user_agent.lower()
                for pattern in self.fraud_patterns['user_agents']:
                    if pattern in ua_lower:
                        fraud_score += 0.7
                        blocked_reason = f"Suspicious user agent pattern: {pattern}"
                        break

            # Check IP address
            if ip_address:
                if ip_address in self.fraud_patterns['suspicious_ips']:
                    fraud_score += 0.8
                    blocked_reason = "IP address blacklisted"
                else:
                    # Mock geo-blocking based on IP
                    # In real implementation, this would use a geo-IP service
                    if ip_address.startswith('192.168.') or ip_address.startswith('10.'):
                        fraud_score += 0.3  # Local/private IPs might be suspicious

            # Check referrer
            if referrer:
                # Mock referrer validation
                suspicious_domains = ['suspicious-site.com', 'spam-domain.net']
                for domain in suspicious_domains:
                    if domain in referrer:
                        fraud_score += 0.5
                        if not blocked_reason:
                            blocked_reason = "Suspicious referrer domain"
                        break

            # Additional validation rules
            # Check click ID format (should be UUID)
            try:
                uuid.UUID(click_id)
            except (ValueError, TypeError):
                fraud_score = 1.0
                blocked_reason = "Invalid click ID format"
                result["isValid"] = False

            # Check for rapid clicks (mock rate limiting)
            # In real implementation, this would check Redis/cache for recent clicks from same IP
            current_time = time.time()
            # Mock: if IP has made clicks in last 0.1 seconds, increase fraud score
            if ip_address:
                fraud_score += 0.1  # Small penalty for rate limiting simulation

            # Final fraud score calculation
            result["fraudScore"] = min(fraud_score, 1.0)  # Cap at 1.0

            # Determine if click should be blocked
            if result["fraudScore"] >= 0.8 or blocked_reason:
                result["isValid"] = False
                result["validationReason"] = "blocked_by_fraud_detection"
                result["blockedReason"] = blocked_reason or "High fraud score"

                # Set redirect URL to safe page for blocked clicks
                result["redirectUrl"] = "https://example.com/safe-page"
            else:
                # Valid click - set redirect URL to offer
                result["redirectUrl"] = "https://affiliate.com/offer/123"

                if result["fraudScore"] > 0.3:
                    result["validationReason"] = "passed_with_warnings"

            logger.info(f"Click {click_id} validation result: valid={result['isValid']}, score={result['fraudScore']:.2f}")

            return result

        except Exception as e:
            logger.error(f"Error validating click {click_id}: {e}", exc_info=True)
            return {
                "clickId": click_id,
                "isValid": False,
                "fraudScore": 1.0,
                "validationReason": "validation_error",
                "blockedReason": "Internal validation error",
                "redirectUrl": "https://example.com/safe-page"
            }
