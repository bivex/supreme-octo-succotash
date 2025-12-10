"""Form repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..entities.form import Lead, FormSubmission, LeadScore, FormValidationRule, LeadStatus, LeadSource


class FormRepository(ABC):
    """Abstract repository for form and lead data access."""

    @abstractmethod
    def save_form_submission(self, submission: FormSubmission) -> None:
        """Save form submission."""
        pass

    @abstractmethod
    def get_form_submission(self, submission_id: str) -> Optional[FormSubmission]:
        """Get form submission by ID."""
        pass

    @abstractmethod
    def get_submissions_by_form(self, form_id: str, limit: int = 100) -> List[FormSubmission]:
        """Get submissions for a specific form."""
        pass

    @abstractmethod
    def get_submissions_by_ip(self, ip_address: str, time_window_minutes: int = 60) -> List[FormSubmission]:
        """Get submissions from IP address within time window (for spam detection)."""
        pass

    @abstractmethod
    def save_lead(self, lead: Lead) -> None:
        """Save lead data."""
        pass

    @abstractmethod
    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        pass

    @abstractmethod
    def get_lead_by_email(self, email: str) -> Optional[Lead]:
        """Get lead by email address."""
        pass

    @abstractmethod
    def get_leads_by_status(self, status: LeadStatus, limit: int = 100) -> List[Lead]:
        """Get leads by status."""
        pass

    @abstractmethod
    def get_leads_by_source(self, source: LeadSource, limit: int = 100) -> List[Lead]:
        """Get leads by source."""
        pass

    @abstractmethod
    def get_hot_leads(self, score_threshold: int = 70, limit: int = 100) -> List[Lead]:
        """Get hot leads above score threshold."""
        pass

    @abstractmethod
    def update_lead_status(self, lead_id: str, status: LeadStatus) -> None:
        """Update lead status."""
        pass

    @abstractmethod
    def save_lead_score(self, score: LeadScore) -> None:
        """Save lead score."""
        pass

    @abstractmethod
    def get_lead_score(self, lead_id: str) -> Optional[LeadScore]:
        """Get lead score by lead ID."""
        pass

    @abstractmethod
    def save_validation_rule(self, rule: FormValidationRule) -> None:
        """Save form validation rule."""
        pass

    @abstractmethod
    def get_validation_rules(self, form_id: str) -> List[FormValidationRule]:
        """Get validation rules for a form."""
        pass

    @abstractmethod
    def get_form_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get form submission analytics for date range."""
        pass

    @abstractmethod
    def get_lead_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get lead conversion funnel analytics."""
        pass

    @abstractmethod
    def check_duplicate_submission(self, form_data: Dict[str, Any],
                                 ip_address: str, time_window_hours: int = 24) -> bool:
        """Check if submission is duplicate within time window."""
        pass
