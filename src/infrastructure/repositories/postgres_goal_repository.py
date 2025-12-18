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

"""PostgreSQL goal repository implementation."""

import json
from datetime import datetime
from typing import Optional, List

from ...domain.entities.goal import Goal, GoalType
from ...domain.repositories.goal_repository import GoalRepository


class PostgresGoalRepository(GoalRepository):
    """PostgreSQL implementation of GoalRepository."""

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

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS goals
                       (
                           id
                           TEXT
                           PRIMARY
                           KEY,
                           campaign_id
                           TEXT
                           NOT
                           NULL,
                           name
                           TEXT
                           NOT
                           NULL,
                           description
                           TEXT,
                           goal_type
                           TEXT
                           NOT
                           NULL,
                           target_value
                           DECIMAL
                       (
                           10,
                           2
                       ),
                           current_value DECIMAL
                       (
                           10,
                           2
                       ) DEFAULT 0.0,
                           status TEXT NOT NULL,
                           priority INTEGER DEFAULT 1,
                           conditions JSONB,
                           created_at TIMESTAMP NOT NULL,
                           updated_at TIMESTAMP NOT NULL
                           )
                       """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_campaign_id ON goals(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_type ON goals(goal_type)")

        conn.commit()

    def _row_to_goal(self, row) -> Goal:
        """Convert database row to Goal entity."""
        return Goal(
            id=row["id"],
            campaign_id=row["campaign_id"],
            name=row["name"],
            description=row["description"],
            goal_type=GoalType(row["goal_type"]),
            target_value=float(row["target_value"]) if row["target_value"] else None,
            current_value=float(row["current_value"]),
            status=row["status"],
            priority=row["priority"],
            conditions=row["conditions"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save(self, goal: Goal) -> None:
        """Save a goal."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       INSERT INTO goals
                       (id, campaign_id, name, description, goal_type, target_value,
                        current_value, status, priority, conditions, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO
                       UPDATE SET
                           campaign_id = EXCLUDED.campaign_id,
                           name = EXCLUDED.name,
                           description = EXCLUDED.description,
                           goal_type = EXCLUDED.goal_type,
                           target_value = EXCLUDED.target_value,
                           current_value = EXCLUDED.current_value,
                           status = EXCLUDED.status,
                           priority = EXCLUDED.priority,
                           conditions = EXCLUDED.conditions,
                           updated_at = EXCLUDED.updated_at
                       """, (
                           goal.id, goal.campaign_id, goal.name, goal.description,
                           goal.goal_type.value, goal.target_value, goal.current_value,
                           goal.status, goal.priority, json.dumps(goal.conditions),
                           goal.created_at, goal.updated_at
                       ))

        conn.commit()

    def get_by_id(self, goal_id: str) -> Optional[Goal]:
        """Get goal by ID."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM goals WHERE id = %s", (goal_id,))

        row = cursor.fetchone()
        if row:
            # Convert tuple to dict for easier access
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            return self._row_to_goal(row_dict)
        return None

    def get_by_campaign_id(self, campaign_id: int, active_only: bool = True) -> List[Goal]:
        """Get goals by campaign ID."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        if active_only:
            cursor.execute("""
                           SELECT *
                           FROM goals
                           WHERE campaign_id = %s
                             AND status = 'active'
                           ORDER BY priority DESC, created_at DESC
                           """, (str(campaign_id),))
        else:
            cursor.execute("""
                           SELECT *
                           FROM goals
                           WHERE campaign_id = %s
                           ORDER BY priority DESC, created_at DESC
                           """, (str(campaign_id),))

        goals = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            goals.append(self._row_to_goal(row_dict))

        return goals

    def get_by_type(self, goal_type: GoalType, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by type, optionally filtered by campaign."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        if campaign_id is not None:
            cursor.execute("""
                           SELECT *
                           FROM goals
                           WHERE goal_type = %s
                             AND campaign_id = %s
                           ORDER BY priority DESC, created_at DESC
                           """, (goal_type.value, str(campaign_id)))
        else:
            cursor.execute("""
                           SELECT *
                           FROM goals
                           WHERE goal_type = %s
                           ORDER BY priority DESC, created_at DESC
                           """, (goal_type.value,))

        goals = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            goals.append(self._row_to_goal(row_dict))

        return goals

    def update_goal(self, goal_id: str, updates: dict) -> Optional[Goal]:
        """Update goal with new data."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        set_parts = []
        params = []

        for key, value in updates.items():
            if key in ['name', 'description', 'status']:
                set_parts.append(f"{key} = %s")
                params.append(value)
            elif key == 'goal_type' and isinstance(value, GoalType):
                set_parts.append("goal_type = %s")
                params.append(value.value)
            elif key in ['target_value', 'current_value', 'priority']:
                set_parts.append(f"{key} = %s")
                params.append(value)
            elif key == 'conditions':
                set_parts.append("conditions = %s")
                params.append(json.dumps(value))

        if not set_parts:
            return self.get_by_id(goal_id)

        set_clause = ", ".join(set_parts)
        params.extend([datetime.now(), goal_id])

        cursor.execute(f"""
            UPDATE goals SET {set_clause}, updated_at = %s
            WHERE id = %s
        """, params)

        conn.commit()

        return self.get_by_id(goal_id)

    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM goals WHERE id = %s", (goal_id,))

        deleted = cursor.rowcount > 0
        conn.commit()

        return deleted

    def get_active_goals_for_campaign(self, campaign_id: int) -> List[Goal]:
        """Get all active goals for a campaign, ordered by priority."""
        return self.get_by_campaign_id(campaign_id, active_only=True)

    def get_goals_by_tag(self, tag: str, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by tag, optionally filtered by campaign."""
        conn = self._container.get_db_connection()
        cursor = conn.cursor()

        if campaign_id is not None:
            cursor.execute("""
                           SELECT *
                           FROM goals
                           WHERE campaign_id = %s
                             AND conditions ->>'tags' ? %s
                           ORDER BY priority DESC, created_at DESC
                           """, (str(campaign_id), tag))
        else:
            cursor.execute("""
                           SELECT *
                           FROM goals
                           WHERE conditions ->>'tags' ? %s
                           ORDER BY priority DESC, created_at DESC
                           """, (tag,))

        goals = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            goals.append(self._row_to_goal(row_dict))

        return goals
