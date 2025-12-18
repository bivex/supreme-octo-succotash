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

"""LTV repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..entities.ltv import Cohort, CustomerLTV, LTVSegment


class LTVRepository(ABC):
    """Abstract repository for LTV data access."""

    @abstractmethod
    def save_customer_ltv(self, customer_ltv: CustomerLTV) -> None:
        """Save customer LTV data."""
        pass

    @abstractmethod
    def get_customer_ltv(self, customer_id: str) -> Optional[CustomerLTV]:
        """Get customer LTV by ID."""
        pass

    @abstractmethod
    def get_customers_by_segment(self, segment: str, limit: int = 100) -> List[CustomerLTV]:
        """Get customers by LTV segment."""
        pass

    @abstractmethod
    def get_customers_by_cohort(self, cohort_id: str) -> List[CustomerLTV]:
        """Get customers by cohort ID."""
        pass

    @abstractmethod
    def save_cohort(self, cohort: Cohort) -> None:
        """Save cohort data."""
        pass

    @abstractmethod
    def get_cohort(self, cohort_id: str) -> Optional[Cohort]:
        """Get cohort by ID."""
        pass

    @abstractmethod
    def get_all_cohorts(self, limit: int = 100) -> List[Cohort]:
        """Get all cohorts."""
        pass

    @abstractmethod
    def save_ltv_segment(self, segment: LTVSegment) -> None:
        """Save LTV segment data."""
        pass

    @abstractmethod
    def get_ltv_segment(self, segment_id: str) -> Optional[LTVSegment]:
        """Get LTV segment by ID."""
        pass

    @abstractmethod
    def get_all_ltv_segments(self) -> List[LTVSegment]:
        """Get all LTV segments."""
        pass

    @abstractmethod
    def get_ltv_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get LTV analytics for date range."""
        pass
