"""Form processing domain service."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import re

from ...entities.form import Lead, FormSubmission, LeadScore, FormValidationRule, LeadStatus, LeadSource


class FormService:
    """Domain service for form processing, validation, and lead management."""

    def __init__(self):
        self._validation_rules = self._create_default_validation_rules()

    def validate_form_submission(self, form_data: Dict,
                                validation_rules: List[FormValidationRule]) -> Tuple[bool, List[str]]:
        """
        Validate form submission data against validation rules.

        Args:
            form_data: Form field data
            validation_rules: List of validation rules

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for rule in validation_rules:
            if rule.field_name not in form_data:
                if rule.rule_type == 'required':
                    errors.append(f"{rule.field_name}: {rule.error_message}")
                continue

            field_value = form_data[rule.field_name]
            error = rule.validate(field_value)
            if error:
                errors.append(error)

        # Additional business logic validations
        if 'email' in form_data and 'confirm_email' in form_data:
            if form_data['email'] != form_data['confirm_email']:
                errors.append("Email addresses do not match")

        if 'phone' in form_data:
            phone = form_data['phone']
            if not self._is_valid_phone_format(phone):
                errors.append("Invalid phone number format")

        return len(errors) == 0, errors

    def process_form_submission(self, form_data: Dict, campaign_id: Optional[str] = None,
                              click_id: Optional[str] = None, ip_address: str = "",
                              user_agent: str = "") -> FormSubmission:
        """
        Process form submission and create FormSubmission entity.

        Args:
            form_data: Submitted form data
            campaign_id: Associated campaign ID
            click_id: Associated click ID
            ip_address: Submitter IP address
            user_agent: Submitter user agent

        Returns:
            FormSubmission entity
        """
        # Validate form data
        is_valid, validation_errors = self.validate_form_submission(form_data, self._validation_rules)

        # Check for duplicates
        submission_hash = self._generate_submission_hash(form_data)
        is_duplicate = self._check_duplicate_submission(submission_hash, ip_address)

        # Create submission entity
        submission = FormSubmission(
            id=f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(submission_hash) % 10000}",
            form_id="default_form",  # Could be made configurable
            campaign_id=campaign_id,
            click_id=click_id,
            ip_address=ip_address,
            user_agent=user_agent,
            form_data=form_data,
            validation_errors=validation_errors,
            is_valid=is_valid,
            is_duplicate=is_duplicate,
            duplicate_of=None,  # Would need duplicate detection logic
            submitted_at=datetime.now(),
            processed_at=datetime.now()
        )

        return submission

    def create_or_update_lead(self, submission: FormSubmission,
                             existing_leads: List[Lead]) -> Lead:
        """
        Create new lead or update existing one based on form submission.

        Args:
            submission: Form submission data
            existing_leads: List of existing leads to check for duplicates

        Returns:
            Lead entity (new or updated)
        """
        # Extract lead information from form data
        email = submission.form_data.get('email', '').strip().lower()
        first_name = submission.form_data.get('first_name', '').strip()
        last_name = submission.form_data.get('last_name', '').strip()
        phone = submission.form_data.get('phone', '').strip()
        company = submission.form_data.get('company', '').strip()

        # Check for existing lead by email
        existing_lead = None
        for lead in existing_leads:
            if lead.email == email:
                existing_lead = lead
                break

        if existing_lead:
            # Update existing lead
            updated_lead = Lead(
                id=existing_lead.id,
                email=email,
                first_name=first_name or existing_lead.first_name,
                last_name=last_name or existing_lead.last_name,
                phone=phone or existing_lead.phone,
                company=company or existing_lead.company,
                job_title=submission.form_data.get('job_title') or existing_lead.job_title,
                source=self._determine_lead_source(submission),
                source_campaign=submission.campaign_id or existing_lead.source_campaign,
                status=existing_lead.status,  # Would be updated by CRM integration
                lead_score=existing_lead.lead_score,
                tags=existing_lead.tags,
                custom_fields={**existing_lead.custom_fields, **submission.form_data},
                first_submission_id=existing_lead.first_submission_id,
                last_submission_id=submission.id,
                submission_count=existing_lead.submission_count + 1,
                converted_at=existing_lead.converted_at,
                created_at=existing_lead.created_at,
                updated_at=datetime.now()
            )
            return updated_lead
        else:
            # Create new lead
            lead_score = self.score_lead(submission.form_data)

            new_lead = Lead(
                id=f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(email) % 10000}",
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                company=company,
                job_title=submission.form_data.get('job_title'),
                source=self._determine_lead_source(submission),
                source_campaign=submission.campaign_id,
                status=LeadStatus.NEW,
                lead_score=lead_score,
                tags=self._generate_lead_tags(submission.form_data),
                custom_fields=submission.form_data,
                first_submission_id=submission.id,
                last_submission_id=submission.id,
                submission_count=1,
                converted_at=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            return new_lead

    def score_lead(self, form_data: Dict) -> LeadScore:
        """
        Score lead based on form data quality and engagement signals.

        Args:
            form_data: Lead form data

        Returns:
            LeadScore entity
        """
        scores = {}
        total_score = 0

        # Email quality (max 25 points)
        email = form_data.get('email', '')
        if email:
            scores['email_quality'] = 25
            total_score += 25
        else:
            scores['email_quality'] = 0

        # Contact information completeness (max 20 points)
        contact_score = 0
        if form_data.get('phone'):
            contact_score += 10
        if form_data.get('company'):
            contact_score += 10
        scores['contact_info'] = contact_score
        total_score += contact_score

        # Job title and company (max 20 points)
        professional_score = 0
        if form_data.get('job_title'):
            professional_score += 10
        if form_data.get('company'):
            professional_score += 10
        scores['professional_info'] = professional_score
        total_score += professional_score

        # Form engagement (max 15 points)
        engagement_score = 0
        if len(form_data) > 5:  # More fields filled
            engagement_score += 10
        if form_data.get('comments') and len(form_data.get('comments', '')) > 10:
            engagement_score += 5
        scores['engagement'] = engagement_score
        total_score += engagement_score

        # Determine grade and if hot lead
        grade, is_hot = self._calculate_lead_grade(total_score)

        reasons = []
        if total_score >= 70:
            reasons.append("High-quality contact information")
        if engagement_score >= 10:
            reasons.append("High engagement with form")
        if professional_score >= 15:
            reasons.append("Professional background provided")

        return LeadScore(
            lead_id="",  # Will be set by caller
            total_score=total_score,
            scores=scores,
            grade=grade,
            is_hot_lead=is_hot,
            reasons=reasons,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def check_spam_indicators(self, submission: FormSubmission) -> Tuple[bool, List[str]]:
        """
        Check form submission for spam indicators.

        Args:
            submission: Form submission to check

        Returns:
            Tuple of (is_spam, reasons)
        """
        spam_indicators = []
        is_spam = False

        # Check for suspicious patterns
        email = submission.form_data.get('email', '')

        # Common spam domains
        spam_domains = ['10minutemail.com', 'guerrillamail.com', 'mailinator.com']
        if any(domain in email.lower() for domain in spam_domains):
            spam_indicators.append("Suspicious email domain")
            is_spam = True

        # Check for too many submissions from same IP (would need rate limiting)
        # This is simplified - in real implementation would check database
        if submission.ip_address in ['127.0.0.1', 'localhost']:
            # Allow localhost for testing
            pass
        else:
            # Would check submission frequency from IP
            pass

        # Check for suspicious content
        suspicious_words = ['viagra', 'casino', 'lottery', 'winner']
        text_fields = ['comments', 'message', 'notes']
        for field in text_fields:
            content = submission.form_data.get(field, '').lower()
            if any(word in content for word in suspicious_words):
                spam_indicators.append(f"Suspicious content in {field}")
                is_spam = True

        return is_spam, spam_indicators

    def _create_default_validation_rules(self) -> List[FormValidationRule]:
        """Create default form validation rules."""
        return [
            FormValidationRule(
                id="email_required",
                field_name="email",
                rule_type="required",
                rule_value=None,
                error_message="Email is required",
                is_active=True,
                created_at=datetime.now()
            ),
            FormValidationRule(
                id="email_format",
                field_name="email",
                rule_type="email",
                rule_value=None,
                error_message="Invalid email format",
                is_active=True,
                created_at=datetime.now()
            ),
            FormValidationRule(
                id="first_name_required",
                field_name="first_name",
                rule_type="required",
                rule_value=None,
                error_message="First name is required",
                is_active=True,
                created_at=datetime.now()
            ),
            FormValidationRule(
                id="phone_format",
                field_name="phone",
                rule_type="phone",
                rule_value=None,
                error_message="Invalid phone number format",
                is_active=True,
                created_at=datetime.now()
            )
        ]

    def _is_valid_phone_format(self, phone: str) -> bool:
        """Check if phone number has valid format."""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)

        # Check length (US format or international)
        if len(digits_only) < 10 or len(digits_only) > 15:
            return False

        # Check if starts with country code or area code
        if len(digits_only) == 10:
            return digits_only[0] in '23456789'  # Valid US area code starts
        elif len(digits_only) > 10:
            return digits_only.startswith(('1', '+1')) or len(digits_only) >= 11

        return True

    def _generate_submission_hash(self, form_data: Dict) -> str:
        """Generate hash for duplicate detection."""
        # Create hash from key form fields
        key_data = {
            'email': form_data.get('email', '').strip().lower(),
            'first_name': form_data.get('first_name', '').strip().lower(),
            'last_name': form_data.get('last_name', '').strip().lower(),
            'phone': form_data.get('phone', '').strip(),
        }

        # Sort keys for consistent hashing
        hash_string = str(sorted(key_data.items()))
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _check_duplicate_submission(self, submission_hash: str, ip_address: str) -> bool:
        """Check if submission is duplicate (simplified implementation)."""
        # In real implementation, would check database for recent submissions
        # with same hash and different IP, or same IP submitting too frequently
        return False  # Simplified - always allow

    def _determine_lead_source(self, submission: FormSubmission) -> LeadSource:
        """Determine lead source from submission context."""
        if submission.campaign_id:
            return LeadSource.AFFILIATE
        elif 'google' in submission.user_agent.lower():
            return LeadSource.ORGANIC
        elif 'facebook' in submission.user_agent.lower():
            return LeadSource.SOCIAL
        else:
            return LeadSource.DIRECT

    def _calculate_lead_grade(self, total_score: int) -> Tuple[str, bool]:
        """Calculate lead grade and hot lead status."""
        if total_score >= 80:
            return "A", True
        elif total_score >= 70:
            return "B", True
        elif total_score >= 60:
            return "C", False
        elif total_score >= 50:
            return "D", False
        else:
            return "F", False

    def _generate_lead_tags(self, form_data: Dict) -> List[str]:
        """Generate tags for lead based on form data."""
        tags = []

        if form_data.get('company'):
            tags.append('b2b')

        if form_data.get('job_title'):
            job_title = form_data['job_title'].lower()
            if any(keyword in job_title for keyword in ['ceo', 'cto', 'cfo', 'vp', 'director']):
                tags.append('executive')
            elif any(keyword in job_title for keyword in ['manager', 'lead', 'senior']):
                tags.append('manager')

        if form_data.get('interests'):
            interests = form_data['interests']
            if isinstance(interests, list):
                tags.extend(interests[:3])  # Max 3 interest tags

        return tags
