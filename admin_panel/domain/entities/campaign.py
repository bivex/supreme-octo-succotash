"""Campaign Entity - Aggregate Root."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects import Budget, DateRange
from ..exceptions import ValidationError, CampaignNotActiveError


class CampaignStatus(Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Campaign:
    """
    Campaign Aggregate Root.

    Represents an advertising campaign with its business rules and invariants.
    This is the boundary of consistency for campaign-related operations.
    """

    # Identity
    id: str
    name: str

    # Core attributes
    status: CampaignStatus
    budget: Budget
    target_url: str
    date_range: DateRange

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Domain invariants enforced on creation
    def __post_init__(self):
        """Validate campaign invariants."""
        self._validate_name()
        self._validate_target_url()

    def _validate_name(self):
        """Ensure campaign name is not empty and within limits."""
        if not self.name or not self.name.strip():
            raise ValidationError("Campaign name cannot be empty")

        if len(self.name) > 255:
            raise ValidationError("Campaign name cannot exceed 255 characters")

    def _validate_target_url(self):
        """Ensure target URL is valid."""
        if not self.target_url or not self.target_url.strip():
            raise ValidationError("Target URL cannot be empty")

        if not (self.target_url.startswith('http://') or
                self.target_url.startswith('https://')):
            raise ValidationError("Target URL must start with http:// or https://")

    # Business operations
    def activate(self) -> None:
        """Activate the campaign."""
        if self.status == CampaignStatus.COMPLETED:
            raise ValidationError("Cannot activate a completed campaign")

        self.status = CampaignStatus.ACTIVE

    def pause(self) -> None:
        """Pause the campaign."""
        if self.status != CampaignStatus.ACTIVE:
            raise ValidationError("Only active campaigns can be paused")

        self.status = CampaignStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused campaign."""
        if self.status != CampaignStatus.PAUSED:
            raise ValidationError("Only paused campaigns can be resumed")

        self.status = CampaignStatus.ACTIVE

    def complete(self) -> None:
        """Mark campaign as completed."""
        self.status = CampaignStatus.COMPLETED

    def update_budget(self, new_budget: Budget) -> None:
        """Update campaign budget."""
        if self.status == CampaignStatus.COMPLETED:
            raise ValidationError("Cannot update budget of completed campaign")

        self.budget = new_budget

    def update_target_url(self, new_url: str) -> None:
        """Update target URL with validation."""
        old_url = self.target_url
        self.target_url = new_url

        try:
            self._validate_target_url()
        except ValidationError:
            # Rollback on validation failure
            self.target_url = old_url
            raise

    # Query methods
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        return (self.status == CampaignStatus.ACTIVE and
                self.date_range.is_active())

    def is_editable(self) -> bool:
        """Check if campaign can be edited."""
        return self.status != CampaignStatus.COMPLETED

    def can_receive_traffic(self) -> bool:
        """Check if campaign can receive traffic."""
        return self.is_active()

    # Factory methods
    @classmethod
    def create(
        cls,
        name: str,
        budget: Budget,
        target_url: str,
        date_range: DateRange,
        campaign_id: Optional[str] = None
    ) -> 'Campaign':
        """
        Factory method to create a new campaign in DRAFT status.

        This is the recommended way to create campaigns.
        """
        return cls(
            id=campaign_id or str(uuid4()),
            name=name,
            status=CampaignStatus.DRAFT,
            budget=budget,
            target_url=target_url,
            date_range=date_range
        )

    # Representation
    def __str__(self) -> str:
        return f"Campaign(id={self.id}, name={self.name}, status={self.status.value})"

    def __repr__(self) -> str:
        return (f"Campaign(id={self.id!r}, name={self.name!r}, "
                f"status={self.status!r}, budget={self.budget!r})")
