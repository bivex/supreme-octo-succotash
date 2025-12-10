"""SQLite retention repository implementation."""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import defaultdict

from ...domain.entities.retention import RetentionCampaign, ChurnPrediction, UserEngagementProfile, UserSegment, RetentionCampaignStatus
from ...domain.repositories.retention_repository import RetentionRepository


class SQLiteRetentionRepository(RetentionRepository):
    """SQLite implementation of RetentionRepository for stress testing."""

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

        # Create retention_campaigns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retention_campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                target_segment TEXT NOT NULL,
                status TEXT NOT NULL,
                triggers TEXT NOT NULL,  -- JSON string
                message_template TEXT NOT NULL,
                target_user_count INTEGER NOT NULL,
                sent_count INTEGER NOT NULL,
                opened_count INTEGER NOT NULL,
                clicked_count INTEGER NOT NULL,
                converted_count INTEGER NOT NULL,
                budget REAL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create churn_predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS churn_predictions (
                customer_id TEXT PRIMARY KEY,
                churn_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                predicted_churn_date TEXT,
                reasons TEXT NOT NULL,  -- JSON string
                last_activity_date TEXT NOT NULL,
                engagement_score REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create user_engagement_profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_engagement_profiles (
                customer_id TEXT PRIMARY KEY,
                total_sessions INTEGER NOT NULL,
                total_clicks INTEGER NOT NULL,
                total_conversions INTEGER NOT NULL,
                avg_session_duration REAL NOT NULL,
                last_session_date TEXT NOT NULL,
                engagement_score REAL NOT NULL,
                segment TEXT NOT NULL,
                interests TEXT NOT NULL,  -- JSON string
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
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

    def save_retention_campaign(self, campaign: RetentionCampaign) -> None:
        """Save retention campaign."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO retention_campaigns
            (id, name, description, target_segment, status, triggers, message_template,
             target_user_count, sent_count, opened_count, clicked_count, converted_count,
             budget, start_date, end_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            campaign.start_date.isoformat(),
            campaign.end_date.isoformat() if campaign.end_date else None,
            campaign.created_at.isoformat(),
            campaign.updated_at.isoformat()
        ))

        conn.commit()

    def get_retention_campaign(self, campaign_id: str) -> Optional[RetentionCampaign]:
        """Get retention campaign by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM retention_campaigns WHERE id = ?", (campaign_id,))

        row = cursor.fetchone()
        return self._row_to_campaign(row) if row else None

    def get_all_retention_campaigns(self, status_filter: Optional[str] = None) -> List[RetentionCampaign]:
        """Get all retention campaigns, optionally filtered by status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM retention_campaigns"
        params = []

        if status_filter:
            query += " WHERE status = ?"
            params.append(status_filter)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)

        return [self._row_to_campaign(row) for row in cursor.fetchall()]

    def get_active_retention_campaigns(self) -> List[RetentionCampaign]:
        """Get currently active retention campaigns."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute("""
            SELECT * FROM retention_campaigns
            WHERE status = ? AND start_date <= ? AND (end_date IS NULL OR end_date >= ?)
            ORDER BY created_at DESC
        """, (RetentionCampaignStatus.ACTIVE.value, now, now))

        return [self._row_to_campaign(row) for row in cursor.fetchall()]

    def update_campaign_metrics(self, campaign_id: str, sent_count: int,
                               opened_count: int, clicked_count: int, converted_count: int) -> None:
        """Update campaign performance metrics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE retention_campaigns
            SET sent_count = ?, opened_count = ?, clicked_count = ?, converted_count = ?, updated_at = ?
            WHERE id = ?
        """, (sent_count, opened_count, clicked_count, converted_count, datetime.now().isoformat(), campaign_id))

        conn.commit()

    def save_churn_prediction(self, prediction: ChurnPrediction) -> None:
        """Save churn prediction."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO churn_predictions
            (customer_id, churn_probability, risk_level, predicted_churn_date, reasons,
             last_activity_date, engagement_score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction.customer_id,
            prediction.churn_probability,
            prediction.risk_level,
            prediction.predicted_churn_date.isoformat() if prediction.predicted_churn_date else None,
            json.dumps(prediction.reasons),
            prediction.last_activity_date.isoformat(),
            prediction.engagement_score,
            prediction.created_at.isoformat(),
            prediction.updated_at.isoformat()
        ))

        conn.commit()

    def get_churn_prediction(self, customer_id: str) -> Optional[ChurnPrediction]:
        """Get churn prediction for customer."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM churn_predictions WHERE customer_id = ?", (customer_id,))

        row = cursor.fetchone()
        return self._row_to_churn_prediction(row) if row else None

    def get_high_risk_customers(self, limit: int = 100) -> List[ChurnPrediction]:
        """Get customers with high churn risk."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM churn_predictions
            WHERE risk_level = 'high'
            ORDER BY churn_probability DESC
            LIMIT ?
        """, (limit,))

        return [self._row_to_churn_prediction(row) for row in cursor.fetchall()]

    def save_user_engagement_profile(self, profile: UserEngagementProfile) -> None:
        """Save user engagement profile."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO user_engagement_profiles
            (customer_id, total_sessions, total_clicks, total_conversions, avg_session_duration,
             last_session_date, engagement_score, segment, interests, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.customer_id,
            profile.total_sessions,
            profile.total_clicks,
            profile.total_conversions,
            profile.avg_session_duration,
            profile.last_session_date.isoformat(),
            profile.engagement_score,
            profile.segment.value,
            json.dumps(profile.interests),
            profile.created_at.isoformat(),
            profile.updated_at.isoformat()
        ))

        conn.commit()

    def get_user_engagement_profile(self, customer_id: str) -> Optional[UserEngagementProfile]:
        """Get user engagement profile by customer ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_engagement_profiles WHERE customer_id = ?", (customer_id,))

        row = cursor.fetchone()
        return self._row_to_engagement_profile(row) if row else None

    def get_users_by_segment(self, segment: UserSegment, limit: int = 100) -> List[UserEngagementProfile]:
        """Get users by engagement segment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM user_engagement_profiles
            WHERE segment = ?
            ORDER BY engagement_score DESC
            LIMIT ?
        """, (segment.value, limit))

        return [self._row_to_engagement_profile(row) for row in cursor.fetchall()]

    def get_retention_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get retention analytics for date range."""
        conn = self._get_connection()
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
            WHERE created_at >= ? AND created_at <= ?
        """, (start_date.isoformat(), end_date.isoformat()))

        campaign_row = cursor.fetchone()

        # Get active campaigns
        cursor.execute("""
            SELECT COUNT(*) as active_campaigns
            FROM retention_campaigns
            WHERE status = ? AND created_at >= ? AND created_at <= ?
        """, (RetentionCampaignStatus.ACTIVE.value, start_date.isoformat(), end_date.isoformat()))

        active_row = cursor.fetchone()

        # Calculate rates
        total_sent = campaign_row[1] or 0
        total_opened = campaign_row[2] or 0
        total_clicked = campaign_row[3] or 0
        total_converted = campaign_row[4] or 0

        # Get churn risk distribution
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM churn_predictions
            WHERE created_at >= ? AND created_at <= ?
            GROUP BY risk_level
        """, (start_date.isoformat(), end_date.isoformat()))

        risk_distribution = {row[0]: row[1] for row in cursor.fetchall()}

        # Get segment distribution
        cursor.execute("""
            SELECT segment, COUNT(*) as count
            FROM user_engagement_profiles
            WHERE created_at >= ? AND created_at <= ?
            GROUP BY segment
        """, (start_date.isoformat(), end_date.isoformat()))

        segment_distribution = {row[0]: row[1] for row in cursor.fetchall()}

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
        triggers_data = json.loads(row["triggers"])
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
            id=row["id"],
            name=row["name"],
            description=row["description"],
            target_segment=UserSegment(row["target_segment"]),
            status=RetentionCampaignStatus(row["status"]),
            triggers=triggers,
            message_template=row["message_template"],
            target_user_count=row["target_user_count"],
            sent_count=row["sent_count"],
            opened_count=row["opened_count"],
            clicked_count=row["clicked_count"],
            converted_count=row["converted_count"],
            budget=row["budget"],
            start_date=datetime.fromisoformat(row["start_date"]),
            end_date=datetime.fromisoformat(row["end_date"]) if row["end_date"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

    def _row_to_churn_prediction(self, row) -> ChurnPrediction:
        """Convert database row to ChurnPrediction entity."""
        import json

        return ChurnPrediction(
            customer_id=row["customer_id"],
            churn_probability=row["churn_probability"],
            risk_level=row["risk_level"],
            predicted_churn_date=datetime.fromisoformat(row["predicted_churn_date"]) if row["predicted_churn_date"] else None,
            reasons=json.loads(row["reasons"]),
            last_activity_date=datetime.fromisoformat(row["last_activity_date"]),
            engagement_score=row["engagement_score"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

    def _row_to_engagement_profile(self, row) -> UserEngagementProfile:
        """Convert database row to UserEngagementProfile entity."""
        import json

        return UserEngagementProfile(
            customer_id=row["customer_id"],
            total_sessions=row["total_sessions"],
            total_clicks=row["total_clicks"],
            total_conversions=row["total_conversions"],
            avg_session_duration=row["avg_session_duration"],
            last_session_date=datetime.fromisoformat(row["last_session_date"]),
            engagement_score=row["engagement_score"],
            segment=UserSegment(row["segment"]),
            interests=json.loads(row["interests"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
