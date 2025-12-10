#!/usr/bin/env python3
"""
Clean Architecture Affiliate Marketing API Server
"""

import sys
import os
import argparse
import signal
import threading
import time
from src.main import create_app
from src.config.settings import settings
from src.container import container
from loguru import logger

# Global list to track background threads for cleanup
background_threads = []

def cleanup_background_threads():
    """Clean up background threads and services on shutdown."""
    logger.info("Cleaning up background threads and services...")

    try:
        # Stop postgres upholder
        upholder = container.get_postgres_upholder()
        if hasattr(upholder, 'stop'):
            logger.info("Stopping postgres upholder...")
            upholder.stop()
    except Exception as e:
        logger.error(f"Error stopping postgres upholder: {e}")

    try:
        # Stop cache monitor
        cache_monitor = container.get_postgres_cache_monitor()
        if hasattr(cache_monitor, 'stop_monitoring'):
            logger.info("Stopping cache monitor...")
            cache_monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Error stopping cache monitor: {e}")

    # Wait for threads to finish
    for thread in background_threads[:]:  # Copy list to avoid modification during iteration
        if thread.is_alive():
            logger.info(f"Waiting for thread {thread.name} to finish...")
            thread.join(timeout=5.0)
            if thread.is_alive():
                logger.warning(f"Thread {thread.name} did not finish gracefully")

    # Clear the list
    background_threads.clear()

    # Close database connections
    try:
        logger.info("Closing database connections...")
        pool = container.get_db_connection_pool()
        if hasattr(pool, '_closeall'):
            pool._closeall()
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    cleanup_background_threads()
    sys.exit(0)

def run_server():
    """Run the server normally."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = create_app()

    port = settings.api.port

    # Determine database driver information and test PostgreSQL connectivity
    # Test PostgreSQL connectivity and determine which driver to use
    try:
        import psycopg2
        # Simple connection test
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="supreme_octosuccotash_db",
            user="app_user",
            password="app_password",
            connect_timeout=5
        )
        conn.close()
        db_driver_info = "PostgreSQL"
        logger.info(f"Database driver: {db_driver_info}")
    except Exception as e:
        db_driver_info = "SQLite (PostgreSQL unavailable)"
        logger.warning(f"Database driver: {db_driver_info}")
        logger.warning(f"PostgreSQL connection failed: {str(e)[:50]}...")

    # Start background services and track their threads
    try:
        logger.info("Starting background services...")

        # Start postgres upholder
        upholder = container.get_postgres_upholder()
        if hasattr(upholder, 'start'):
            upholder.start()
            # Track the upholder thread
            if hasattr(upholder, '_scheduler_thread') and upholder._scheduler_thread:
                background_threads.append(upholder._scheduler_thread)

        # Start cache monitor
        cache_monitor = container.get_postgres_cache_monitor()
        cache_monitor.start_monitoring(interval_seconds=30)
        # Track the monitor thread
        if hasattr(cache_monitor, 'monitor_thread') and cache_monitor.monitor_thread:
            background_threads.append(cache_monitor.monitor_thread)

        logger.info(f"Started {len(background_threads)} background threads")

    except Exception as e:
        logger.error(f"Error starting background services: {e}")

    def on_listen(cfg):
        logger.info(f"Server listening on port {cfg.port}")

    try:
        app.listen(port, on_listen)
        app.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Ensure cleanup happens even if app.run() fails
        cleanup_background_threads()

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
