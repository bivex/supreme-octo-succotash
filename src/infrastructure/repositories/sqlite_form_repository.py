# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:32
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""SQLite form repository implementation."""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ...domain.entities.form import Lead, FormSubmission, LeadScore, FormValidationRule, LeadStatus, LeadSource
from ...domain.repositories.form_repository import FormRepository


class SQLiteFormRepository(FormRepository):
    """SQLite implementation of FormRepository for stress testing."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._connection = None
        self._initialize_db()

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create form_submissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS form_submissions (
                id TEXT PRIMARY KEY,
                form_id TEXT NOT NULL,
                campaign_id TEXT,
                click_id TEXT,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                referrer TEXT,
                form_data TEXT NOT NULL,  -- JSON string
                validation_errors TEXT NOT NULL,  -- JSON string
                is_valid INTEGER NOT NULL,
                is_duplicate INTEGER NOT NULL,
                duplicate_of TEXT,
                submitted_at TEXT NOT NULL,
                processed_at TEXT
            )
        """)

        # Create leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                company TEXT,
                job_title TEXT,
                source TEXT NOT NULL,
                source_campaign TEXT,
                status TEXT NOT NULL,
                tags TEXT NOT NULL,  -- JSON string
                custom_fields TEXT NOT NULL,  -- JSON string
                first_submission_id TEXT NOT NULL,
                last_submission_id TEXT NOT NULL,
                submission_count INTEGER NOT NULL,
                converted_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create lead_scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_scores (
                lead_id TEXT PRIMARY KEY,
                total_score INTEGER NOT NULL,
                scores TEXT NOT NULL,  -- JSON string
                grade TEXT NOT NULL,
                is_hot_lead INTEGER NOT NULL,
                reasons TEXT NOT NULL,  -- JSON string
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)

        # Create validation_rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_rules (
                id TEXT PRIMARY KEY,
                form_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_value TEXT,
                error_message TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_form ON form_submissions(form_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_ip ON form_submissions(ip_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_email ON form_submissions(form_data)")  # JSON index workaround
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_date ON form_submissions(submitted_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_lead ON lead_scores(lead_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_form ON validation_rules(form_id)")

        conn.commit()

    def save_form_submission(self, submission: FormSubmission) -> None:
        """Save form submission."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO form_submissions
            (id, form_id, campaign_id, click_id, ip_address, user_agent, referrer,
             form_data, validation_errors, is_valid, is_duplicate, duplicate_of,
             submitted_at, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission.id,
            submission.form_id,
            submission.campaign_id,
            submission.click_id,
            submission.ip_address,
            submission.user_agent,
            submission.referrer,
            json.dumps(submission.form_data),
            json.dumps(submission.validation_errors),
            1 if submission.is_valid else 0,
            1 if submission.is_duplicate else 0,
            submission.duplicate_of,
            submission.submitted_at.isoformat(),
            submission.processed_at.isoformat() if submission.processed_at else None
        ))

        conn.commit()

    def get_form_submission(self, submission_id: str) -> Optional[FormSubmission]:
        """Get form submission by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM form_submissions WHERE id = ?", (submission_id,))

        row = cursor.fetchone()
        return self._row_to_submission(row) if row else None

    def get_submissions_by_form(self, form_id: str, limit: int = 100) -> List[FormSubmission]:
        """Get submissions for a specific form."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM form_submissions
            WHERE form_id = ?
            ORDER BY submitted_at DESC
            LIMIT ?
        """, (form_id, limit))

        return [self._row_to_submission(row) for row in cursor.fetchall()]

    def get_submissions_by_ip(self, ip_address: str, time_window_minutes: int = 60) -> List[FormSubmission]:
        """Get submissions from IP address within time window."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_time = (datetime.now() - timedelta(minutes=time_window_minutes)).isoformat()

        cursor.execute("""
            SELECT * FROM form_submissions
            WHERE ip_address = ? AND submitted_at >= ?
            ORDER BY submitted_at DESC
        """, (ip_address, cutoff_time))

        return [self._row_to_submission(row) for row in cursor.fetchall()]

    def save_lead(self, lead: Lead) -> None:
        """Save lead data."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO leads
            (id, email, first_name, last_name, phone, company, job_title, source,
             source_campaign, status, tags, custom_fields, first_submission_id,
             last_submission_id, submission_count, converted_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.id,
            lead.email,
            lead.first_name,
            lead.last_name,
            lead.phone,
            lead.company,
            lead.job_title,
            lead.source.value,
            lead.source_campaign,
            lead.status.value,
            json.dumps(lead.tags),
            json.dumps(lead.custom_fields),
            lead.first_submission_id,
            lead.last_submission_id,
            lead.submission_count,
            lead.converted_at.isoformat() if lead.converted_at else None,
            lead.created_at.isoformat(),
            lead.updated_at.isoformat()
        ))

        conn.commit()

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))

        row = cursor.fetchone()
        return self._row_to_lead(row) if row else None

    def get_lead_by_email(self, email: str) -> Optional[Lead]:
        """Get lead by email address."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM leads WHERE email = ?", (email.lower().strip(),))

        row = cursor.fetchone()
        return self._row_to_lead(row) if row else None

    def get_leads_by_status(self, status: LeadStatus, limit: int = 100) -> List[Lead]:
        """Get leads by status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM leads
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (status.value, limit))

        return [self._row_to_lead(row) for row in cursor.fetchall()]

    def get_leads_by_source(self, source: LeadSource, limit: int = 100) -> List[Lead]:
        """Get leads by source."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM leads
            WHERE source = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (source.value, limit))

        return [self._row_to_lead(row) for row in cursor.fetchall()]

    def get_hot_leads(self, score_threshold: int = 70, limit: int = 100) -> List[Lead]:
        """Get hot leads above score threshold."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT l.*, s.total_score
            FROM leads l
            LEFT JOIN lead_scores s ON l.id = s.lead_id
            WHERE s.total_score >= ?
            ORDER BY s.total_score DESC
            LIMIT ?
        """, (score_threshold, limit))

        return [self._row_to_lead(row) for row in cursor.fetchall()]

    def update_lead_status(self, lead_id: str, status: LeadStatus) -> None:
        """Update lead status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE leads
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status.value, datetime.now().isoformat(), lead_id))

        conn.commit()

    def save_lead_score(self, score: LeadScore) -> None:
        """Save lead score."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO lead_scores
            (lead_id, total_score, scores, grade, is_hot_lead, reasons, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score.lead_id,
            score.total_score,
            json.dumps(score.scores),
            score.grade,
            1 if score.is_hot_lead else 0,
            json.dumps(score.reasons),
            score.created_at.isoformat(),
            score.updated_at.isoformat()
        ))

        conn.commit()

    def get_lead_score(self, lead_id: str) -> Optional[LeadScore]:
        """Get lead score by lead ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM lead_scores WHERE lead_id = ?", (lead_id,))

        row = cursor.fetchone()
        return self._row_to_lead_score(row) if row else None

    def save_validation_rule(self, rule: FormValidationRule) -> None:
        """Save form validation rule."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO validation_rules
            (id, form_id, field_name, rule_type, rule_value, error_message, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule.id,
            "default_form",  # Simplified - could be parameterized
            rule.field_name,
            rule.rule_type,
            rule.rule_value,
            rule.error_message,
            1 if rule.is_active else 0,
            rule.created_at.isoformat()
        ))

        conn.commit()

    def get_validation_rules(self, form_id: str) -> List[FormValidationRule]:
        """Get validation rules for a form."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM validation_rules WHERE form_id = ? AND is_active = 1", (form_id,))

        return [self._row_to_validation_rule(row) for row in cursor.fetchall()]

    def get_form_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get form submission analytics for date range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get submission metrics
        cursor.execute("""
            SELECT
                COUNT(*) as total_submissions,
                SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) as valid_submissions,
                SUM(CASE WHEN is_duplicate = 1 THEN 1 ELSE 0 END) as duplicate_submissions
            FROM form_submissions
            WHERE submitted_at >= ? AND submitted_at <= ?
        """, (start_date.isoformat(), end_date.isoformat()))

        sub_row = cursor.fetchone()

        # Get lead conversion metrics
        cursor.execute("""
            SELECT
                COUNT(*) as total_leads,
                SUM(CASE WHEN converted_at IS NOT NULL THEN 1 ELSE 0 END) as converted_leads
            FROM leads
            WHERE created_at >= ? AND created_at <= ?
        """, (start_date.isoformat(), end_date.isoformat()))

        lead_row = cursor.fetchone()

        # Get source distribution
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM leads
            WHERE created_at >= ? AND created_at <= ?
            GROUP BY source
        """, (start_date.isoformat(), end_date.isoformat()))

        source_distribution = {row[0]: row[1] for row in cursor.fetchall()}

        total_submissions = sub_row[0] or 0
        valid_submissions = sub_row[1] or 0
        duplicate_submissions = sub_row[2] or 0
        total_leads = lead_row[0] or 0
        converted_leads = lead_row[1] or 0

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
            'source_distribution': source_distribution
        }

    def get_lead_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get lead conversion funnel analytics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get status counts
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM leads
            WHERE created_at >= ? AND created_at <= ?
            GROUP BY status
        """, (start_date.isoformat(), end_date.isoformat()))

        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

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
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_time = (datetime.now() - timedelta(hours=time_window_hours)).isoformat()
        email = form_data.get('email', '').lower().strip()

        if not email:
            return False

        # Check for existing submissions with same email and IP within time window
        cursor.execute("""
            SELECT COUNT(*) FROM form_submissions
            WHERE ip_address = ? AND submitted_at >= ?
            AND json_extract(form_data, '$.email') = ?
        """, (ip_address, cutoff_time, email))

        count = cursor.fetchone()[0]
        return count > 0

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

    def _row_to_submission(self, row) -> FormSubmission:
        """Convert database row to FormSubmission entity."""
        import json

        return FormSubmission(
            id=row["id"],
            form_id=row["form_id"],
            campaign_id=row["campaign_id"],
            click_id=row["click_id"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            referrer=row["referrer"],
            form_data=json.loads(row["form_data"]),
            validation_errors=json.loads(row["validation_errors"]),
            is_valid=bool(row["is_valid"]),
            is_duplicate=bool(row["is_duplicate"]),
            duplicate_of=row["duplicate_of"],
            submitted_at=datetime.fromisoformat(row["submitted_at"]),
            processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None
        )

    def _row_to_lead(self, row) -> Lead:
        """Convert database row to Lead entity."""
        import json

        # Get associated lead score
        score = self.get_lead_score(row["id"])

        return Lead(
            id=row["id"],
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            phone=row["phone"],
            company=row["company"],
            job_title=row["job_title"],
            source=LeadSource(row["source"]),
            source_campaign=row["source_campaign"],
            status=LeadStatus(row["status"]),
            lead_score=score,
            tags=json.loads(row["tags"]),
            custom_fields=json.loads(row["custom_fields"]),
            first_submission_id=row["first_submission_id"],
            last_submission_id=row["last_submission_id"],
            submission_count=row["submission_count"],
            converted_at=datetime.fromisoformat(row["converted_at"]) if row["converted_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

    def _row_to_lead_score(self, row) -> LeadScore:
        """Convert database row to LeadScore entity."""
        import json

        return LeadScore(
            lead_id=row["lead_id"],
            total_score=row["total_score"],
            scores=json.loads(row["scores"]),
            grade=row["grade"],
            is_hot_lead=bool(row["is_hot_lead"]),
            reasons=json.loads(row["reasons"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

    def _row_to_validation_rule(self, row) -> FormValidationRule:
        """Convert database row to FormValidationRule entity."""
        return FormValidationRule(
            id=row["id"],
            field_name=row["field_name"],
            rule_type=row["rule_type"],
            rule_value=row["rule_value"],
            error_message=row["error_message"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"])
        )
