"""PostgreSQL form repository implementation."""

import psycopg2
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ...domain.entities.form import Lead, FormSubmission, LeadScore, FormValidationRule, LeadStatus, LeadSource
from ...domain.repositories.form_repository import FormRepository


class PostgresFormRepository(FormRepository):
    """PostgreSQL implementation of FormRepository."""

    def __init__(self, container):
        self._container = container
        self._connection = None
        self._db_initialized = False

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = self._container.get_db_connection()
        if not self._db_initialized:
            self._initialize_db()
            self._db_initialized = True
        return self._connection

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            # Enable UUID extension for potential future use
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

            # Create form_submissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_submissions (
                    id TEXT PRIMARY KEY,
                    form_id TEXT NOT NULL,
                    campaign_id TEXT,
                    click_id TEXT,
                    ip_address INET NOT NULL,
                    user_agent TEXT,
                    referrer TEXT,
                    form_data JSONB NOT NULL,
                    validation_errors JSONB DEFAULT '[]'::jsonb,
                    is_valid BOOLEAN NOT NULL DEFAULT false,
                    is_duplicate BOOLEAN NOT NULL DEFAULT false,
                    duplicate_of TEXT,
                    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
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
                    status TEXT NOT NULL DEFAULT 'new',
                    tags JSONB DEFAULT '[]'::jsonb,
                    custom_fields JSONB DEFAULT '{}'::jsonb,
                    first_submission_id TEXT NOT NULL,
                    last_submission_id TEXT NOT NULL,
                    submission_count INTEGER NOT NULL DEFAULT 1,
                    converted_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create lead_scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lead_scores (
                    lead_id TEXT PRIMARY KEY,
                    total_score INTEGER NOT NULL DEFAULT 0,
                    scores JSONB DEFAULT '{}'::jsonb,
                    grade TEXT NOT NULL DEFAULT 'F',
                    is_hot_lead BOOLEAN NOT NULL DEFAULT false,
                    reasons JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
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
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_form ON form_submissions(form_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_ip ON form_submissions(ip_address)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_email ON form_submissions((form_data->>'email'))")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_date ON form_submissions(submitted_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_lead ON lead_scores(lead_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_form ON validation_rules(form_id)")

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def save_form_submission(self, submission: FormSubmission) -> None:
        """Save form submission."""
        import json
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO form_submissions
                (id, form_id, campaign_id, click_id, ip_address, user_agent, referrer,
                 form_data, validation_errors, is_valid, is_duplicate, duplicate_of,
                 submitted_at, processed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    processed_at = EXCLUDED.processed_at
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
                submission.is_valid,
                submission.is_duplicate,
                submission.duplicate_of,
                submission.submitted_at,
                submission.processed_at
            ))

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_form_submission(self, submission_id: str) -> Optional[FormSubmission]:
        """Get form submission by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM form_submissions WHERE id = %s", (submission_id,))

            row = cursor.fetchone()

            return self._row_to_submission(row) if row else None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_submissions_by_form(self, form_id: str, limit: int = 100) -> List[FormSubmission]:
        """Get submissions for a specific form."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM form_submissions
                WHERE form_id = %s
                ORDER BY submitted_at DESC
                LIMIT %s
            """, (form_id, limit))

            rows = cursor.fetchall()

            return [self._row_to_submission(row) for row in rows]
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_submissions_by_ip(self, ip_address: str, time_window_minutes: int = 60) -> List[FormSubmission]:
        """Get submissions from IP address within time window."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

            cursor.execute("""
                SELECT * FROM form_submissions
                WHERE ip_address = %s AND submitted_at >= %s
                ORDER BY submitted_at DESC
            """, (ip_address, cutoff_time))

            rows = cursor.fetchall()

            return [self._row_to_submission(row) for row in rows]
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def save_lead(self, lead: Lead) -> None:
        """Save lead data."""
        import json
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO leads
                (id, email, first_name, last_name, phone, company, job_title, source,
                 source_campaign, status, tags, custom_fields, first_submission_id,
                 last_submission_id, submission_count, converted_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    phone = EXCLUDED.phone,
                    company = EXCLUDED.company,
                    job_title = EXCLUDED.job_title,
                    source = EXCLUDED.source,
                    source_campaign = EXCLUDED.source_campaign,
                    status = EXCLUDED.status,
                    tags = EXCLUDED.tags,
                    custom_fields = EXCLUDED.custom_fields,
                    last_submission_id = EXCLUDED.last_submission_id,
                    submission_count = EXCLUDED.submission_count,
                    converted_at = EXCLUDED.converted_at,
                    updated_at = CURRENT_TIMESTAMP
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
                lead.converted_at,
                lead.created_at,
                lead.updated_at
            ))

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))

            row = cursor.fetchone()

            return self._row_to_lead(row) if row else None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_lead_by_email(self, email: str) -> Optional[Lead]:
        """Get lead by email address."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM leads WHERE email = %s", (email.lower().strip(),))

            row = cursor.fetchone()

            return self._row_to_lead(row) if row else None
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_leads_by_status(self, status: LeadStatus, limit: int = 100) -> List[Lead]:
        """Get leads by status."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM leads
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (status.value, limit))

            rows = cursor.fetchall()

            return [self._row_to_lead(row) for row in rows]
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_leads_by_source(self, source: LeadSource, limit: int = 100) -> List[Lead]:
        """Get leads by source."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM leads
            WHERE source = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (source.value, limit))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_lead(row) for row in rows]

    def get_hot_leads(self, score_threshold: int = 70, limit: int = 100) -> List[Lead]:
        """Get hot leads above score threshold."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT l.*
            FROM leads l
            LEFT JOIN lead_scores s ON l.id = s.lead_id
            WHERE s.total_score >= %s
            ORDER BY s.total_score DESC
            LIMIT %s
        """, (score_threshold, limit))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_lead(row) for row in rows]

    def update_lead_status(self, lead_id: str, status: LeadStatus) -> None:
        """Update lead status."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE leads
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status.value, lead_id))

        conn.commit()
        cursor.close()
        conn.close()

    def save_lead_score(self, score: LeadScore) -> None:
        """Save lead score."""
        import json
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO lead_scores
            (lead_id, total_score, scores, grade, is_hot_lead, reasons, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (lead_id) DO UPDATE SET
                total_score = EXCLUDED.total_score,
                scores = EXCLUDED.scores,
                grade = EXCLUDED.grade,
                is_hot_lead = EXCLUDED.is_hot_lead,
                reasons = EXCLUDED.reasons,
                updated_at = CURRENT_TIMESTAMP
        """, (
            score.lead_id,
            score.total_score,
            json.dumps(score.scores),
            score.grade,
            score.is_hot_lead,
            json.dumps(score.reasons),
            score.created_at,
            score.updated_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_lead_score(self, lead_id: str) -> Optional[LeadScore]:
        """Get lead score by lead ID."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM lead_scores WHERE lead_id = %s", (lead_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return self._row_to_lead_score(row) if row else None

    def save_validation_rule(self, rule: FormValidationRule) -> None:
        """Save form validation rule."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO validation_rules
            (id, form_id, field_name, rule_type, rule_value, error_message, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                field_name = EXCLUDED.field_name,
                rule_type = EXCLUDED.rule_type,
                rule_value = EXCLUDED.rule_value,
                error_message = EXCLUDED.error_message,
                is_active = EXCLUDED.is_active
        """, (
            rule.id,
            "default_form",  # Simplified - could be parameterized
            rule.field_name,
            rule.rule_type,
            rule.rule_value,
            rule.error_message,
            rule.is_active,
            rule.created_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_validation_rules(self, form_id: str) -> List[FormValidationRule]:
        """Get validation rules for a form."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM validation_rules WHERE form_id = %s AND is_active = true", (form_id,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_validation_rule(row) for row in rows]

    def get_form_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get form submission analytics for date range."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        # Get submission metrics
        cursor.execute("""
            SELECT
                COUNT(*) as total_submissions,
                SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) as valid_submissions,
                SUM(CASE WHEN is_duplicate THEN 1 ELSE 0 END) as duplicate_submissions
            FROM form_submissions
            WHERE submitted_at >= %s AND submitted_at <= %s
        """, (start_date, end_date))

        sub_row = cursor.fetchone()

        # Get lead conversion metrics
        cursor.execute("""
            SELECT
                COUNT(*) as total_leads,
                SUM(CASE WHEN converted_at IS NOT NULL THEN 1 ELSE 0 END) as converted_leads
            FROM leads
            WHERE created_at >= %s AND created_at <= %s
        """, (start_date, end_date))

        lead_row = cursor.fetchone()

        # Get source distribution
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM leads
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY source
        """, (start_date, end_date))

        source_rows = cursor.fetchall()
        source_distribution = {row[0]: row[1] for row in source_rows}

        cursor.close()
        conn.close()

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
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        # Get status counts
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM leads
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY status
        """, (start_date, end_date))

        status_rows = cursor.fetchall()
        status_counts = {row[0]: row[1] for row in status_rows}

        cursor.close()
        conn.close()

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
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        email = form_data.get('email', '').lower().strip()

        if not email:
            cursor.close()
            conn.close()
            return False

        # Check for existing submissions with same email and IP within time window
        cursor.execute("""
            SELECT COUNT(*) FROM form_submissions
            WHERE ip_address = %s AND submitted_at >= %s
            AND form_data->>'email' = %s
        """, (ip_address, cutoff_time, email))

        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

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
            id=row[0],
            form_id=row[1],
            campaign_id=row[2],
            click_id=row[3],
            ip_address=row[4],
            user_agent=row[5],
            referrer=row[6],
            form_data=json.loads(row[7]) if row[7] else {},
            validation_errors=json.loads(row[8]) if row[8] else [],
            is_valid=row[9],
            is_duplicate=row[10],
            duplicate_of=row[11],
            submitted_at=row[12],
            processed_at=row[13]
        )

    def _row_to_lead(self, row) -> Lead:
        """Convert database row to Lead entity."""
        import json

        # Get associated lead score
        score = self.get_lead_score(row[0])

        return Lead(
            id=row[0],
            email=row[1],
            first_name=row[2],
            last_name=row[3],
            phone=row[4],
            company=row[5],
            job_title=row[6],
            source=LeadSource(row[7]),
            source_campaign=row[8],
            status=LeadStatus(row[9]),
            lead_score=score,
            tags=json.loads(row[10]) if row[10] else [],
            custom_fields=json.loads(row[11]) if row[11] else {},
            first_submission_id=row[12],
            last_submission_id=row[13],
            submission_count=row[14],
            converted_at=row[15],
            created_at=row[16],
            updated_at=row[17]
        )

    def _row_to_lead_score(self, row) -> LeadScore:
        """Convert database row to LeadScore entity."""
        import json

        return LeadScore(
            lead_id=row[0],
            total_score=row[1],
            scores=json.loads(row[2]) if row[2] else {},
            grade=row[3],
            is_hot_lead=row[4],
            reasons=json.loads(row[5]) if row[5] else [],
            created_at=row[6],
            updated_at=row[7]
        )

    def _row_to_validation_rule(self, row) -> FormValidationRule:
        """Convert database row to FormValidationRule entity."""
        return FormValidationRule(
            id=row[0],
            field_name=row[2],  # Skip form_id at index 1
            rule_type=row[3],
            rule_value=row[4],
            error_message=row[5],
            is_active=row[6],
            created_at=row[7]
        )
