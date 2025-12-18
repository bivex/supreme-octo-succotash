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

"""In-memory postback repository implementation."""

from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
from ...domain.repositories.postback_repository import PostbackRepository
from ...domain.entities.postback import Postback, PostbackStatus


class InMemoryPostbackRepository(PostbackRepository):
    """In-memory implementation of postback repository."""

    def __init__(self):
        self._postbacks: Dict[str, Postback] = {}
        self._conversion_index: Dict[str, List[str]] = {}  # conversion_id -> list of postback_ids
        self._status_index: Dict[PostbackStatus, List[str]] = {}  # status -> list of postback_ids

    def save(self, postback: Postback) -> None:
        """Save a postback."""
        self._postbacks[postback.id] = postback

        # Update conversion index
        if postback.conversion_id not in self._conversion_index:
            self._conversion_index[postback.conversion_id] = []
        if postback.id not in self._conversion_index[postback.conversion_id]:
            self._conversion_index[postback.conversion_id].append(postback.id)

        # Update status index
        # Remove from old status if exists
        for status, postback_ids in self._status_index.items():
            if postback.id in postback_ids:
                postback_ids.remove(postback.id)

        # Add to new status
        if postback.status not in self._status_index:
            self._status_index[postback.status] = []
        self._status_index[postback.status].append(postback.id)

    def get_by_id(self, postback_id: str) -> Optional[Postback]:
        """Get postback by ID."""
        return self._postbacks.get(postback_id)

    def get_by_conversion_id(self, conversion_id: str) -> List[Postback]:
        """Get postbacks by conversion ID."""
        postback_ids = self._conversion_index.get(conversion_id, [])
        return [self._postbacks[pid] for pid in postback_ids if pid in self._postbacks]

    def get_pending(self, limit: int = 100) -> List[Postback]:
        """Get pending postbacks ready for delivery."""
        pending_ids = self._status_index.get(PostbackStatus.PENDING, [])
        pending_postbacks = [self._postbacks[pid] for pid in pending_ids if pid in self._postbacks]
        return pending_postbacks[:limit]

    def get_by_status(self, status: PostbackStatus, limit: int = 100) -> List[Postback]:
        """Get postbacks by status."""
        status_ids = self._status_index.get(status, [])
        status_postbacks = [self._postbacks[pid] for pid in status_ids if pid in self._postbacks]
        return status_postbacks[:limit]

    def update_status(self, postback_id: str, status: PostbackStatus) -> None:
        """Update postback status."""
        if postback_id in self._postbacks:
            postback = self._postbacks[postback_id]
            # Create updated postback (since Postback is a dataclass)
            updated_postback = Postback(
                id=postback.id,
                conversion_id=postback.conversion_id,
                url=postback.url,
                method=postback.method,
                payload=postback.payload,
                headers=postback.headers,
                status=status,
                attempt_count=postback.attempt_count,
                max_attempts=postback.max_attempts,
                last_attempt_at=postback.last_attempt_at,
                next_attempt_at=postback.next_attempt_at,
                response_code=postback.response_code,
                response_body=postback.response_body,
                error_message=postback.error_message,
                created_at=postback.created_at,
                completed_at=postback.completed_at
            )
            self.save(updated_postback)

    def get_retry_candidates(self, current_time: datetime, limit: int = 50) -> List[Postback]:
        """Get postbacks that should be retried now."""
        retrying_ids = self._status_index.get(PostbackStatus.RETRYING, [])
        retry_candidates = []

        for postback_id in retrying_ids:
            if postback_id in self._postbacks:
                postback = self._postbacks[postback_id]
                if postback.should_attempt_now():
                    retry_candidates.append(postback)

        return retry_candidates[:limit]
