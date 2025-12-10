"""Form processing handler."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from ...domain.repositories.form_repository import FormRepository
from ...domain.services.form.form_service import FormService


class FormHandler:
    """Handler for form processing operations."""

    def __init__(self, form_repository: FormRepository):
        self._form_repository = form_repository
        self._form_service = FormService()

    def submit_form(self, form_data: Dict[str, Any], campaign_id: Optional[str] = None,
                   click_id: Optional[str] = None, ip_address: str = "",
                   user_agent: str = "") -> Dict[str, Any]:
        """
        Process form submission.

        Args:
            form_data: Submitted form data
            campaign_id: Associated campaign ID
            click_id: Associated click ID
            ip_address: Submitter IP address
            user_agent: Submitter user agent

        Returns:
            Dict containing submission result
        """
        try:
            logger.info("Processing form submission")

            # Check for duplicates
            is_duplicate = self._form_repository.check_duplicate_submission(
                form_data, ip_address, time_window_hours=24
            )

            if is_duplicate:
                logger.warning(f"Duplicate form submission detected from IP: {ip_address}")
                return {
                    "status": "duplicate",
                    "message": "Form submission appears to be a duplicate",
                    "lead_id": None
                }

            # Process form submission
            submission = self._form_service.process_form_submission(
                form_data, campaign_id, click_id, ip_address, user_agent
            )

            # Check for spam
            is_spam, spam_reasons = self._form_service.check_spam_indicators(submission)

            if is_spam:
                logger.warning(f"Spam form submission detected: {spam_reasons}")
                return {
                    "status": "spam",
                    "message": "Form submission flagged as spam",
                    "reasons": spam_reasons,
                    "lead_id": None
                }

            # Save submission
            self._form_repository.save_form_submission(submission)

            # Create or update lead
            existing_leads = []
            if 'email' in form_data:
                # Try to find existing leads by email
                existing_lead = self._form_repository.get_lead_by_email(form_data['email'])
                if existing_lead:
                    existing_leads = [existing_lead]

            lead = self._form_service.create_or_update_lead(submission, existing_leads)

            # Save lead
            self._form_repository.save_lead(lead)

            # Save lead score if it exists
            if lead.lead_score:
                self._form_repository.save_lead_score(lead.lead_score)

            result = {
                "status": "success",
                "lead_id": lead.id,
                "message": "Form submitted successfully",
                "lead_info": {
                    "email": lead.email,
                    "status": lead.status.value,
                    "score": lead.lead_score.total_score if lead.lead_score else 0,
                    "is_hot_lead": lead.lead_score.is_hot_lead if lead.lead_score else False
                },
                "validation": {
                    "is_valid": submission.is_valid,
                    "errors": submission.validation_errors if not submission.is_valid else []
                }
            }

            logger.info(f"Form submission processed successfully. Lead ID: {lead.id}")

            return result

        except Exception as e:
            logger.error(f"Error processing form submission: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to process form submission: {str(e)}",
                "lead_id": None
            }

    def get_lead_details(self, lead_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a lead.

        Args:
            lead_id: Lead identifier

        Returns:
            Dict containing lead details
        """
        try:
            logger.info(f"Getting details for lead: {lead_id}")

            lead = self._form_repository.get_lead(lead_id)

            if not lead:
                return {
                    "status": "not_found",
                    "message": f"Lead {lead_id} not found",
                    "lead_id": lead_id
                }

            result = {
                "status": "success",
                "lead_id": lead.id,
                "contact_info": {
                    "email": lead.email,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "phone": lead.phone,
                    "company": lead.company,
                    "job_title": lead.job_title
                },
                "lead_info": {
                    "source": lead.source.value,
                    "source_campaign": lead.source_campaign,
                    "status": lead.status.value,
                    "lead_score": lead.lead_score.total_score if lead.lead_score else 0,
                    "grade": lead.lead_score.grade if lead.lead_score else "Unknown",
                    "is_hot_lead": lead.lead_score.is_hot_lead if lead.lead_score else False,
                    "is_qualified": lead.lead_score.is_qualified if lead.lead_score else False,
                    "tags": lead.tags,
                    "submission_count": lead.submission_count
                },
                "timeline": {
                    "first_submission": lead.first_submission_id,
                    "last_submission": lead.last_submission_id,
                    "converted_at": lead.converted_at.isoformat() if lead.converted_at else None,
                    "created_at": lead.created_at.isoformat(),
                    "updated_at": lead.updated_at.isoformat(),
                    "days_since_creation": lead.days_since_creation
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error getting lead details for {lead_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get lead details: {str(e)}",
                "lead_id": lead_id
            }

    def get_form_analytics(self, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get form submission analytics.

        Args:
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)

        Returns:
            Dict containing form analytics data
        """
        try:
            logger.info("Generating form analytics data")

            # Use provided dates or default to last 30 days
            if not start_date:
                start_date = datetime.now().replace(day=datetime.now().day - 30)
            if not end_date:
                end_date = datetime.now()

            # Get analytics from repository
            analytics = self._form_repository.get_form_analytics(start_date, end_date)

            # Get lead conversion funnel
            funnel = self._form_repository.get_lead_conversion_funnel(start_date, end_date)

            result = {
                "status": "success",
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "submission_metrics": analytics.get('submission_metrics', {}),
                "lead_metrics": analytics.get('lead_metrics', {}),
                "source_distribution": analytics.get('source_distribution', {}),
                "conversion_funnel": funnel.get('funnel_stages', {}),
                "conversion_rates": funnel.get('conversion_rates', {})
            }

            logger.info(f"Form analytics generated for {result['date_range']['start']} to {result['date_range']['end']}")

            return result

        except Exception as e:
            logger.error(f"Error generating form analytics: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate form analytics: {str(e)}",
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }

    def get_hot_leads(self, score_threshold: int = 70, limit: int = 50) -> Dict[str, Any]:
        """
        Get hot leads above score threshold.

        Args:
            score_threshold: Minimum score threshold
            limit: Maximum number of leads to return

        Returns:
            Dict containing hot leads data
        """
        try:
            logger.info(f"Getting hot leads with score >= {score_threshold}")

            hot_leads = self._form_repository.get_hot_leads(score_threshold, limit)

            lead_data = []
            for lead in hot_leads:
                lead_data.append({
                    "lead_id": lead.id,
                    "email": lead.email,
                    "full_name": lead.full_name,
                    "company": lead.company,
                    "job_title": lead.job_title,
                    "score": lead.lead_score.total_score if lead.lead_score else 0,
                    "grade": lead.lead_score.grade if lead.lead_score else "Unknown",
                    "status": lead.status.value,
                    "source": lead.source.value,
                    "tags": lead.tags,
                    "created_at": lead.created_at.isoformat(),
                    "days_since_creation": lead.days_since_creation
                })

            result = {
                "status": "success",
                "hot_leads": lead_data,
                "total_count": len(lead_data),
                "score_threshold": score_threshold
            }

            return result

        except Exception as e:
            logger.error(f"Error getting hot leads: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get hot leads: {str(e)}",
                "hot_leads": [],
                "total_count": 0
            }
