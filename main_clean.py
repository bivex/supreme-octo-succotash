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
import weakref
import inspect
import asyncio
from contextlib import contextmanager

# Async trace import (optional)
try:
    import async_trace
    ASYNC_TRACE_AVAILABLE = True
except ImportError:
    ASYNC_TRACE_AVAILABLE = False
from typing import Optional

from loguru import logger

# Register psycopg2 adapters for value objects
try:
    import psycopg2.extensions
    from src.domain.value_objects import CampaignId

    def adapt_campaign_id(campaign_id):
        return psycopg2.extensions.adapt(campaign_id.value)

    psycopg2.extensions.register_adapter(CampaignId, adapt_campaign_id)
    logger.info("Registered psycopg2 adapter for CampaignId")
except ImportError:
    logger.warning("psycopg2 not available for adapter registration")

from src.config.settings import load_settings
settings = load_settings()
from src.container import container
from src.main import create_app


# Global registry to prevent conflicts between multiple managers
_active_managers = weakref.WeakSet()


class BackgroundServiceManager:
    """Manages background services and their cleanup."""

    def __init__(self):
        self._threads: list[threading.Thread] = []
        self._services = []
        self._service_lock = threading.RLock()  # Синхронизация для доступа к сервисам
        self._is_primary_manager = False  # Only primary manager handles global services

        # Register this manager
        if not _active_managers:
            self._is_primary_manager = True
        _active_managers.add(self)

    def __del__(self):
        """Cleanup when manager is destroyed."""
        try:
            _active_managers.discard(self)
        except:
            pass  # Ignore errors during cleanup

    def add_thread(self, thread: threading.Thread) -> None:
        """Add a thread to be tracked for cleanup."""
        if thread and thread.is_alive():
            self._threads.append(thread)

    def start_postgres_upholder(self) -> None:
        """Start the PostgreSQL connection upholder service."""
        with self._service_lock:
            try:
                def _resolve_awaitable(maybe_awaitable):
                    """Resolve coroutine to a concrete object for sync contexts."""
                    if not inspect.isawaitable(maybe_awaitable):
                        return maybe_awaitable
                    try:
                        return asyncio.run(maybe_awaitable)
                    except RuntimeError:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            temp_loop = asyncio.new_event_loop()
                            try:
                                return temp_loop.run_until_complete(maybe_awaitable)
                            finally:
                                temp_loop.close()
                        return loop.run_until_complete(maybe_awaitable)
                    except Exception as e:
                        logger.error(f"Failed to resolve awaitable: {e}")
                        return maybe_awaitable

                # Check if already started by this manager
                if any(name == 'postgres_upholder' for name, _ in self._services):
                    logger.info("PostgreSQL upholder already started by this manager")
                    return

                # Only primary manager starts global services
                if not self._is_primary_manager:
                    logger.info("Skipping postgres upholder start - not primary manager")
                    return

                upholder_factory = container.get_postgres_upholder
                if inspect.iscoroutinefunction(upholder_factory):
                    upholder = asyncio.run(upholder_factory())
                else:
                    upholder = upholder_factory()
                upholder = _resolve_awaitable(upholder)
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
        with self._service_lock:
            try:
                # Check if already started by this manager
                if any(name == 'cache_monitor' for name, _ in self._services):
                    logger.info("Cache monitor already started by this manager")
                    return

                # Only primary manager starts global services
                if not self._is_primary_manager:
                    logger.info("Skipping cache monitor start - not primary manager")
                    return

                cache_monitor_factory = container.get_postgres_cache_monitor
                if inspect.iscoroutinefunction(cache_monitor_factory):
                    cache_monitor = asyncio.run(cache_monitor_factory())
                else:
                    cache_monitor = cache_monitor_factory()
                cache_monitor = _resolve_awaitable(cache_monitor)
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
        with self._service_lock:
            logger.info(f"Stopping background services (managing {len(self._services)} services)...")

            # Stop services in reverse order
            for service_name, service in reversed(self._services):
                try:
                    # More robust service stopping logic
                    if hasattr(service, 'stop') and callable(getattr(service, 'stop')):
                        logger.info(f"Stopping service '{service_name}' via stop()...")
                        service.stop()
                    elif hasattr(service, 'stop_monitoring') and callable(getattr(service, 'stop_monitoring')):
                        logger.info(f"Stopping service '{service_name}' via stop_monitoring()...")
                        service.stop_monitoring()
                    else:
                        logger.warning(f"Service '{service_name}' ({type(service).__name__}) has no known stop method")
                except Exception as e:
                    logger.error(f"Error stopping {service_name} ({type(service).__name__}): {e}")

            # Clear services list after stopping
            stopped_services = len(self._services)
            self._services.clear()

            # Wait for threads to finish
            if self._threads:
                logger.info(f"Waiting for {len(self._threads)} threads to finish...")
                self._wait_for_threads()
                self._threads.clear()  # Clear after waiting

            # Close database connections
            self._close_database_connections()

            logger.info(f"All background services stopped (stopped {stopped_services} services)")

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
        with self._service_lock:
            try:
                logger.info("Closing database connections...")
                pool = container.get_db_connection_pool_sync()
                if pool and hasattr(pool, '_closeall'):
                    pool._closeall()
                    logger.info("Database connections closed successfully")
            except Exception as e:
                logger.error(f"Error closing database connections: {e}")


