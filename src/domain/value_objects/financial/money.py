"""Money value object for handling monetary amounts with currency."""

from dataclasses import dataclass
from typing import Union
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class Money:
    """Value object representing monetary amount with currency."""

    amount: Decimal
    _currency: str  # Private attribute

    def __post_init__(self) -> None:
        """Validate money object invariants."""
        if not isinstance(self.amount, Decimal):
            raise ValueError("Amount must be a Decimal")

        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

        if not self._currency or not isinstance(self._currency, str):
            raise ValueError("Currency must be a non-empty string")

    @property
    def currency(self) -> str:
        """Get normalized currency code."""
        return self._currency.upper()

    @classmethod
    def from_float(cls, amount: Union[float, int], currency: str) -> 'Money':
        """Create Money from float/int amount."""
        if isinstance(amount, float) and (amount == float('inf') or amount == float('-inf') or str(amount) == 'nan'):
            raise ValueError("Amount must be a finite number")
        return cls(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), currency)

    @classmethod
    def zero(cls, currency: str) -> 'Money':
        """Create zero money for given currency."""
        return cls(Decimal('0.00'), currency)

    def add(self, other: 'Money') -> 'Money':
        """Add two Money objects."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add money with different currencies: {self.currency} vs {other.currency}")
        return Money(self.amount + other.amount, self._currency)

    def subtract(self, other: 'Money') -> 'Money':
        """Subtract two Money objects."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract money with different currencies: {self.currency} vs {other.currency}")
        return Money(self.amount - other.amount, self._currency)

    def multiply(self, factor: Union[int, float, Decimal]) -> 'Money':
        """Multiply money by a factor."""
        return Money(self.amount * Decimal(str(factor)), self._currency)

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} vs {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} vs {other.currency}")
        return self.amount <= other.amount

    def __gt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} vs {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} vs {other.currency}")
        return self.amount >= other.amount
