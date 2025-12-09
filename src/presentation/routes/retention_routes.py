"""Retention campaign routes."""

import json
from loguru import logger


class RetentionRoutes:
    """Routes for retention campaigns."""

    def register(self, app):
        """Register routes."""
        self._register_retention_campaigns(app)

    def _register_retention_campaigns(self, app):
        """Register retention campaigns route."""
        def get_retention_campaigns(res, req):
            """Get retention campaigns."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Mock retention campaigns response
                result = {
                    "status": "success",
                    "campaigns": [
                        {
                            "id": "retention_1",
                            "name": "Welcome Back Campaign",
                            "target_audience": "inactive_users_30_days",
                            "status": "active"
                        }
                    ]
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in retention campaigns: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.get('/retention/campaigns', get_retention_campaigns)
