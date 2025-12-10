#!/usr/bin/env python3
"""
Clean Architecture Affiliate Marketing API Server

A modular server application with background service management,
hot reload capabilities, and graceful shutdown handling.
"""

import argparse
import signal
import sys
import threading
import time
from contextlib import contextmanager
from typing import Optional

from loguru import logger

from src.config.settings import settings
from src.container import container
from src.main import create_app


class BackgroundServiceManager:
    """Manages background services and their cleanup."""

    def __init__(self):
        self._threads: list[threading.Thread] = []
        self._services = []

    def add_thread(self, thread: threading.Thread) -> None:
        """Add a thread to be tracked for cleanup."""
        if thread and thread.is_alive():
            self._threads.append(thread)

    def start_postgres_upholder(self) -> None:
        """Start the PostgreSQL connection upholder service."""
        try:
            upholder = container.get_postgres_upholder()
            if hasattr(upholder, 'start'):
                logger.info("Starting PostgreSQL upholder...")
                upholder.start()

                # Track the scheduler thread if it exists
                if hasattr(upholder, '_scheduler_thread') and upholder._scheduler_thread:
                    self.add_thread(upholder._scheduler_thread)
                    self._services.append(('postgres_upholder', upholder))

                logger.info("PostgreSQL upholder started successfully")
        except Exception as e:
            logger.error(f"Failed to start PostgreSQL upholder: {e}")

    def start_cache_monitor(self, interval_seconds: int = 30) -> None:
        """Start the cache monitoring service."""
        try:
            cache_monitor = container.get_postgres_cache_monitor()
            logger.info("Starting cache monitor...")
            cache_monitor.start_monitoring(interval_seconds=interval_seconds)

            # Track the monitor thread if it exists
            if hasattr(cache_monitor, 'monitor_thread') and cache_monitor.monitor_thread:
                self.add_thread(cache_monitor.monitor_thread)
                self._services.append(('cache_monitor', cache_monitor))

            logger.info("Cache monitor started successfully")
        except Exception as e:
            logger.error(f"Failed to start cache monitor: {e}")

    def stop_all_services(self) -> None:
        """Stop all background services gracefully."""
        logger.info("Stopping background services...")

        # Stop services in reverse order
        for service_name, service in reversed(self._services):
            try:
                if service_name == 'postgres_upholder' and hasattr(service, 'stop'):
                    logger.info("Stopping PostgreSQL upholder...")
                    service.stop()
                elif service_name == 'cache_monitor' and hasattr(service, 'stop_monitoring'):
                    logger.info("Stopping cache monitor...")
                    service.stop_monitoring()
            except Exception as e:
                logger.error(f"Error stopping {service_name}: {e}")

        # Wait for threads to finish
        self._wait_for_threads()

        # Close database connections
        self._close_database_connections()

        logger.info("All background services stopped")

    def _wait_for_threads(self) -> None:
        """Wait for all tracked threads to finish."""
        for thread in self._threads:
            if thread.is_alive():
                logger.info(f"Waiting for thread '{thread.name}' to finish...")
                thread.join(timeout=5.0)
                if thread.is_alive():
                    logger.warning(f"Thread '{thread.name}' did not finish gracefully")

    def _close_database_connections(self) -> None:
        """Close all database connections."""
        try:
            logger.info("Closing database connections...")
            pool = container.get_db_connection_pool()
            if hasattr(pool, '_closeall'):
                pool._closeall()
                logger.info("Database connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


class DatabaseConnectionTester:
    """Tests database connectivity and determines driver information."""

    @staticmethod
    def test_postgresql_connection() -> tuple[bool, str]:
        """Test PostgreSQL connection and return (is_connected, driver_info)."""
        try:
            import psycopg2

            # Use configuration settings instead of hardcoded values
            conn_params = {
                'host': getattr(settings.database, 'host', 'localhost'),
                'port': getattr(settings.database, 'port', 5432),
                'database': getattr(settings.database, 'name', 'supreme_octosuccotash_db'),
                'user': getattr(settings.database, 'user', 'app_user'),
                'password': getattr(settings.database, 'password', 'app_password'),
                'connect_timeout': 5
            }

            with psycopg2.connect(**conn_params) as conn:
                return True, "PostgreSQL"

        except ImportError:
            logger.warning("psycopg2 not available, falling back to SQLite")
            return False, "SQLite (psycopg2 not installed)"
        except Exception as e:
            error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
            logger.warning(f"PostgreSQL connection failed: {error_msg}")
            return False, "SQLite (PostgreSQL unavailable)"

    @staticmethod
    def log_database_info(driver_info: str) -> None:
        """Log database driver information."""
        logger.info(f"Database driver: {driver_info}")


class ServerRunner:
    """Handles server execution with proper lifecycle management."""

    def __init__(self):
        self.service_manager = BackgroundServiceManager()
        self.db_tester = DatabaseConnectionTester()

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.service_manager.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @contextmanager
    def managed_services(self):
        """Context manager for starting and stopping services."""
        try:
            # Test database connection
            is_connected, driver_info = self.db_tester.test_postgresql_connection()
            self.db_tester.log_database_info(driver_info)

            # Start background services
            self.service_manager.start_postgres_upholder()
            self.service_manager.start_cache_monitor()

            yield
        finally:
            self.service_manager.stop_all_services()

    def run_server(self) -> None:
        """Run the server with full lifecycle management."""
        self.setup_signal_handlers()

        app = create_app()
        port = settings.api.port

        def on_listen(cfg):
            logger.info(f"Server listening on port {cfg.port}")

        try:
            with self.managed_services():
                app.listen(port, on_listen)
                app.run()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


class HotReloadManager:
    """Manages hot reloading functionality using watchdog."""

    def __init__(self):
        self._check_watchdog_availability()

    def _check_watchdog_availability(self) -> None:
        """Check if watchdog is available, raise ImportError if not."""
        try:
            import watchdog  # noqa: F401
        except ImportError:
            raise ImportError(
                "watchdog not installed. Install with: pip install watchdog"
            )

    class ReloadHandler:
        """Handles file change events for hot reloading."""

        def __init__(self, script_path: str):
            from watchdog.events import FileSystemEventHandler
            import subprocess

            self.FileSystemEventHandler = FileSystemEventHandler
            self.subprocess = subprocess
            self.script_path = script_path
            self.process: Optional[subprocess.Popen] = None
            self.restart_server()

        def restart_server(self) -> None:
            """Restart the server process."""
            if self.process:
                logger.info("Stopping current server process...")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except self.subprocess.TimeoutExpired:
                    logger.warning("Force killing server process...")
                    self.process.kill()

            logger.info("Starting new server process...")
            self.process = self.subprocess.Popen([
                sys.executable, self.script_path, '--no-reload'
            ])

        def on_modified(self, event) -> None:
            """Handle file modification events."""
            if (event.src_path.endswith('.py') and
                not event.src_path.endswith(('__pycache__', '__init__.py'))):
                logger.info(f"File changed: {event.src_path}")
                self.restart_server()

    def run_with_reload(self, script_path: str) -> None:
        """Run server with hot reload watching for file changes."""
        from watchdog.observers import Observer

        observer = Observer()
        handler = self.ReloadHandler(script_path)

        # Watch directories for changes
        observer.schedule(handler, path='./src', recursive=True)
        observer.schedule(handler, path=script_path, recursive=False)

        logger.info("Hot reload enabled. Watching for file changes...")

        try:
            observer.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping hot reload...")
            observer.stop()
            if handler.process:
                handler.process.terminate()
        finally:
            observer.join()


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Clean Architecture Affiliate Marketing API Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run server normally
  %(prog)s --reload          # Run with hot reload
        """
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable hot reload for development'
    )
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='Internal flag for reload subprocess (do not use manually)'
    )

    args = parser.parse_args()

    if args.no_reload:
        # This is a subprocess started by the reload handler
        ServerRunner().run_server()
    elif args.reload:
        # Start with hot reload
        try:
            reload_manager = HotReloadManager()
            reload_manager.run_with_reload(__file__)
        except ImportError as e:
            logger.error(str(e))
            logger.info("Falling back to normal run mode")
            ServerRunner().run_server()
    else:
        # Normal server run
        ServerRunner().run_server()


if __name__ == "__main__":
    main()
