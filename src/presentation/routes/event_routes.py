"""Event tracking HTTP routes."""

import json
from loguru import logger
from ...application.handlers.track_event_handler import TrackEventHandler


class EventRoutes:
    """Socketify routes for event tracking operations."""

    def __init__(self, track_event_handler: TrackEventHandler):
        self.track_event_handler = track_event_handler

    def register(self, app):
        """Register routes with socketify app."""
        self._register_track_event(app)

    def _register_track_event(self, app):
        """Register event tracking route."""
        def track_event(res, req):
            """Track user events from landing pages."""
            from ...presentation.middleware.security_middleware import validate_request, add_security_headers
            import json

            try:
                logger.debug("Event tracking request received")

                # For event tracking, we might want minimal validation
                # since events come from public landing pages

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
                                        logger.error("Invalid JSON in event tracking request")
                                        res.write_status(400)
                                        res.write_header("Content-Type", "application/json")
                                        add_security_headers(res)
                                        res.end(json.dumps({
                                            "status": "error",
                                            "message": "Invalid JSON format"
                                        }))
                                        return

                            # Extract request context
                            request_context = {
                                'ip': self._get_client_ip(req),
                                'user_agent': req.get_header('user-agent') or req.get_header('User-Agent'),
                                'referrer': req.get_header('referer') or req.get_header('Referer'),
                            }

                            # Track event
                            result = self.track_event_handler.handle(body_data, request_context)

                            # Return response
                            res.write_header("Content-Type", "application/json")
                            add_security_headers(res)

                            if result["status"] == "success":
                                res.write_status(200)
                            else:
                                res.write_status(400)

                            res.end(json.dumps(result))

                    except Exception as e:
                        logger.error(f"Error processing event tracking data: {e}", exc_info=True)
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
                logger.error(f"Error in track_event: {e}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": "Internal server error"
                }
                res.write_status(500)
                res.write_header("Content-Type", "application/json")
                add_security_headers(res)
                res.end(json.dumps(error_response))

        # Register the event tracking endpoint
        app.post('/events/track', track_event)

    def _get_client_ip(self, req) -> str:
        """Extract client IP address from request."""
        # Try X-Forwarded-For header first (for proxies/load balancers)
        x_forwarded_for = req.get_header('x-forwarded-for') or req.get_header('X-Forwarded-For')
        if x_forwarded_for:
            # Take first IP if multiple
            return x_forwarded_for.split(',')[0].strip()

        # Try X-Real-IP header
        x_real_ip = req.get_header('x-real-ip') or req.get_header('X-Real-IP')
        if x_real_ip:
            return x_real_ip

        # Fallback to remote address
        # Note: socketify might not have direct access to remote IP
        # This would need to be implemented based on the actual server setup
        return "127.0.0.1"  # Default for local development
