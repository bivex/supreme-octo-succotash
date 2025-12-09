"""Form integration routes."""

import json
from loguru import logger


class FormRoutes:
    """Routes for form integration."""

    def register(self, app):
        """Register routes."""
        self._register_form_submit(app)

    def _register_form_submit(self, app):
        """Register form submission route."""
        def submit_form(res, req):
            """Handle form submission."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers

            try:
                # Mock form submission response
                result = {
                    "status": "success",
                    "lead_id": "lead_123",
                    "message": "Form submitted successfully"
                }

                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.write_status(200)
                res.end(json.dumps(result))

            except Exception as e:
                logger.error(f"Error in form submission: {e}")
                error_response = {"status": "error", "message": str(e)}
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        app.post('/forms/submit', submit_form)
