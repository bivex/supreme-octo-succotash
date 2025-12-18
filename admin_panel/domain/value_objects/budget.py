# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:34
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Budget Value Object - Represents campaign budgets."""

from dataclasses import dataclass
from enum import Enum

from .money import Money
from ..exceptions import InvalidBudgetError


class BudgetType(Enum):
    """Budget type enumeration."""
    DAILY = "daily"
    TOTAL = "total"


@dataclass(frozen=True)
class Budget:
    """
    Immutable Budget value object.

    Represents a campaign budget with amount and type.
    """

    amount: Money
    budget_type: BudgetType

    def __post_init__(self):
        """Validate budget invariants."""
        if not self.amount.is_positive():
            raise InvalidBudgetError("Budget amount must be positive")

    @classmethod
    def create_daily(cls, amount: Money) -> 'Budget':
        """Create a daily budget."""
        return cls(amount, BudgetType.DAILY)

    @classmethod
    def create_total(cls, amount: Money) -> 'Budget':
        """Create a total budget."""
        return cls(amount, BudgetType.TOTAL)

    def is_daily(self) -> bool:
        """Check if this is a daily budget."""
        return self.budget_type == BudgetType.DAILY

    def is_total(self) -> bool:
        """Check if this is a total budget."""
        return self.budget_type == BudgetType.TOTAL

    def __str__(self) -> str:
        return f"{self.amount} ({self.budget_type.value})"
