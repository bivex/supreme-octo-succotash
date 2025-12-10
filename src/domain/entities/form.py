"""Form processing domain entities."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class LeadStatus(Enum):
    """Lead status in the sales funnel."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadSource(Enum):
    """Source of the lead."""
    AFFILIATE = "affiliate"
    ORGANIC = "organic"
    PAID_AD = "paid_ad"
    REFERRAL = "referral"
    DIRECT = "direct"
    SOCIAL = "social"


@dataclass
class LeadScore:
    """Lead scoring information."""

    lead_id: str
    total_score: int
    scores: Dict[str, int]  # category -> score
    grade: str  # A, B, C, D, F
    is_hot_lead: bool
    reasons: List[str]
    created_at: datetime
    updated_at: datetime

    @property
    def score_percentage(self) -> float:
        """Get score as percentage."""
        return min(100.0, (self.total_score / 100.0) * 100)

    @property
    def is_qualified(self) -> bool:
        """Check if lead is qualified based on score."""
        return self.total_score >= 70


@dataclass
class FormSubmission:
    """Form submission data."""

    id: str
    form_id: str
    campaign_id: Optional[str]
    click_id: Optional[str]
    ip_address: str
    user_agent: str
    referrer: Optional[str]
    form_data: Dict[str, Any]
    validation_errors: List[str]
    is_valid: bool
    is_duplicate: bool
    duplicate_of: Optional[str]
    submitted_at: datetime
    processed_at: Optional[datetime]

    @property
    def has_validation_errors(self) -> bool:
        """Check if submission has validation errors."""
        return len(self.validation_errors) > 0

    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Get processing time in seconds."""
        if self.processed_at is None:
            return None
        return (self.processed_at - self.submitted_at).total_seconds()


@dataclass
class Lead:
    """Lead entity."""

    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    source: LeadSource
    source_campaign: Optional[str]
    status: LeadStatus
    lead_score: Optional[LeadScore]
    tags: List[str]
    custom_fields: Dict[str, Any]
    first_submission_id: str
    last_submission_id: str
    submission_count: int
    converted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @property
    def full_name(self) -> str:
        """Get full name."""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else "Unknown"

    @property
    def is_converted(self) -> bool:
        """Check if lead has been converted."""
        return self.converted_at is not None

    @property
    def days_since_creation(self) -> int:
        """Get days since lead creation."""
        return (datetime.now() - self.created_at).days

    @property
    def lead_quality(self) -> str:
        """Get lead quality based on score."""
        if not self.lead_score:
            return "Unknown"
        return self.lead_score.grade


@dataclass
class FormValidationRule:
    """Form validation rule."""

    id: str
    field_name: str
    rule_type: str  # 'required', 'email', 'phone', 'regex', 'length'
    rule_value: Optional[str]
    error_message: str
    is_active: bool
    created_at: datetime

    def validate(self, value: Any) -> Optional[str]:
        """Validate field value against this rule."""
        if not self.is_active:
            return None

        if self.rule_type == 'required' and not value:
            return self.error_message

        if self.rule_type == 'email' and value:
            import re
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)):
                return self.error_message

        if self.rule_type == 'phone' and value:
            import re
            if not re.match(r'^\+?[\d\s\-\(\)]+$', str(value)):
                return self.error_message

        if self.rule_type == 'regex' and value and self.rule_value:
            import re
            if not re.match(self.rule_value, str(value)):
                return self.error_message

        if self.rule_type == 'length' and value and self.rule_value:
            min_len, max_len = map(int, self.rule_value.split(','))
            if not (min_len <= len(str(value)) <= max_len):
                return self.error_message

        return None
