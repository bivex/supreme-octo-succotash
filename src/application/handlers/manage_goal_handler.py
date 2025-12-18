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

"""Goal management handler."""

import json
from typing import Dict, Any, List, Optional
from loguru import logger
from ...domain.repositories.goal_repository import GoalRepository
from ...domain.services.goal.goal_service import GoalService
from ...domain.entities.goal import Goal


class ManageGoalHandler:
    """Handler for managing conversion goals."""

    def __init__(
        self,
        goal_repository: GoalRepository,
        goal_service: GoalService
    ):
        self.goal_repository = goal_repository
        self.goal_service = goal_service

    def create_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversion goal."""
        try:
            logger.info(f"Creating goal for campaign {goal_data.get('campaign_id')}")

            # Validate goal data
            is_valid, error_message = self.goal_service.validate_goal_data(goal_data)
            if not is_valid:
                return {
                    "status": "error",
                    "message": error_message
                }

            # Create goal entity
            goal = Goal.create_from_request(goal_data)

            # Save goal
            self.goal_repository.save(goal)
            logger.info(f"Goal created successfully: {goal.id}")

            return {
                "status": "success",
                "goal_id": goal.id,
                "goal": self._goal_to_dict(goal)
            }

        except Exception as e:
            logger.error(f"Error creating goal: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def get_goal(self, goal_id: str) -> Dict[str, Any]:
        """Get a specific goal."""
        try:
            goal = self.goal_repository.get_by_id(goal_id)
            if not goal:
                return {
                    "status": "error",
                    "message": "Goal not found"
                }

            return {
                "status": "success",
                "goal": self._goal_to_dict(goal)
            }

        except Exception as e:
            logger.error(f"Error getting goal {goal_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def list_goals(self, campaign_id: Optional[int] = None, active_only: bool = True) -> Dict[str, Any]:
        """List goals, optionally filtered by campaign."""
        try:
            if campaign_id:
                goals = self.goal_repository.get_by_campaign_id(campaign_id, active_only)
            else:
                # Getting all goals without campaign filter is not supported yet
                raise ValueError("Listing all goals without campaign filter is not supported. Please provide a campaign_id parameter.")

            return {
                "status": "success",
                "goals": [self._goal_to_dict(goal) for goal in goals],
                "total": len(goals)
            }

        except Exception as e:
            logger.error(f"Error listing goals: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def update_goal(self, goal_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing goal."""
        try:
            # Validate updates if they include configuration
            if any(key in updates for key in ['goal_type', 'trigger_type', 'trigger_config']):
                # Get current goal and merge with updates for validation
                current_goal = self.goal_repository.get_by_id(goal_id)
                if current_goal:
                    merged_data = {
                        'campaign_id': current_goal.campaign_id,
                        'name': current_goal.name,
                        'goal_type': current_goal.goal_type.value,
                        'trigger_type': current_goal.trigger_type.value,
                        'trigger_config': current_goal.trigger_config,
                        'value_config': current_goal.value_config,
                        'attribution_window_days': current_goal.attribution_window_days,
                        'priority': current_goal.priority,
                        **updates
                    }

                    is_valid, error_message = self.goal_service.validate_goal_data(merged_data)
                    if not is_valid:
                        return {
                            "status": "error",
                            "message": error_message
                        }

            # Add updated_at timestamp
            from datetime import datetime
            updates['updated_at'] = datetime.utcnow()

            # Update goal
            updated_goal = self.goal_repository.update_goal(goal_id, updates)
            if not updated_goal:
                return {
                    "status": "error",
                    "message": "Goal not found"
                }

            return {
                "status": "success",
                "goal": self._goal_to_dict(updated_goal)
            }

        except Exception as e:
            logger.error(f"Error updating goal {goal_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def delete_goal(self, goal_id: str) -> Dict[str, Any]:
        """Delete a goal."""
        try:
            deleted = self.goal_repository.delete_goal(goal_id)
            if not deleted:
                return {
                    "status": "error",
                    "message": "Goal not found"
                }

            return {
                "status": "success",
                "message": "Goal deleted successfully"
            }

        except Exception as e:
            logger.error(f"Error deleting goal {goal_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_goal_templates(self) -> Dict[str, Any]:
        """Get predefined goal templates."""
        try:
            templates = self.goal_service.get_goal_templates()
            return {
                "status": "success",
                "templates": templates
            }

        except Exception as e:
            logger.error(f"Error getting goal templates: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def duplicate_goal(self, goal_id: str, new_campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Duplicate an existing goal."""
        try:
            duplicated_goal = self.goal_service.duplicate_goal(goal_id, new_campaign_id)
            if not duplicated_goal:
                return {
                    "status": "error",
                    "message": "Original goal not found"
                }

            return {
                "status": "success",
                "goal": self._goal_to_dict(duplicated_goal)
            }

        except Exception as e:
            logger.error(f"Error duplicating goal {goal_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_goal_performance(self, goal_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get performance metrics for a specific goal."""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            performance = self.goal_service.calculate_goal_performance(goal_id, start, end)

            if 'error' in performance:
                return {
                    "status": "error",
                    "message": performance['error']
                }

            return {
                "status": "success",
                "performance": performance
            }

        except Exception as e:
            logger.error(f"Error getting goal performance for {goal_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _goal_to_dict(self, goal: Goal) -> Dict[str, Any]:
        """Convert goal entity to dictionary."""
        return {
            "id": goal.id,
            "campaign_id": goal.campaign_id,
            "name": goal.name,
            "description": goal.description,
            "goal_type": goal.goal_type.value,
            "trigger_type": goal.trigger_type.value,
            "trigger_config": goal.trigger_config,
            "value_config": goal.value_config,
            "is_active": goal.is_active,
            "attribution_window_days": goal.attribution_window_days,
            "priority": goal.priority,
            "tags": goal.tags,
            "created_at": goal.created_at.isoformat(),
            "updated_at": goal.updated_at.isoformat()
        }
