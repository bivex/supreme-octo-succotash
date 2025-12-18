# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:13:08
# Last Updated: 2025-12-18T12:28:30
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Goal management HTTP routes."""

import json
from loguru import logger
from ...application.handlers.manage_goal_handler import ManageGoalHandler


class GoalRoutes:
    """Socketify routes for goal management operations."""

    def __init__(self, manage_goal_handler: ManageGoalHandler):
        self.manage_goal_handler = manage_goal_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_create_goal(app)
        self._register_get_goal(app)
        self._register_list_goals(app)
        self._register_update_goal(app)
        self._register_delete_goal(app)
        self._register_get_goal_performance(app)
        self._register_get_templates(app)
        self._register_duplicate_goal(app)

    def _register_create_goal(self, app):
        """Register create goal route."""
        def create_goal(res, req):
            """Create a new conversion goal."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.debug("Create goal request received")

                # Parse request body
                data_parts = []

                def on_data(res, chunk, is_last, *args):
                    try:
                        if chunk:
                            data_parts.append(chunk)

                        if is_last:
                            # Parse body
                            body_data = {}
                            if data_parts:
                                full_body = b"".join(data_parts)
                                if full_body:
                                    try:
                                        body_data = json.loads(full_body)
                                    except (ValueError, json.JSONDecodeError):
                                        logger.error("Invalid JSON in create goal request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Create goal
                            result = self.manage_goal_handler.create_goal(body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(201)
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing create goal data: {e}", exc_info=True)
                        error_response = {
                            "status": "error",
                            "message": "Internal server error"
                        }
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in create_goal: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the create goal endpoint
        app.post('/goals', create_goal)

    def _register_get_goal(self, app):
        """Register get goal route."""
        def get_goal(res, req):
            """Get a specific goal."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                goal_id = req.get_parameter(0)

                # Get goal
                result = self.manage_goal_handler.get_goal(goal_id)

                # Return response
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)

                if result["status"] == "success":
                    res.write_status(200)
                else:
                    res.write_status(404)

                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in get_goal: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/goals/:goal_id', get_goal)

    def _register_list_goals(self, app):
        """Register list goals route."""
        def list_goals(res, req):
            """List goals with optional filtering."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Parse query parameters
                campaign_id_str = req.get_query('campaign_id')
                campaign_id = int(campaign_id_str) if campaign_id_str else None

                active_only_str = req.get_query('active_only')
                active_only = active_only_str != 'false' if active_only_str else True

                # List goals
                result = self.manage_goal_handler.list_goals(campaign_id, active_only)

                # Return response
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)

                if result["status"] == "success":
                    res.write_status(200)
                else:
                    res.write_status(400)

                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in list_goals: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/goals', list_goals)

    def _register_update_goal(self, app):
        """Register update goal route."""
        def update_goal(res, req):
            """Update an existing goal."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.debug("Update goal request received")
                goal_id = req.get_parameter(0)

                # Parse request body
                data_parts = []

                def on_data(res, chunk, is_last, *args):
                    try:
                        if chunk:
                            data_parts.append(chunk)

                        if is_last:
                            # Parse body
                            body_data = {}
                            if data_parts:
                                full_body = b"".join(data_parts)
                                if full_body:
                                    try:
                                        body_data = json.loads(full_body)
                                    except (ValueError, json.JSONDecodeError):
                                        logger.error("Invalid JSON in update goal request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Update goal
                            result = self.manage_goal_handler.update_goal(goal_id, body_data)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            else:
                                res.write_status(404 if "not found" in result.get("message", "").lower() else 400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing update goal data: {e}", exc_info=True)
                        error_response = {
                            "status": "error",
                            "message": "Internal server error"
                        }
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in update_goal: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.put('/goals/:goal_id', update_goal)

    def _register_delete_goal(self, app):
        """Register delete goal route."""
        def delete_goal(res, req):
            """Delete a goal."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                goal_id = req.get_parameter(0)

                # Delete goal
                result = self.manage_goal_handler.delete_goal(goal_id)

                # Return response
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)

                if result["status"] == "success":
                    res.write_status(200)
                else:
                    res.write_status(404)

                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in delete_goal: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.delete('/goals/:goal_id', delete_goal)

    def _register_get_templates(self, app):
        """Register get goal templates route."""
        def get_templates(res, req):
            """Get predefined goal templates."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Get templates
                result = self.manage_goal_handler.get_goal_templates()

                # Return response
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)

                if result["status"] == "success":
                    res.write_status(200)
                else:
                    res.write_status(500)

                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in get_templates: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/goals/templates', get_templates)

    def _register_duplicate_goal(self, app):
        """Register duplicate goal route."""
        def duplicate_goal(res, req):
            """Duplicate an existing goal."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                goal_id = req.get_parameter(0)

                # Parse request body for optional new campaign_id
                data_parts = []

                def on_data(res, chunk, is_last, *args):
                    try:
                        if chunk:
                            data_parts.append(chunk)

                        if is_last:
                            # Parse body
                            body_data = {}
                            if data_parts:
                                full_body = b"".join(data_parts)
                                if full_body:
                                    try:
                                        body_data = json.loads(full_body)
                                    except (ValueError, json.JSONDecodeError):
                                        body_data = {}

                            new_campaign_id = body_data.get('campaign_id')

                            # Duplicate goal
                            result = self.manage_goal_handler.duplicate_goal(goal_id, new_campaign_id)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(201)
                            else:
                                res.write_status(404)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing duplicate goal data: {e}", exc_info=True)
                        error_response = {
                            "status": "error",
                            "message": "Internal server error"
                        }
                        res.write_status(500)
                        res.write_header("Content-Type", "application/json")
                        add_security_headers(res)
                        res.end(json.dumps(error_response))

                res.on_data(on_data)

            except Exception as e:
                logger.error(f"Error in duplicate_goal: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.post('/goals/:goal_id/duplicate', duplicate_goal)

    def _register_get_goal_performance(self, app):
        """Register get goal performance route."""
        def get_goal_performance(res, req):
            """Get performance metrics for a specific goal."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            # Validate request (authentication, rate limiting, etc.)
            if validate_request(req, res):
                return  # Validation failed, response already sent

            try:
                goal_id = req.get_parameter(0)
                start_date = req.get_query('start_date')
                end_date = req.get_query('end_date')

                # Validate required parameters
                if not start_date or not end_date:
                    error_response = {
                        "status": "error",
                        "message": "start_date and end_date query parameters are required"
                    }
                    res.write_status(400)
                    res.write_header("Content-Type", "application/json")
                    add_security_headers(res)
                    res.end(json.dumps(error_response))
                    return

                # Get goal performance
                result = self.manage_goal_handler.get_goal_performance(goal_id, start_date, end_date)

                # Return response
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)

                if result["status"] == "success":
                    res.write_status(200)
                else:
                    res.write_status(404 if "not found" in result.get("message", "").lower() else 400)

                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in get_goal_performance: {e}")
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/goals/:goal_id/performance', get_goal_performance)
