#!/usr/bin/env python3
"""
Clean Architecture Affiliate Marketing API Server
"""

import sys
import os
import argparse
from src.main import create_app
from src.config.settings import settings
from loguru import logger

def run_server():
    """Run the server normally."""
    app = create_app()

    port = settings.api.port

    # Determine database driver information and test PostgreSQL connectivity
    db_driver_info = "SQLite (primary) + PostgreSQL"

    # Test PostgreSQL connectivity on startup
    try:
        from src.infrastructure.repositories.postgres_ltv_repository import PostgresLTVRepository
        postgres_repo = PostgresLTVRepository()
        db_driver_info += " - PostgreSQL: ✅ Connected"
        logger.info(f"Database driver: {db_driver_info}")
    except Exception as e:
        db_driver_info += f" - PostgreSQL: ❌ Connection failed ({str(e)[:50]}...)"
        logger.warning(f"Database driver: {db_driver_info}")
        logger.warning("PostgreSQL features will not be available")

    def on_listen(cfg):
        logger.info(f"Server listening on port {cfg.port}")

    app.listen(port, on_listen)

    app.run()

def run_with_reload():
    """Run server with hot reload using watchdog."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        import subprocess
        import signal
        import time
    except ImportError:
        logger.error("watchdog not installed. Install with: pip install watchdog")
        logger.info("Falling back to normal run mode")
        run_server()
        return

    class ReloadHandler(FileSystemEventHandler):
        def __init__(self):
            self.process = None
            self.restart_server()

        def restart_server(self):
            if self.process:
                logger.info("Stopping current server process...")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Force killing server process...")
                    self.process.kill()

            logger.info("Starting new server process...")
            self.process = subprocess.Popen([sys.executable, __file__, '--no-reload'])

        def on_modified(self, event):
            if event.src_path.endswith('.py') and not event.src_path.endswith('__pycache__'):
                logger.info(f"File changed: {event.src_path}")
                self.restart_server()

    # Watch current directory and src directory
    observer = Observer()
    handler = ReloadHandler()

    # Watch src directory
    observer.schedule(handler, path='./src', recursive=True)
    observer.schedule(handler, path='./main_clean.py', recursive=False)

    logger.info("Hot reload enabled. Watching for file changes...")

    try:
        observer.start()
        # Keep the observer running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping hot reload...")
        observer.stop()
        if handler.process:
            handler.process.terminate()
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean Architecture API Server')
    parser.add_argument('--reload', action='store_true', help='Enable hot reload')
    parser.add_argument('--no-reload', action='store_true', help='Internal flag for reload subprocess')

    args = parser.parse_args()

    if args.no_reload:
        # This is a subprocess started by reload handler
        run_server()
    elif args.reload:
        # Start with hot reload
        run_with_reload()
    else:
        # Normal run
        run_server()
