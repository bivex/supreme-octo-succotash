# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:31
# Last Updated: 2025-12-18T12:28:31
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""In-memory goal repository implementation."""

from typing import Dict, List, Optional
from collections import defaultdict
from ...domain.repositories.goal_repository import GoalRepository
from ...domain.entities.goal import Goal, GoalType


class InMemoryGoalRepository(GoalRepository):
    """In-memory implementation of goal repository."""

    def __init__(self):
        self._goals: Dict[str, Goal] = {}
        self._campaign_index: Dict[int, List[str]] = {}  # campaign_id -> list of goal_ids
        self._type_index: Dict[GoalType, List[str]] = {}  # goal_type -> list of goal_ids
        self._tag_index: Dict[str, List[str]] = {}  # tag -> list of goal_ids

    def save(self, goal: Goal) -> None:
        """Save a goal."""
        self._goals[goal.id] = goal

        # Update campaign index
        if goal.campaign_id not in self._campaign_index:
            self._campaign_index[goal.campaign_id] = []
        if goal.id not in self._campaign_index[goal.campaign_id]:
            self._campaign_index[goal.campaign_id].append(goal.id)

        # Update type index
        if goal.goal_type not in self._type_index:
            self._type_index[goal.goal_type] = []
        if goal.id not in self._type_index[goal.goal_type]:
            self._type_index[goal.goal_type].append(goal.id)

        # Update tag index
        for tag in goal.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if goal.id not in self._tag_index[tag]:
                self._tag_index[tag].append(goal.id)

    def get_by_id(self, goal_id: str) -> Optional[Goal]:
        """Get goal by ID."""
        return self._goals.get(goal_id)

    def get_by_campaign_id(self, campaign_id: int, active_only: bool = True) -> List[Goal]:
        """Get goals by campaign ID."""
        goal_ids = self._campaign_index.get(campaign_id, [])
        goals = [self._goals[goal_id] for goal_id in goal_ids if goal_id in self._goals]

        if active_only:
            goals = [goal for goal in goals if goal.is_active]

        return goals

    def get_by_type(self, goal_type: GoalType, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by type, optionally filtered by campaign."""
        goal_ids = self._type_index.get(goal_type, [])
        goals = [self._goals[goal_id] for goal_id in goal_ids if goal_id in self._goals]

        if campaign_id is not None:
            goals = [goal for goal in goals if goal.campaign_id == campaign_id]

        return goals

    def update_goal(self, goal_id: str, updates: dict) -> Optional[Goal]:
        """Update goal with new data."""
        if goal_id not in self._goals:
            return None

        current_goal = self._goals[goal_id]

        # Create updated goal with new data
        updated_goal = Goal(
            id=current_goal.id,
            campaign_id=updates.get('campaign_id', current_goal.campaign_id),
            name=updates.get('name', current_goal.name),
            description=updates.get('description', current_goal.description),
            goal_type=updates.get('goal_type', current_goal.goal_type),
            trigger_type=updates.get('trigger_type', current_goal.trigger_type),
            trigger_config=updates.get('trigger_config', current_goal.trigger_config),
            value_config=updates.get('value_config', current_goal.value_config),
            is_active=updates.get('is_active', current_goal.is_active),
            attribution_window_days=updates.get('attribution_window_days', current_goal.attribution_window_days),
            priority=updates.get('priority', current_goal.priority),
            tags=updates.get('tags', current_goal.tags),
            created_at=current_goal.created_at,
            updated_at=updates.get('updated_at', current_goal.updated_at)
        )

        self.save(updated_goal)
        return updated_goal

    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal."""
        if goal_id not in self._goals:
            return False

        goal = self._goals[goal_id]

        # Remove from indexes
        if goal.campaign_id in self._campaign_index:
            self._campaign_index[goal.campaign_id] = [
                gid for gid in self._campaign_index[goal.campaign_id] if gid != goal_id
            ]

        if goal.goal_type in self._type_index:
            self._type_index[goal.goal_type] = [
                gid for gid in self._type_index[goal.goal_type] if gid != goal_id
            ]

        for tag in goal.tags:
            if tag in self._tag_index:
                self._tag_index[tag] = [
                    gid for gid in self._tag_index[tag] if gid != goal_id
                ]

        # Remove goal
        del self._goals[goal_id]
        return True

    def get_active_goals_for_campaign(self, campaign_id: int) -> List[Goal]:
        """Get all active goals for a campaign, ordered by priority."""
        goals = self.get_by_campaign_id(campaign_id, active_only=True)
        # Sort by priority (higher priority first)
        goals.sort(key=lambda g: g.priority, reverse=True)
        return goals

    def get_goals_by_tag(self, tag: str, campaign_id: Optional[int] = None) -> List[Goal]:
        """Get goals by tag, optionally filtered by campaign."""
        goal_ids = self._tag_index.get(tag, [])
        goals = [self._goals[goal_id] for goal_id in goal_ids if goal_id in self._goals]

        if campaign_id is not None:
            goals = [goal for goal in goals if goal.campaign_id == campaign_id]

        return goals
