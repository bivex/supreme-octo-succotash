
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:49
# Last Updated: 2025-12-18T12:11:49
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Minimal test that exactly mimics main_clean.py structure
"""

import asyncio
import signal
import sys
import inspect
import socketify
from loguru import logger

# Mock settings
class MockSettings:
    class API:
        port = 5004

settings = MockSettings()
MockSettings.api = MockSettings.API()

async def create_test_app():
    """Create app exactly like main_clean.py"""
    logger.info("🏗️ START: Creating Socketify application")

    app = socketify.App()
    logger.info("🏗️ Step 1: Initializing Socketify App")

    logger.info("🏗️ Step 1: Socketify App created successfully")

    # Simple route
    def health(res, req):
        logger.info("Health check requested")
        res.write_header("Content-Type", "application/json")
        res.end('{"status": "healthy", "message": "minimal test working"}')

    def home(res, req):
        logger.info("Home requested")
        res.end("Hello from minimal main_clean.py test!")

    # Register routes
    app.get("/health", health)
    app.get("/", home)

    logger.info("🏗️ FINISH: Socketify application created")
    return app

class MinimalServerRunner:
    def setup_signal_handlers(self):
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run_server(self):
        try:
            self.setup_signal_handlers()

            logger.info("🚀 Creating app...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            app = loop.run_until_complete(create_test_app())
            port = settings.api.port

            def on_listen(cfg):
                logger.info(f"Server listening on port {cfg.port}")

            try:
                logger.info(f"Binding to port: {port}")
                listen_result = app.listen(port, on_listen)

                if inspect.isawaitable(listen_result):
                    loop.run_until_complete(listen_result)

                logger.info("Running socketify loop...")
                app.run()

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt")
            except Exception as e:
                logger.error(f"Server error: {e}")
                raise

        except Exception as e:
            logger.error(f"Runner error: {e}")
            raise

if __name__ == "__main__":
    MinimalServerRunner().run_server()