"""
Domain Exceptions

Business rule violations and domain-specific errors.
"""


class DomainException(Exception):
    """Base exception for all domain errors."""
    pass


class ValidationError(DomainException):
    """Raised when domain invariants are violated."""
    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity cannot be found."""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class InvalidBudgetError(ValidationError):
    """Raised when budget constraints are violated."""
    pass


class InvalidDateRangeError(ValidationError):
    """Raised when date range is invalid."""
    pass


class CampaignNotActiveError(DomainException):
    """Raised when attempting operations on inactive campaigns."""
    pass
