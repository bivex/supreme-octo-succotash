"""In-memory form repository implementation."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ...domain.entities.form import Lead, FormSubmission, LeadScore, FormValidationRule, LeadStatus, LeadSource
from ...domain.repositories.form_repository import FormRepository


class InMemoryFormRepository(FormRepository):
    """In-memory implementation of FormRepository for testing and development."""

    def __init__(self):
        self._submissions: Dict[str, FormSubmission] = {}
        self._leads: Dict[str, Lead] = {}
        self._leads_by_email: Dict[str, str] = {}  # email -> lead_id mapping
        self._scores: Dict[str, LeadScore] = {}
        self._validation_rules: Dict[str, List[FormValidationRule]] = {}
        self._deleted_leads: set[str] = set()
        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        """Initialize with mock form and lead data."""
        # Create mock validation rules
        default_rules = [
            FormValidationRule(
                id="email_required",
                field_name="email",
                rule_type="required",
                error_message="Email is required",
                is_active=True,
                created_at=datetime.now()
            ),
            FormValidationRule(
                id="email_format",
                field_name="email",
                rule_type="email",
                error_message="Invalid email format",
                is_active=True,
                created_at=datetime.now()
            ),
            FormValidationRule(
                id="first_name_required",
                field_name="first_name",
                rule_type="required",
                error_message="First name is required",
                is_active=True,
                created_at=datetime.now()
            )
        ]
        self._validation_rules["default_form"] = default_rules

        # Create mock form submissions
        mock_submissions = [
            FormSubmission(
                id="sub_001",
                form_id="default_form",
                campaign_id="camp_123",
                click_id="click_456",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                referrer="https://google.com",
                form_data={
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "company": "Tech Corp",
                    "job_title": "Developer"
                },
                validation_errors=[],
                is_valid=True,
                is_duplicate=False,
                duplicate_of=None,
                submitted_at=datetime.now() - timedelta(hours=2),
                processed_at=datetime.now() - timedelta(hours=1, minutes=30)
            ),
            FormSubmission(
                id="sub_002",
                form_id="default_form",
                campaign_id=None,
                click_id=None,
                ip_address="192.168.1.101",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                referrer="https://facebook.com",
                form_data={
                    "email": "jane.smith@example.com",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "phone": "+1-555-0123",
                    "comments": "Interested in your services"
                },
                validation_errors=[],
                is_valid=True,
                is_duplicate=False,
                duplicate_of=None,
                submitted_at=datetime.now() - timedelta(hours=1),
                processed_at=datetime.now() - timedelta(minutes=45)
            )
        ]

        for submission in mock_submissions:
            self._submissions[submission.id] = submission

        # Create mock leads
        mock_leads = [
            Lead(
                id="lead_001",
                email="john.doe@example.com",
                first_name="John",
                last_name="Doe",
                phone=None,
                company="Tech Corp",
                job_title="Developer",
                source=LeadSource.AFFILIATE,
                source_campaign="camp_123",
                status=LeadStatus.NEW,
                lead_score=None,  # Will be set later
                tags=["b2b", "tech"],
                custom_fields={"interests": ["development", "cloud"]},
                first_submission_id="sub_001",
                last_submission_id="sub_001",
                submission_count=1,
                converted_at=None,
                created_at=datetime.now() - timedelta(hours=1, minutes=30),
                updated_at=datetime.now() - timedelta(hours=1, minutes=30)
            ),
            Lead(
                id="lead_002",
                email="jane.smith@example.com",
                first_name="Jane",
                last_name="Smith",
                phone="+1-555-0123",
                company=None,
                job_title=None,
                source=LeadSource.SOCIAL,
                source_campaign=None,
                status=LeadStatus.CONTACTED,
                lead_score=None,
                tags=["interested"],
                custom_fields={"comments": "Interested in your services"},
                first_submission_id="sub_002",
                last_submission_id="sub_002",
                submission_count=1,
                converted_at=None,
                created_at=datetime.now() - timedelta(minutes=45),
                updated_at=datetime.now() - timedelta(minutes=45)
            )
        ]

        for lead in mock_leads:
            self._leads[lead.id] = lead
            self._leads_by_email[lead.email] = lead.id

        # Create mock lead scores
        mock_scores = [
            LeadScore(
                lead_id="lead_001",
                total_score=75,
                scores={
                    "email_quality": 25,
                    "contact_info": 10,
                    "professional_info": 20,
                    "engagement": 10,
                    "company_size": 10
                },
                grade="B",
                is_hot_lead=True,
                reasons=["High engagement", "Professional background"],
                created_at=datetime.now() - timedelta(hours=1),
                updated_at=datetime.now() - timedelta(hours=1)
            ),
            LeadScore(
                lead_id="lead_002",
                total_score=65,
                scores={
                    "email_quality": 25,
                    "contact_info": 15,
                    "professional_info": 0,
                    "engagement": 15,
                    "social_proof": 10
                },
                grade="C",
                is_hot_lead=False,
                reasons=["Good engagement", "Contact info provided"],
                created_at=datetime.now() - timedelta(minutes=30),
                updated_at=datetime.now() - timedelta(minutes=30)
            )
        ]

        for score in mock_scores:
            self._scores[score.lead_id] = score

        # Link scores to leads
        self._leads["lead_001"].lead_score = mock_scores[0]
        self._leads["lead_002"].lead_score = mock_scores[1]

    def save_form_submission(self, submission: FormSubmission) -> None:
        """Save form submission."""
        self._submissions[submission.id] = submission

    def get_form_submission(self, submission_id: str) -> Optional[FormSubmission]:
        """Get form submission by ID."""
        return self._submissions.get(submission_id)

    def get_submissions_by_form(self, form_id: str, limit: int = 100) -> List[FormSubmission]:
        """Get submissions for a specific form."""
        matching_submissions = [s for s in self._submissions.values() if s.form_id == form_id]
        return sorted(matching_submissions, key=lambda x: x.submitted_at, reverse=True)[:limit]

    def get_submissions_by_ip(self, ip_address: str, time_window_minutes: int = 60) -> List[FormSubmission]:
        """Get submissions from IP address within time window."""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        matching_submissions = [
            s for s in self._submissions.values()
            if s.ip_address == ip_address and s.submitted_at >= cutoff_time
        ]
        return sorted(matching_submissions, key=lambda x: x.submitted_at, reverse=True)

    def save_lead(self, lead: Lead) -> None:
        """Save lead data."""
        self._leads[lead.id] = lead
        self._leads_by_email[lead.email] = lead.id

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        if lead_id in self._deleted_leads:
            return None
        return self._leads.get(lead_id)

    def get_lead_by_email(self, email: str) -> Optional[Lead]:
        """Get lead by email address."""
        lead_id = self._leads_by_email.get(email.lower().strip())
        if lead_id and lead_id not in self._deleted_leads:
            return self._leads.get(lead_id)
        return None

    def get_leads_by_status(self, status: LeadStatus, limit: int = 100) -> List[Lead]:
        """Get leads by status."""
        matching_leads = [
            l for l in self._leads.values()
            if l.id not in self._deleted_leads and l.status == status
        ]
        return sorted(matching_leads, key=lambda x: x.created_at, reverse=True)[:limit]

    def get_leads_by_source(self, source: LeadSource, limit: int = 100) -> List[Lead]:
        """Get leads by source."""
        matching_leads = [
            l for l in self._leads.values()
            if l.id not in self._deleted_leads and l.source == source
        ]
        return sorted(matching_leads, key=lambda x: x.created_at, reverse=True)[:limit]

    def get_hot_leads(self, score_threshold: int = 70, limit: int = 100) -> List[Lead]:
        """Get hot leads above score threshold."""
        hot_leads = []
        for lead in self._leads.values():
            if (lead.id not in self._deleted_leads and
                lead.lead_score and
                lead.lead_score.total_score >= score_threshold):
                hot_leads.append(lead)

        return sorted(hot_leads, key=lambda x: x.lead_score.total_score, reverse=True)[:limit]

    def update_lead_status(self, lead_id: str, status: LeadStatus) -> None:
        """Update lead status."""
        if lead_id in self._leads and lead_id not in self._deleted_leads:
            lead = self._leads[lead_id]
            updated_lead = Lead(
                id=lead.id,
                email=lead.email,
                first_name=lead.first_name,
                last_name=lead.last_name,
                phone=lead.phone,
                company=lead.company,
                job_title=lead.job_title,
                source=lead.source,
                source_campaign=lead.source_campaign,
                status=status,
                lead_score=lead.lead_score,
                tags=lead.tags,
                custom_fields=lead.custom_fields,
                first_submission_id=lead.first_submission_id,
                last_submission_id=lead.last_submission_id,
                submission_count=lead.submission_count,
                converted_at=lead.converted_at,
                created_at=lead.created_at,
                updated_at=datetime.now()
            )
            self._leads[lead_id] = updated_lead

    def save_lead_score(self, score: LeadScore) -> None:
        """Save lead score."""
        self._scores[score.lead_id] = score

        # Update linked lead if exists
        if score.lead_id in self._leads:
            lead = self._leads[score.lead_id]
            updated_lead = Lead(
                id=lead.id,
                email=lead.email,
                first_name=lead.first_name,
                last_name=lead.last_name,
                phone=lead.phone,
                company=lead.company,
                job_title=lead.job_title,
                source=lead.source,
                source_campaign=lead.source_campaign,
                status=lead.status,
                lead_score=score,
                tags=lead.tags,
                custom_fields=lead.custom_fields,
                first_submission_id=lead.first_submission_id,
                last_submission_id=lead.last_submission_id,
                submission_count=lead.submission_count,
                converted_at=lead.converted_at,
                created_at=lead.created_at,
                updated_at=datetime.now()
            )
            self._leads[score.lead_id] = updated_lead

    def get_lead_score(self, lead_id: str) -> Optional[LeadScore]:
        """Get lead score by lead ID."""
        return self._scores.get(lead_id)

    def save_validation_rule(self, rule: FormValidationRule) -> None:
        """Save form validation rule."""
        if rule.field_name not in self._validation_rules:
            self._validation_rules[rule.field_name] = []
        self._validation_rules[rule.field_name].append(rule)

    def get_validation_rules(self, form_id: str) -> List[FormValidationRule]:
        """Get validation rules for a form."""
        return self._validation_rules.get(form_id, [])

    def get_form_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get form submission analytics for date range."""
        # Filter submissions within date range
        relevant_submissions = [
            s for s in self._submissions.values()
            if s.submitted_at >= start_date and s.submitted_at <= end_date
        ]

        # Calculate metrics
        total_submissions = len(relevant_submissions)
        valid_submissions = len([s for s in relevant_submissions if s.is_valid])
        duplicate_submissions = len([s for s in relevant_submissions if s.is_duplicate])

        # Conversion metrics
        total_leads = len(set(s.form_data.get('email', '').lower() for s in relevant_submissions if s.form_data.get('email')))
        converted_leads = len([l for l in self._leads.values() if l.converted_at and start_date <= l.converted_at <= end_date])

        return {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'submission_metrics': {
                'total_submissions': total_submissions,
                'valid_submissions': valid_submissions,
                'duplicate_submissions': duplicate_submissions,
                'validation_rate': valid_submissions / max(total_submissions, 1),
                'duplicate_rate': duplicate_submissions / max(total_submissions, 1)
            },
            'lead_metrics': {
                'total_leads': total_leads,
                'converted_leads': converted_leads,
                'conversion_rate': converted_leads / max(total_leads, 1)
            },
            'source_distribution': self._get_source_distribution(relevant_submissions)
        }

    def get_lead_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get lead conversion funnel analytics."""
        # Filter leads created in date range
        relevant_leads = [
            l for l in self._leads.values()
            if l.created_at >= start_date and l.created_at <= end_date
        ]

        status_counts = defaultdict(int)
        for lead in relevant_leads:
            status_counts[lead.status.value] += 1

        return {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'funnel_stages': {
                'new': status_counts.get('new', 0),
                'contacted': status_counts.get('contacted', 0),
                'qualified': status_counts.get('qualified', 0),
                'proposal': status_counts.get('proposal', 0),
                'negotiation': status_counts.get('negotiation', 0),
                'closed_won': status_counts.get('closed_won', 0),
                'closed_lost': status_counts.get('closed_lost', 0)
            },
            'conversion_rates': self._calculate_conversion_rates(status_counts)
        }

    def check_duplicate_submission(self, form_data: Dict[str, Any],
                                 ip_address: str, time_window_hours: int = 24) -> bool:
        """Check if submission is duplicate within time window."""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        # Check by email + IP + time window
        email = form_data.get('email', '').lower().strip()
        if not email:
            return False

        for submission in self._submissions.values():
            if (submission.ip_address == ip_address and
                submission.form_data.get('email', '').lower().strip() == email and
                submission.submitted_at >= cutoff_time):
                return True

        return False

    def _get_source_distribution(self, submissions: List[FormSubmission]) -> Dict[str, int]:
        """Get distribution of submissions by source."""
        distribution = defaultdict(int)
        for submission in submissions:
            # Determine source from submission context (simplified)
            if submission.campaign_id:
                distribution['affiliate'] += 1
            elif 'google' in submission.user_agent.lower():
                distribution['organic'] += 1
            elif 'facebook' in submission.user_agent.lower():
                distribution['social'] += 1
            else:
                distribution['direct'] += 1
        return dict(distribution)

    def _calculate_conversion_rates(self, status_counts: Dict[str, int]) -> Dict[str, float]:
        """Calculate conversion rates between funnel stages."""
        total_new = status_counts.get('new', 0)
        if total_new == 0:
            return {}

        return {
            'new_to_contacted': status_counts.get('contacted', 0) / total_new,
            'contacted_to_qualified': status_counts.get('qualified', 0) / max(status_counts.get('contacted', 0), 1),
            'qualified_to_proposal': status_counts.get('proposal', 0) / max(status_counts.get('qualified', 0), 1),
            'proposal_to_negotiation': status_counts.get('negotiation', 0) / max(status_counts.get('proposal', 0), 1),
            'negotiation_to_closed': (status_counts.get('closed_won', 0) + status_counts.get('closed_lost', 0)) / max(status_counts.get('negotiation', 0), 1),
            'overall_win_rate': status_counts.get('closed_won', 0) / max(total_new, 1)
        }
