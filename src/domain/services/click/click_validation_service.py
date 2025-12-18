# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Click validation service for fraud detection and bot filtering."""

import re
from typing import Optional, Tuple, List
from ipaddress import ip_address

from ...entities.click import Click
from ...constants import BOT_DETECTION_PATTERNS


class ClickValidationService:
    """Domain service for validating clicks and detecting fraud."""

    # Suspicious referrer patterns
    SUSPICIOUS_REFERRER_PATTERNS = [
        r'localhost',
        r'127\.0\.0\.1',
        r'0\.0\.0\.0',
        r'example\.com',
        r'test\.',
    ]

    def validate_click(self, click: Click, campaign_filters: Optional[dict] = None) -> Tuple[bool, Optional[str], float]:
        """
        Validate a click for fraud and bot detection.

        Returns:
            Tuple of (is_valid, reason, fraud_score)
        """
        fraud_score, reasons = self._calculate_fraud_score(click, campaign_filters)
        is_valid = fraud_score < 0.5
        reason = '; '.join(reasons) if reasons else None

        return is_valid, reason, min(fraud_score, 1.0)

    def _calculate_fraud_score(self, click: Click, campaign_filters: Optional[dict]) -> Tuple[float, List[str]]:
        """Calculate fraud score and collect reasons."""
        fraud_score = 0.0
        reasons = []

        self._check_bot_detection(click.user_agent, fraud_score, reasons)
        self._check_ip_validation(click.ip_address, fraud_score, reasons)
        self._check_referrer_validation(click.referrer, fraud_score, reasons)

        if campaign_filters:
            self._check_campaign_filters(click, campaign_filters, fraud_score, reasons)

        self._check_tracking_parameters(click, fraud_score, reasons)

        return fraud_score, reasons

    def _check_bot_detection(self, user_agent: Optional[str], fraud_score: float, reasons: List[str]) -> None:
        """Check for bot detection by user agent."""
        is_bot, bot_reason = self._detect_bot_by_user_agent(user_agent)
        if is_bot:
            fraud_score += 1.0
            reasons.append(bot_reason)

    def _check_ip_validation(self, ip_address: Optional[str], fraud_score: float, reasons: List[str]) -> None:
        """Check IP address validation."""
        ip_valid, ip_reason = self._validate_ip_address(ip_address)
        if not ip_valid:
            fraud_score += 0.3
            reasons.append(ip_reason)

    def _check_referrer_validation(self, referrer: Optional[str], fraud_score: float, reasons: List[str]) -> None:
        """Check referrer validation."""
        referrer_valid, referrer_reason = self._validate_referrer(referrer)
        if not referrer_valid:
            fraud_score += 0.2
            reasons.append(referrer_reason)

    def _check_campaign_filters(self, click: Click, campaign_filters: dict, fraud_score: float, reasons: List[str]) -> None:
        """Check campaign-specific filters."""
        filter_valid, filter_reason = self._apply_campaign_filters(click, campaign_filters)
        if not filter_valid:
            fraud_score += 0.8
            reasons.append(filter_reason)

    def _check_tracking_parameters(self, click: Click, fraud_score: float, reasons: List[str]) -> None:
        """Check tracking parameters for suspicious patterns."""
        param_valid, param_reason = self._validate_tracking_parameters(click)
        if not param_valid:
            fraud_score += 0.1
            reasons.append(param_reason)

    def _detect_bot_by_user_agent(self, user_agent: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Detect bots based on user agent string."""
        if not user_agent:
            return True, "missing_user_agent"

        ua_lower = user_agent.lower()

        # Check for bot patterns
        for pattern in BOT_DETECTION_PATTERNS:
            if pattern in ua_lower:
                return True, f"bot_pattern_detected: {pattern}"

        # Check for suspicious patterns
        if len(user_agent) < 10:
            return True, "user_agent_too_short"

        if user_agent.count(' ') > 20:  # Unrealistically long user agent
            return True, "user_agent_suspiciously_long"

        return False, None

    def _validate_ip_address(self, ip: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate IP address format and check for suspicious IPs."""
        if not ip:
            return False, "missing_ip_address"

        try:
            ip_obj = ip_address(ip)
        except ValueError:
            return False, "invalid_ip_format"

        # Check for private/reserved IPs that shouldn't appear in production
        if ip_obj.is_private:
            return False, "private_ip_address"

        if ip_obj.is_reserved:
            return False, "reserved_ip_address"

        # Check for localhost IPs
        if ip in ['127.0.0.1', '::1', 'localhost']:
            return False, "localhost_ip_address"

        return True, None

    def _validate_referrer(self, referrer: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate referrer URL."""
        if not referrer:
            return True, None  # Missing referrer is not necessarily fraudulent

        if len(referrer) > 1000:
            return False, "referrer_too_long"

        # Check for suspicious patterns
        ref_lower = referrer.lower()
        for pattern in self.SUSPICIOUS_REFERRER_PATTERNS:
            if re.search(pattern, ref_lower):
                return False, f"suspicious_referrer_pattern: {pattern}"

        # Validate URL format
        if not (referrer.startswith('http://') or referrer.startswith('https://')):
            return False, "invalid_referrer_scheme"

        return True, None

    def _apply_campaign_filters(self, click: Click, filters: dict) -> Tuple[bool, Optional[str]]:
        """Apply campaign-specific filtering rules."""
        # IP blacklist check
        ip_blacklist = filters.get('ip_blacklist', [])
        if click.ip_address and click.ip_address in ip_blacklist:
            return False, "ip_blacklisted"

        # User agent filtering
        blocked_uas = filters.get('blocked_user_agents', [])
        if click.user_agent:
            ua_lower = click.user_agent.lower()
            for blocked_ua in blocked_uas:
                if blocked_ua.lower() in ua_lower:
                    return False, "user_agent_blocked"

        # Geo filtering would require IP geolocation service
        # For now, skip geo-based filtering

        return True, None

    def _validate_tracking_parameters(self, click: Click) -> Tuple[bool, Optional[str]]:
        """Validate tracking parameters for suspicious patterns."""
        # Pattern for valid tracking parameters (alphanumeric, dots, underscores, hyphens)
        valid_pattern = re.compile(r'^[a-zA-Z0-9._-]*$')

        tracking_params = click.tracking_params

        for param_name, param_value in tracking_params.items():
            if param_value is not None:
                if not valid_pattern.match(param_value):
                    return False, f"invalid_{param_name}_format"

                # Check for suspicious content
                suspicious_patterns = ['[filtered]', 'schemathesis', 'null', 'undefined', '<script>']
                val_lower = param_value.lower()
                for pattern in suspicious_patterns:
                    if pattern in val_lower:
                        return False, f"suspicious_{param_name}_content"

        return True, None
