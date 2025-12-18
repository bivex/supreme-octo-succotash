# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:30
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Postback entity."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PostbackStatus(Enum):
    """Postback delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Postback:
    """Postback notification entity."""

    id: str
    conversion_id: str
    url: str
    method: str  # 'GET', 'POST'
    payload: Optional[Dict[str, Any]]
    headers: Optional[Dict[str, str]]
    status: PostbackStatus
    attempt_count: int
    max_attempts: int
    last_attempt_at: Optional[datetime]
    next_attempt_at: Optional[datetime]
    response_code: Optional[int]
    response_body: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    @classmethod
    def create_from_conversion(
        cls,
        conversion_id: str,
        postback_config: Dict[str, Any]
    ) -> 'Postback':
        """Create postback from conversion and configuration."""
        import uuid
        from datetime import datetime

        return cls(
            id=str(uuid.uuid4()),
            conversion_id=conversion_id,
            url=postback_config['url'],
            method=postback_config.get('method', 'GET'),
            payload=postback_config.get('payload'),
            headers=postback_config.get('headers'),
            status=PostbackStatus.PENDING,
            attempt_count=0,
            max_attempts=postback_config.get('max_attempts', 3),
            last_attempt_at=None,
            next_attempt_at=datetime.utcnow(),  # Schedule immediate attempt
            response_code=None,
            response_body=None,
            error_message=None,
            created_at=datetime.utcnow(),
            completed_at=None
        )

    def mark_attempted(self, response_code: Optional[int], response_body: Optional[str], error_message: Optional[str]) -> None:
        """Mark a delivery attempt."""
        from datetime import datetime, timedelta

        self.attempt_count += 1
        self.last_attempt_at = datetime.utcnow()
        self.response_code = response_code
        self.response_body = response_body
        self.error_message = error_message

        if response_code and 200 <= response_code < 300:
            # Success
            self.status = PostbackStatus.SENT
            self.completed_at = datetime.utcnow()
            self.next_attempt_at = None
        elif self.attempt_count >= self.max_attempts:
            # Max attempts reached
            self.status = PostbackStatus.FAILED
            self.completed_at = datetime.utcnow()
            self.next_attempt_at = None
        else:
            # Schedule retry with exponential backoff
            delay_minutes = 2 ** (self.attempt_count - 1)  # 1, 2, 4, 8 minutes
            self.status = PostbackStatus.RETRYING
            self.next_attempt_at = datetime.utcnow() + timedelta(minutes=delay_minutes)

    def should_attempt_now(self) -> bool:
        """Check if postback should be attempted now."""
        if self.status in [PostbackStatus.SENT, PostbackStatus.FAILED]:
            return False

        if not self.next_attempt_at:
            return False

        from datetime import datetime
        return datetime.utcnow() >= self.next_attempt_at
