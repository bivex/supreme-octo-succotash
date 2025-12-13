"""Money Value Object - Represents monetary amounts."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Union

from ..exceptions import ValidationError


@dataclass(frozen=True)
class Money:
    """
    Immutable Money value object.

    Represents a monetary amount with currency.
    Enforces positive amounts and valid currency codes.
    """

    amount: Decimal
    currency: str

    def __post_init__(self):
        """Validate invariants."""
        if self.amount < 0:
            raise ValidationError(f"Money amount cannot be negative: {self.amount}")

        if not self.currency or len(self.currency) != 3:
            raise ValidationError(f"Invalid currency code: {self.currency}")

        # Ensure currency is uppercase
        object.__setattr__(self, 'currency', self.currency.upper())

    @classmethod
    def from_float(cls, amount: float, currency: str) -> 'Money':
        """Create Money from float amount."""
        return cls(Decimal(str(amount)), currency)

    @classmethod
    def zero(cls, currency: str = 'USD') -> 'Money':
        """Create zero money."""
        return cls(Decimal('0'), currency)

    def add(self, other: 'Money') -> 'Money':
        """Add two Money objects (must have same currency)."""
        if self.currency != other.currency:
            raise ValidationError(
                f"Cannot add money with different currencies: "
                f"{self.currency} and {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def to_float(self) -> float:
        """Convert to float (for display/serialization)."""
        return float(self.amount)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __repr__(self) -> str:
        return f"Money({self.amount}, {self.currency})"