class DatabaseConnectionTester:
    """Tests database connectivity using connection pool and determines driver information."""

    def __init__(self, container_instance):
        """Initialize with container instance for thread-safe connection testing."""
        self.container = container_instance
        self._connection_lock = threading.RLock()  # Reentrant lock for connection testing and container access
        self._container_lock = threading.RLock()   # Separate lock for container operations

    def test_postgresql_connection(self) -> tuple[bool, str]:
        """Test PostgreSQL connection using connection pool with thread safety."""
        with self._connection_lock:
            try:
                import psycopg2

                # Use connection pool from container with thread-safe access (sync)
                with self._container_lock:
                    pool = self.container.get_db_connection_pool_sync()
                    if pool is None:
                        # Create pool synchronously as a fallback
                        conn = self.container.get_db_connection()
                        pool = self.container.get_db_connection_pool_sync()
                        if conn and pool:
                            pool.putconn(conn)
                conn = None

                try:
                    # Get connection from pool with timeout
                    conn = pool.getconn()

                    # Test connection with simple query
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()

                        if result and result[0] == 1:
                            return True, "PostgreSQL"
                        else:
                            return False, "SQLite (PostgreSQL test query failed)"

                finally:
                    # Always return connection to pool
                    if conn:
                        pool.putconn(conn)

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
        self.db_tester = DatabaseConnectionTester(container)

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")

            # Save trace before shutdown if async-trace is enabled
            try:
                from src.utils.async_debug import save_debug_snapshot
                signal_trace = save_debug_snapshot(f"signal_shutdown_sig{signum}")
                logger.info(f"📸 Signal shutdown trace saved: {signal_trace}")
            except Exception as e:
                logger.error(f"Failed to save signal trace: {e}")

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
            # self.service_manager.start_postgres_upholder()
            # self.service_manager.start_cache_monitor()

            yield
        finally:
            self.service_manager.stop_all_services()

    def run_server(self) -> None:
        """Run the server with full lifecycle management (sync entrypoint)."""
        try:
            from src.utils.async_debug import debug_async_trace
            debug_async_trace("Starting server runner")
        except ImportError:
            pass

        self.setup_signal_handlers()

        logger.info("🚀 Creating app...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # create_app is async; run it once on the current loop (do not close it)
        app = loop.run_until_complete(create_app())
        port = settings.api.port

        def on_listen(cfg):
            logger.info(f"Server listening on port {cfg.port}")

        try:
            with self.managed_services():
                # Create listen options to bind to 0.0.0.0
                import socketify
                listen_options = socketify.AppListenOptions(
                    host="0.0.0.0",
                    port=port
                )
                logger.info(f"Binding to host: {listen_options.host}, port: {listen_options.port}")
                listen_result = app.listen(listen_options, on_listen)
                # app.listen may be sync; if it returns awaitable, wait for it on the same loop
                if inspect.isawaitable(listen_result):
                    loop.run_until_complete(listen_result)

                # Run socketify loop in the main thread (blocking)
                app.run()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
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
            import asyncio # Import asyncio here

            self.FileSystemEventHandler = FileSystemEventHandler
            self.subprocess = subprocess
            self.script_path = script_path
            self.process: Optional[subprocess.Popen] = None
            asyncio.run(self.restart_server()) # Run restart_server as async

        async def restart_server(self) -> None:
            """Restart the server process (async)."""
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
                import asyncio
                asyncio.run(self.restart_server())

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


def main_async(): # Now synchronous wrapper, keeps arg parsing logic
    """Main entry point for the application (sync wrapper)."""
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
    parser.add_argument(
        '--async-trace',
        action='store_true',
        help='Enable async-trace for debugging asyncio tasks'
    )

    args = parser.parse_args()

    # Enable async tracing if requested and available
    if args.async_trace:
        if ASYNC_TRACE_AVAILABLE:
            async_trace.enable_tracing()
            logger.info("🔍 Async-trace enabled for debugging asyncio tasks")

            # Import async debug utilities
            from src.utils.async_debug import save_debug_snapshot, log_trace_to_continuous_file

            # Save initial server startup trace if a loop is running
            try:
                asyncio.get_running_loop()
                startup_trace = save_debug_snapshot("server_startup")
                logger.info(f"📸 Server startup trace saved: {startup_trace}")
            except RuntimeError:
                logger.warning("Skipping startup trace: no running event loop at startup")

            # Setup automatic trace saving on shutdown
            import atexit
            def save_shutdown_trace():
                try:
                    shutdown_trace = save_debug_snapshot("server_shutdown")
                    logger.info(f"📸 Server shutdown trace saved: {shutdown_trace}")
                except Exception as e:
                    print(f"Error saving shutdown trace: {e}")

            atexit.register(save_shutdown_trace)

        else:
            logger.warning("⚠️  Async-trace requested but not available. Install with: pip install async-trace")

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
            ServerRunner().run_server() # fallback
    else:
        # Normal server run
        ServerRunner().run_server()


if __name__ == "__main__":
    main_async()
