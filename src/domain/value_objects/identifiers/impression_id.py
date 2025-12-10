"""Impression ID value object."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ImpressionId:
    """Value object representing a unique impression identifier."""

    value: str

    def __post_init__(self) -> None:
        """Validate impression ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Impression ID must be a non-empty string")

        # Basic UUID format validation (without strict checking for performance)
        if len(self.value) < 10:
            raise ValueError("Impression ID is too short")

    @classmethod
    def generate(cls) -> 'ImpressionId':
        """Generate a new unique impression ID."""
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> 'ImpressionId':
        """Create ImpressionId from string."""
        return cls(value)

    def __str__(self) -> str:
        return self.value
