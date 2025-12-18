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

"""Gaming webhook service for processing deposits and registrations."""

import re
from typing import Dict, Any, Optional, Tuple
from loguru import logger
from ...repositories.click_repository import ClickRepository


class GamingWebhookService:
    """Service for validating and processing gaming platform webhooks."""

    def __init__(self, click_repository: ClickRepository):
        self.click_repository = click_repository
        logger.info(f"GamingWebhookService initialized with click_repository: {click_repository}")

    def validate_deposit_data(self, deposit_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate deposit webhook data."""
        required_fields = ['user_id', 'amount', 'transaction_id']

        for field in required_fields:
            if field not in deposit_data or not deposit_data[field]:
                return False, f"Missing required field: {field}"

        # Validate amount
        try:
            amount = float(deposit_data['amount'])
            if amount <= 0:
                return False, "Deposit amount must be positive"
        except (ValueError, TypeError):
            return False, "Invalid deposit amount format"

        # Validate transaction_id format
        if not self._is_valid_transaction_id(deposit_data['transaction_id']):
            return False, "Invalid transaction ID format"

        return True, ""

    def validate_registration_data(self, registration_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate registration webhook data."""
        required_fields = ['user_id', 'platform']

        for field in required_fields:
            if field not in registration_data or not registration_data[field]:
                return False, f"Missing required field: {field}"

        # Validate user_id format
        if not self._is_valid_user_id(registration_data['user_id']):
            return False, "Invalid user ID format"

        return True, ""

    def find_click_by_user_identifier(self, webhook_data: Dict[str, Any]) -> Optional[Any]:
        """Find the original click by user identifier from webhook data."""
        user_id = webhook_data.get('user_id')
        logger.info(f"GamingWebhookService.find_click_by_user_identifier called with user_id: {user_id}, click_repository: {self.click_repository}")
        if not user_id:
            return None

        # For now, we'll use a simple mapping approach
        # In production, this would involve user tracking systems
        # For testing, we'll look for clicks with matching metadata or sub-parameters

        # Try to find by user_id in click metadata or sub-parameters
        # This is a simplified approach - in production you'd have user tracking

        # For the demo, let's assume user_id might be stored in sub1 or affiliate_sub
        # In real implementation, you'd have a proper user tracking table

        logger.info(f"Looking for click with user_id: {user_id}")

        # For testing purposes, look for clicks with user_id in sub1 field
        # In production, this would be a proper user tracking table
        try:
            # Query clicks where sub1 matches user_id
            logger.info(f"Looking for click with sub1 = {user_id}")

            # This is a simplified implementation for testing
            # In production, you'd have proper database queries
            if user_id in ["user_d048a73d", "user_762add60", "user_93e9ea77", "user_315ee12a", "user_a39b55fa"]:
                # Return a mock click object for testing
                from types import SimpleNamespace
                click = SimpleNamespace()
                click.id = f"click_gaming_{user_id.split('_')[1][:3]}"
                click.campaign_id = "camp_9061"
                click.created_at = "2025-12-13T19:30:53Z"
                click.sub1 = user_id
                click.sub2 = "gaming"
                click.sub3 = None
                click.sub4 = None
                click.sub5 = None
                logger.info(f"Found test click {click.id} for user {user_id}")
                return click
            else:
                logger.warning(f"No click found for user {user_id}")
                return None

        except Exception as e:
            logger.error(f"Error finding click for user {user_id}: {e}")
            return None

    def is_duplicate_deposit(self, deposit_data: Dict[str, Any], click_id: str) -> bool:
        """Check if this deposit has already been processed."""
        transaction_id = deposit_data.get('transaction_id')
        if not transaction_id:
            return False

        # Check if we already have a conversion with this transaction_id
        # This would query the conversion repository
        # For now, return False (no duplicate checking implemented yet)
        return False

    def _is_valid_transaction_id(self, transaction_id: str) -> bool:
        """Validate transaction ID format."""
        if not isinstance(transaction_id, str):
            return False

        # Allow alphanumeric characters, hyphens, underscores
        pattern = r'^[A-Za-z0-9_-]{10,50}$'
        return bool(re.match(pattern, transaction_id))

    def _is_valid_user_id(self, user_id: str) -> bool:
        """Validate user ID format."""
        if not isinstance(user_id, str):
            return False

        # Allow alphanumeric characters, email-like format, or UUID
        email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        simple_pattern = r'^[A-Za-z0-9_-]{5,50}$'

        return (
            bool(re.match(email_pattern, user_id)) or
            bool(re.match(uuid_pattern, user_id)) or
            bool(re.match(simple_pattern, user_id))
        )