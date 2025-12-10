"""SQLite goal repository implementation."""

import sqlite3
from typing import Optional, List
from datetime import datetime, timezone

from ...domain.entities.goal import Goal, GoalType
from ...domain.repositories.goal_repository import GoalRepository


class SQLiteGoalRepository(GoalRepository):
    """SQLite implementation of GoalRepository for stress testing."""

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                goal_type TEXT NOT NULL,
                target_value REAL,
                current_value REAL DEFAULT 0.0,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                conditions TEXT,  -- JSON string
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_campaign_id ON goals(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")

        conn.commit()

    def save(self, goal: Goal) -> None:
        """Save a goal."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO goals
            (id, campaign_id, name, description, goal_type, target_value,
             current_value, status, priority, conditions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal.id.value, goal.campaign_id, goal.name, goal.description,
            goal.goal_type, goal.target_value, goal.current_value, goal.status,
            goal.priority, json.dumps(goal.conditions) if goal.conditions else None,
            goal.created_at.isoformat(), goal.updated_at.isoformat()
        ))

        conn.commit()

    def find_by_id(self, goal_id: str) -> Optional[Goal]:
        """Find goal by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))

        row = cursor.fetchone()
        return self._row_to_goal(row) if row else None

    def find_by_campaign_id(self, campaign_id: str) -> List[Goal]:
        """Find goals by campaign ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM goals
            WHERE campaign_id = ?
            ORDER BY priority DESC, created_at DESC
        """, (campaign_id,))

        return [self._row_to_goal(row) for row in cursor.fetchall()]

    def find_active_goals_by_campaign_id(self, campaign_id: str) -> List[Goal]:
        """Find active goals by campaign ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM goals
            WHERE campaign_id = ? AND status = 'active'
            ORDER BY priority DESC, created_at DESC
        """, (campaign_id,))

        return [self._row_to_goal(row) for row in cursor.fetchall()]

    def get_by_id(self, goal_id: str) -> Optional[Goal]:
        """Get goal by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))

        row = cursor.fetchone()
        return self._row_to_goal(row) if row else None

    def get_by_campaign_id(self, campaign_id: int, active_only: bool = True) -> List[Goal]:
        """Get goals by campaign ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM goals WHERE campaign_id = ?"
        params = [campaign_id]

        if active_only:
            query += " AND status = 'active'"

        query += " ORDER BY priority DESC, created_at DESC"

        cursor.execute(query, params)
        return [self._row_to_goal(row) for row in cursor.fetchall()]

    def get_by_type(self, goal_type: GoalType, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by type, optionally filtered by campaign."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM goals WHERE goal_type = ?"
        params = [goal_type.value]

        if campaign_id is not None:
            query += " AND campaign_id = ?"
            params.append(campaign_id)

        query += " ORDER BY priority DESC, created_at DESC"

        cursor.execute(query, params)
        return [self._row_to_goal(row) for row in cursor.fetchall()]

    def update_goal(self, goal_id: str, updates: dict) -> Optional[Goal]:
        """Update goal with new data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        set_parts = []
        params = []

        for key, value in updates.items():
            if key in ['name', 'description', 'goal_type', 'target_value', 'current_value', 'status', 'priority']:
                set_parts.append(f"{key} = ?")
                params.append(value)
            elif key == 'conditions':
                import json
                set_parts.append("conditions = ?")
                params.append(json.dumps(value))

        if not set_parts:
            return self.get_by_id(goal_id)

        set_parts.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())

        query = f"UPDATE goals SET {', '.join(set_parts)} WHERE id = ?"
        params.append(goal_id)

        cursor.execute(query, params)
        conn.commit()

        return self.get_by_id(goal_id)

    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()

        return cursor.rowcount > 0

    def get_active_goals_for_campaign(self, campaign_id: int) -> List[Goal]:
        """Get all active goals for a campaign, ordered by priority."""
        return self.get_by_campaign_id(campaign_id, active_only=True)

    def get_goals_by_tag(self, tag: str, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by tag, optionally filtered by campaign."""
        # Note: This implementation assumes tags are stored in conditions JSON
        # Simplified implementation - would need more complex querying for full tag support
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM goals
            WHERE json_extract(conditions, '$.tags') LIKE ?
        """
        params = [f'%{tag}%']

        if campaign_id is not None:
            query += " AND campaign_id = ?"
            params.append(campaign_id)

        query += " ORDER BY priority DESC, created_at DESC"

        cursor.execute(query, params)
        return [self._row_to_goal(row) for row in cursor.fetchall()]

    def update_progress(self, goal_id: str, new_value: float) -> None:
        """Update goal progress."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE goals
            SET current_value = ?, updated_at = ?
            WHERE id = ?
        """, (new_value, datetime.now(timezone.utc).isoformat(), goal_id))

        conn.commit()

    def _row_to_goal(self, row) -> Goal:
        """Convert database row to Goal entity."""
        import json
        from ...domain.value_objects.identifiers import GoalId

        return Goal(
            id=GoalId.from_string(row["id"]),
            campaign_id=row["campaign_id"],
            name=row["name"],
            description=row["description"],
            goal_type=row["goal_type"],
            target_value=row["target_value"],
            current_value=row["current_value"],
            status=row["status"],
            priority=row["priority"],
            conditions=json.loads(row["conditions"]) if row["conditions"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
