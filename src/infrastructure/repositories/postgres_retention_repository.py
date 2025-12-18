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

"""PostgreSQL retention repository implementation."""

import psycopg2
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import defaultdict

from ...domain.entities.retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, UserSegment, RetentionCampaignStatus
from ...domain.repositories.retention_repository import RetentionRepository


class PostgresRetentionRepository(RetentionRepository):
    """PostgreSQL implementation of RetentionRepository."""

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
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        # Create retention_campaigns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retention_campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                target_segment TEXT NOT NULL,
                status TEXT NOT NULL,
                triggers JSONB,
                message_template TEXT NOT NULL,
                target_user_count INTEGER NOT NULL,
                sent_count INTEGER NOT NULL DEFAULT 0,
                opened_count INTEGER NOT NULL DEFAULT 0,
                clicked_count INTEGER NOT NULL DEFAULT 0,
                converted_count INTEGER NOT NULL DEFAULT 0,
                budget DECIMAL(10,2),
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create churn_predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS churn_predictions (
                customer_id TEXT PRIMARY KEY,
                churn_probability DECIMAL(3,2) NOT NULL,
                risk_level TEXT NOT NULL,
                predicted_churn_date TIMESTAMP,
                reasons JSONB,
                last_activity_date TIMESTAMP NOT NULL,
                engagement_score DECIMAL(5,2) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create user_engagement_profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_engagement_profiles (
                customer_id TEXT PRIMARY KEY,
                total_sessions INTEGER NOT NULL DEFAULT 0,
                total_clicks INTEGER NOT NULL DEFAULT 0,
                total_conversions INTEGER NOT NULL DEFAULT 0,
                avg_session_duration DECIMAL(5,2) NOT NULL DEFAULT 0.0,
                last_session_date TIMESTAMP NOT NULL,
                engagement_score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
                segment TEXT NOT NULL,
                interests JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_status ON retention_campaigns(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_segment ON retention_campaigns(target_segment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_dates ON retention_campaigns(start_date, end_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_churn_risk ON churn_predictions(risk_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_churn_probability ON churn_predictions(churn_probability)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_segment ON user_engagement_profiles(segment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_score ON user_engagement_profiles(engagement_score)")

        conn.commit()
        cursor.close()
        conn.close()

    def save_retention_campaign(self, campaign: RetentionCampaign) -> None:
        """Save retention campaign."""
        import json
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO retention_campaigns
            (id, name, description, target_segment, status, triggers, message_template,
             target_user_count, sent_count, opened_count, clicked_count, converted_count,
             budget, start_date, end_date, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                target_segment = EXCLUDED.target_segment,
                status = EXCLUDED.status,
                triggers = EXCLUDED.triggers,
                message_template = EXCLUDED.message_template,
                target_user_count = EXCLUDED.target_user_count,
                sent_count = EXCLUDED.sent_count,
                opened_count = EXCLUDED.opened_count,
                clicked_count = EXCLUDED.clicked_count,
                converted_count = EXCLUDED.converted_count,
                budget = EXCLUDED.budget,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                updated_at = CURRENT_TIMESTAMP
        """, (
            campaign.id,
            campaign.name,
            campaign.description,
            campaign.target_segment.value,
            campaign.status.value,
            json.dumps([{"id": t.id, "type": t.type, "value": t.value, "operator": t.operator} for t in campaign.triggers]),
            campaign.message_template,
            campaign.target_user_count,
            campaign.sent_count,
            campaign.opened_count,
            campaign.clicked_count,
            campaign.converted_count,
            campaign.budget,
            campaign.start_date,
            campaign.end_date,
            campaign.created_at,
            campaign.updated_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_retention_campaign(self, campaign_id: str) -> Optional[RetentionCampaign]:
        """Get retention campaign by ID."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM retention_campaigns WHERE id = %s", (campaign_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return self._row_to_campaign(row) if row else None

    def get_all_retention_campaigns(self, status_filter: Optional[str] = None) -> List[RetentionCampaign]:
        """Get all retention campaigns, optionally filtered by status."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM retention_campaigns"
        params = []

        if status_filter:
            query += " WHERE status = %s"
            params.append(status_filter)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_campaign(row) for row in rows]

    def get_active_retention_campaigns(self) -> List[RetentionCampaign]:
        """Get currently active retention campaigns."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM retention_campaigns
            WHERE status = %s AND start_date <= CURRENT_TIMESTAMP
            AND (end_date IS NULL OR end_date >= CURRENT_TIMESTAMP)
            ORDER BY created_at DESC
        """, (RetentionCampaignStatus.ACTIVE.value,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_campaign(row) for row in rows]

    def update_campaign_metrics(self, campaign_id: str, sent_count: int,
                               opened_count: int, clicked_count: int, converted_count: int) -> None:
        """Update campaign performance metrics."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE retention_campaigns
            SET sent_count = %s, opened_count = %s, clicked_count = %s,
                converted_count = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (sent_count, opened_count, clicked_count, converted_count, campaign_id))

        conn.commit()
        cursor.close()
        conn.close()

    def save_churn_prediction(self, prediction: ChurnPrediction) -> None:
        """Save churn prediction."""
        import json
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO churn_predictions
            (customer_id, churn_probability, risk_level, predicted_churn_date, reasons,
             last_activity_date, engagement_score, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                churn_probability = EXCLUDED.churn_probability,
                risk_level = EXCLUDED.risk_level,
                predicted_churn_date = EXCLUDED.predicted_churn_date,
                reasons = EXCLUDED.reasons,
                last_activity_date = EXCLUDED.last_activity_date,
                engagement_score = EXCLUDED.engagement_score,
                updated_at = CURRENT_TIMESTAMP
        """, (
            prediction.customer_id,
            prediction.churn_probability,
            prediction.risk_level,
            prediction.predicted_churn_date,
            json.dumps(prediction.reasons),
            prediction.last_activity_date,
            prediction.engagement_score,
            prediction.created_at,
            prediction.updated_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_churn_prediction(self, customer_id: str) -> Optional[ChurnPrediction]:
        """Get churn prediction for customer."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM churn_predictions WHERE customer_id = %s", (customer_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return self._row_to_churn_prediction(row) if row else None

    def get_high_risk_customers(self, limit: int = 100) -> List[ChurnPrediction]:
        """Get customers with high churn risk."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM churn_predictions
            WHERE risk_level = 'high'
            ORDER BY churn_probability DESC
            LIMIT %s
        """, (limit,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_churn_prediction(row) for row in rows]

    def save_user_engagement_profile(self, profile: UserEngagementProfile) -> None:
        """Save user engagement profile."""
        import json
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_engagement_profiles
            (customer_id, total_sessions, total_clicks, total_conversions, avg_session_duration,
             last_session_date, engagement_score, segment, interests, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                total_sessions = EXCLUDED.total_sessions,
                total_clicks = EXCLUDED.total_clicks,
                total_conversions = EXCLUDED.total_conversions,
                avg_session_duration = EXCLUDED.avg_session_duration,
                last_session_date = EXCLUDED.last_session_date,
                engagement_score = EXCLUDED.engagement_score,
                segment = EXCLUDED.segment,
                interests = EXCLUDED.interests,
                updated_at = CURRENT_TIMESTAMP
        """, (
            profile.customer_id,
            profile.total_sessions,
            profile.total_clicks,
            profile.total_conversions,
            profile.avg_session_duration,
            profile.last_session_date,
            profile.engagement_score,
            profile.segment.value,
            json.dumps(profile.interests),
            profile.created_at,
            profile.updated_at
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_user_engagement_profile(self, customer_id: str) -> Optional[UserEngagementProfile]:
        """Get user engagement profile by customer ID."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_engagement_profiles WHERE customer_id = %s", (customer_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return self._row_to_engagement_profile(row) if row else None

    def get_users_by_segment(self, segment: UserSegment, limit: int = 100) -> List[UserEngagementProfile]:
        """Get users by engagement segment."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM user_engagement_profiles
            WHERE segment = %s
            ORDER BY engagement_score DESC
            LIMIT %s
        """, (segment.value, limit))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [self._row_to_engagement_profile(row) for row in rows]

    def get_retention_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get retention analytics for date range."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        # Get campaign metrics
        cursor.execute("""
            SELECT
                COUNT(*) as total_campaigns,
                SUM(sent_count) as total_sent,
                SUM(opened_count) as total_opened,
                SUM(clicked_count) as total_clicked,
                SUM(converted_count) as total_converted
            FROM retention_campaigns
            WHERE created_at >= %s AND created_at <= %s
        """, (start_date, end_date))

        campaign_row = cursor.fetchone()

        # Get active campaigns
        cursor.execute("""
            SELECT COUNT(*) as active_campaigns
            FROM retention_campaigns
            WHERE status = %s AND created_at >= %s AND created_at <= %s
        """, (RetentionCampaignStatus.ACTIVE.value, start_date, end_date))

        active_row = cursor.fetchone()

        # Get churn risk distribution
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM churn_predictions
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY risk_level
        """, (start_date, end_date))

        risk_rows = cursor.fetchall()
        risk_distribution = {row[0]: row[1] for row in risk_rows}

        # Get segment distribution
        cursor.execute("""
            SELECT segment, COUNT(*) as count
            FROM user_engagement_profiles
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY segment
        """, (start_date, end_date))

        segment_rows = cursor.fetchall()
        segment_distribution = {row[0]: row[1] for row in segment_rows}

        cursor.close()
        conn.close()

        # Calculate rates
        total_sent = campaign_row[1] or 0
        total_opened = campaign_row[2] or 0
        total_clicked = campaign_row[3] or 0
        total_converted = campaign_row[4] or 0

        return {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'campaign_metrics': {
                'total_campaigns': campaign_row[0] or 0,
                'active_campaigns': active_row[0] or 0,
                'total_sent': total_sent,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'total_converted': total_converted,
                'open_rate': total_opened / max(total_sent, 1),
                'click_rate': total_clicked / max(total_sent, 1),
                'conversion_rate': total_converted / max(total_sent, 1)
            },
            'churn_risk_distribution': risk_distribution,
            'segment_distribution': segment_distribution
        }

    def get_campaign_performance_summary(self, campaign_id: str) -> Dict[str, Any]:
        """Get detailed performance summary for a campaign."""
        campaign = self.get_retention_campaign(campaign_id)
        if not campaign:
            return {}

        return {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'status': campaign.status.value,
            'target_segment': campaign.target_segment.value,
            'metrics': {
                'target_user_count': campaign.target_user_count,
                'sent_count': campaign.sent_count,
                'opened_count': campaign.opened_count,
                'clicked_count': campaign.clicked_count,
                'converted_count': campaign.converted_count,
                'open_rate': campaign.open_rate,
                'click_rate': campaign.click_rate,
                'conversion_rate': campaign.conversion_rate
            },
            'budget': campaign.budget,
            'dates': {
                'start_date': campaign.start_date.isoformat() if campaign.start_date else None,
                'end_date': campaign.end_date.isoformat() if campaign.end_date else None,
                'days_remaining': campaign.days_remaining
            }
        }

    def _row_to_campaign(self, row) -> RetentionCampaign:
        """Convert database row to RetentionCampaign entity."""
        import json
        from ...domain.entities.retention import RetentionTrigger

        # Parse triggers
        triggers_data = json.loads(row[5]) if row[5] else []
        triggers = [
            RetentionTrigger(
                id=t["id"],
                type=t["type"],
                value=t["value"],
                operator=t["operator"],
                created_at=datetime.now()  # Simplified
            ) for t in triggers_data
        ]

        return RetentionCampaign(
            id=row[0],
            name=row[1],
            description=row[2],
            target_segment=UserSegment(row[3]),
            status=RetentionCampaignStatus(row[4]),
            triggers=triggers,
            message_template=row[6],
            target_user_count=row[7],
            sent_count=row[8],
            opened_count=row[9],
            clicked_count=row[10],
            converted_count=row[11],
            budget=row[12],
            start_date=row[13],
            end_date=row[14],
            created_at=row[15],
            updated_at=row[16]
        )

    def _row_to_churn_prediction(self, row) -> ChurnPrediction:
        """Convert database row to ChurnPrediction entity."""
        import json

        return ChurnPrediction(
            customer_id=row[0],
            churn_probability=float(row[1]),
            risk_level=row[2],
            predicted_churn_date=row[3],
            reasons=json.loads(row[4]) if row[4] else [],
            last_activity_date=row[5],
            engagement_score=float(row[6]),
            created_at=row[7],
            updated_at=row[8]
        )

    def _row_to_engagement_profile(self, row) -> UserEngagementProfile:
        """Convert database row to UserEngagementProfile entity."""
        import json

        return UserEngagementProfile(
            customer_id=row[0],
            total_sessions=row[1],
            total_clicks=row[2],
            total_conversions=row[3],
            avg_session_duration=float(row[4]),
            last_session_date=row[5],
            engagement_score=float(row[6]),
            segment=UserSegment(row[7]),
            interests=json.loads(row[8]) if row[8] else [],
            created_at=row[9],
            updated_at=row[10]
        )
