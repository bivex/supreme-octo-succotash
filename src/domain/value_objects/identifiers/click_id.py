"""Click ID value object."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ClickId:
    """Value object representing a unique click identifier."""

    value: str

    def __post_init__(self) -> None:
        """Validate click ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Click ID must be a non-empty string")

        # Basic UUID format validation (without strict checking for performance)
        if len(self.value) < 10:
            raise ValueError("Click ID is too short")

    @classmethod
    def generate(cls) -> 'ClickId':
        """Generate a new unique click ID."""
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> 'ClickId':
        """Create ClickId from string."""
        return cls(value)

    def __str__(self) -> str:
        return self.value
