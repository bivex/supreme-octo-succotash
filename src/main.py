"""Main application entry point."""

# uvloop not available on Windows, skipping (would give +20-40% HTTP performance boost on Linux/macOS)

import socketify
from loguru import logger
import json
import os
import time
from decimal import Decimal

from .config.settings import settings
from .container import container

# Custom JSON encoder for Decimal objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Monkey patch json.dumps to handle Decimal objects
_original_dumps = json.dumps
def custom_dumps(obj, **kwargs):
    """Custom json.dumps that handles Decimal objects."""
    # If cls is already specified, don't override it
    if 'cls' not in kwargs:
        kwargs['cls'] = CustomJSONEncoder
    return _original_dumps(obj, **kwargs)

json.dumps = custom_dumps


async def create_app() -> socketify.App:
    """Create and configure socketify application with maximum performance settings."""
    # Import async debug here to avoid circular imports
    try:
        from .utils.async_debug import debug_async_trace
        debug_async_trace("Starting Socketify application creation")
    except ImportError:
        pass

    logger.info("🏗️ START: Creating Socketify application")
    app_start = time.time()

    # Create app with basic configuration
    logger.info("🏗️ Step 1: Initializing Socketify App")
    app = socketify.App()
    logger.info("🏗️ Step 1: Socketify App created successfully")

    # Set uWebSockets environment variables for maximum performance
    os.environ.setdefault('UWS_MAX_HEADER_SIZE', '32768')
    os.environ.setdefault('UWS_THREAD_AFFINITY', '1')
    os.environ.setdefault('UWS_SSL_FAST_PATH', '1')

    _configure_socketify_app(app)
    _configure_logging(app)
    _setup_global_exception_handler()
    _apply_middleware(app)
    await _register_routes(app) # Await the async function
    _register_error_handlers(app)
    _add_health_endpoints(app)
    # _initialize_postgres_upholder(app) # Removed, will be called in background tasks

    app_time = time.time() - app_start
    logger.info(f"🏗️ FINISH: Socketify application created in {app_time:.4f} seconds")
    return app


def _configure_socketify_app(app: socketify.App) -> None:
    """Configure socketify application settings."""
    # Socketify doesn't have the same config system as Flask
    # JSON settings and other configurations will be handled in route handlers
    pass


def _configure_logging(app: socketify.App) -> None:
    """Configure logging for the application."""
    # Import async debug here to avoid circular imports
    try:
        from .utils.async_debug import debug_async_trace
        debug_async_trace("Configuring logging system")
    except ImportError:
        pass

    # Configure loguru with detailed format including file, line, function
    log_level = settings.logging.level.upper()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Remove all default handlers
    logger.remove()

    # Add console handler with stderr output
    # Add console handler with stderr output
    import sys
    logger.add(
        sink=sys.stderr,
        level=log_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # Add file handler for testing
    logger.add(
        "app.log",
        level=log_level,
        format=log_format,
        rotation="10 MB",
        retention="1 week",
        backtrace=True,
        diagnose=True
    )

    # Add file handler if configured
    if settings.logging.file_path:
        logger.add(
            settings.logging.file_path,
            level=log_level,
            format=log_format,
            rotation="10 MB",
            retention="1 week",
            backtrace=True,
            diagnose=True
        )

    # Test log message
    logger.info("Logging system initialized with loguru")


def _setup_global_exception_handler() -> None:
    """Setup global exception handler to catch all unhandled exceptions."""
    # Import async debug here to avoid circular imports
    try:
        from .utils.async_debug import debug_async_trace
        debug_async_trace("Setting up global exception handler")
    except ImportError:
        pass

    import sys
    import traceback
    import functools
    from decimal import Decimal

    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """Global exception handler that logs full traceback."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical("Unhandled exception occurred!")
        logger.critical(f"Exception type: {exc_type.__name__}")
        logger.critical(f"Exception message: {exc_value}")
        logger.critical("Full traceback:")
        logger.critical("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        # Save async trace if available
        try:
            from .utils.async_debug import save_debug_snapshot
            error_trace = save_debug_snapshot("unhandled_exception")
            logger.critical(f"📸 Unhandled exception trace saved: {error_trace}")
        except Exception as trace_error:
            logger.error(f"Failed to save exception trace: {trace_error}")

        # Also call the original exception handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Set the global exception handler
    sys.excepthook = global_exception_handler

    # Note: Custom JSON encoder is already set up globally at module level

    # Note: Exception handling is done in individual route handlers with try/catch blocks

    logger.info("Global exception handler configured (JSON encoder already set up) - Hot reload ready - Test change")


async def _register_routes(app: socketify.App) -> None:
    """Register application routes."""
    logger.info("🔌 Registering routes...")
    start = time.time()

    try:
        from .utils.async_debug import debug_async_trace, save_debug_snapshot
    except Exception:
        def debug_async_trace(msg: str = ""):
            return
        def save_debug_snapshot(reason: str = "debug"):
            return None

    steps = [
        ("campaign", container.get_campaign_routes),
        ("click", container.get_click_routes),
        ("webhook", container.get_webhook_routes),
        ("event", container.get_event_routes),
        ("conversion", container.get_conversion_routes),
        ("postback", container.get_postback_routes),
        ("click_generation", container.get_click_generation_routes),
        ("goal", container.get_goal_routes),
        ("journey", container.get_journey_routes),
        ("ltv", container.get_ltv_routes),
        ("form", container.get_form_routes),
        ("retention", container.get_retention_routes),
        ("bulk_operations", container.get_bulk_operations_routes),
        ("fraud", container.get_fraud_routes),
        ("system", container.get_system_routes),
        ("analytics", container.get_analytics_routes),
    ]

    try:
        for name, getter in steps:
            step_start = time.time()
            logger.info(f"🔌 Route step START: {name}")
            debug_async_trace(f"Before route step: {name}")
            routes = await getter()
            await routes.register(app)
            step_duration = time.time() - step_start
            logger.info(f"✅ Route step DONE: {name} in {step_duration:.3f}s")
            debug_async_trace(f"After route step: {name}")

        duration = time.time() - start
        logger.info(f"✅ Routes registered in {duration:.3f}s")
    except Exception as e:
        duration = time.time() - start
        logger.exception(f"❌ Route registration failed after {duration:.3f}s")
        try:
            snapshot = save_debug_snapshot(f"routes_error_{name}")
            if snapshot:
                logger.error(f"📸 Async snapshot saved: {snapshot}")
        except Exception:
            logger.error("Failed to save async snapshot for route error")
        raise


def _register_error_handlers(app: socketify.App) -> None:
    """Register error handlers for socketify."""
    # Global exception handler is already set up
    # Socketify handles errors differently - exceptions in route handlers
    # will be caught by the global exception handler
    logger.info("Error handlers configured (using global exception handler)")


async def _start_background_tasks(app: socketify.App):
    """Start background tasks like PostgreSQL upholder and cache monitoring."""
    import asyncio
    logger.info("🚀 Starting background tasks...")
    await _initialize_postgres_upholder(app) # Await here
    logger.info("✅ Background tasks started.")


def _add_health_endpoints(app: socketify.App) -> None:
    """Add health check and utility endpoints."""
    def health(res, req):
        """Health check endpoint."""
        import socket
        import os
        import time

        health_response = {
            "status": "healthy",
            "service": "affiliate-api",
            "version": "1.0.0",
            "environment": settings.environment,
            "instance": os.environ.get('FLASK_INSTANCE_ID', 'single'),
            "port": settings.api.port,
            "hostname": socket.gethostname(),
            "timestamp": time.time()
        }
        res.write_header("Content-Type", "application/json")
        # Add CORS headers for API endpoints
        res.write_header('Access-Control-Allow-Origin', '*')
        res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        res.write_header('Access-Control-Allow-Credentials', 'false')
        res.write_header('Access-Control-Max-Age', '86400')
        # Add security headers
        from .presentation.middleware.security_middleware import add_security_headers
        add_security_headers(res)
        res.end(json.dumps(health_response))

    def reset(res, req):
        """Reset application state for testing."""
        # Note: PostgreSQL repositories don't need explicit reset
        # as they work with the database directly
        res.write_header("Content-Type", "application/json")
        res.end(json.dumps({"message": "Application state reset"}))

    # Register the routes
    app.get("/v1/health", health)
    app.post("/v1/reset", reset)


async def _initialize_postgres_upholder(app: socketify.App) -> None: # Made async
    """Initialize PostgreSQL Auto Upholder system."""
    try:
        logger.info("🔧 Initializing PostgreSQL Auto Upholder...")

        # Get upholder instance from container
        upholder = await container.get_postgres_upholder() # Await here

        # Add custom alert handler that integrates with app logging
        def app_alert_handler(alert_type: str, message: str):
            if alert_type == "performance_alert":
                logger.warning(f"🚨 PostgreSQL Performance Alert: {message}")
            else:
                logger.info(f"📊 PostgreSQL Upholder: {alert_type} - {message}")

        upholder.add_alert_handler(app_alert_handler)

        # Start upholder monitoring
        upholder.start()
        logger.info("✅ PostgreSQL Auto Upholder started successfully")

        # Initialize vectorized cache monitor if performance mode is enabled
        import os
        if os.getenv('PERFORMANCE_MODE', 'false').lower() == 'true':
            try:
                logger.info("🚀 Initializing vectorized cache monitor...")
                vectorized_monitor = container.get_vectorized_cache_monitor()

                # Add alert handler for vectorized monitor
                def vectorized_alert_handler(alert):
                    logger.warning(f"🚨 Vectorized Cache Alert [{alert.severity.upper()}]: {alert.message}")
                    for rec in alert.recommendations:
                        logger.info(f"💡 Recommendation: {rec}")

                vectorized_monitor.add_alert_handler(vectorized_alert_handler)
                vectorized_monitor.start_monitoring()
                logger.info("✅ Vectorized cache monitor started successfully")

            except Exception as e:
                logger.error(f"❌ Failed to initialize vectorized cache monitor: {e}")

        # Add upholder management endpoints
        _add_upholder_endpoints(app, upholder)

    except Exception as e:
        logger.error(f"❌ Failed to initialize PostgreSQL Auto Upholder: {e}")
        # Don't fail app startup if upholder fails
        logger.warning("⚠️  Continuing without PostgreSQL optimization monitoring")


def _add_upholder_endpoints(app: socketify.App, upholder) -> None:
    """Add PostgreSQL upholder management endpoints."""

    async def get_upholder_status(res, req):
        """Get upholder status and recent reports."""
        logger.info("🚀 START: GET /v1/system/upholder/status")
        start_time = time.time()

        try:
            logger.info("📊 Step 1: Getting upholder status")
            status_start = time.time()
            status = upholder.get_status()
            status_time = time.time() - status_start
            logger.info("📊 Step 2: Getting performance dashboard (async)")
            dashboard_start = time.time()

            # Run blocking database operations in thread pool to avoid blocking the event loop
            import asyncio
            loop = asyncio.get_event_loop()
            dashboard = await asyncio.wait_for(
                loop.run_in_executor(None, upholder.get_performance_dashboard),
                timeout=30.0  # 30 second timeout
            )
            dashboard_time = time.time() - dashboard_start
            logger.info("📊 Step 3: Preparing response")
            response = {
                "upholder_status": status,
                "performance_dashboard": dashboard
            }

            logger.info("📊 Step 4: Setting response headers")
            res.write_header("Content-Type", "application/json")
            res.write_header('Access-Control-Allow-Origin', '*')
            res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
            res.write_header('Access-Control-Allow-Credentials', 'false')
            res.write_header('Access-Control-Max-Age', '86400')

            logger.info("📊 Step 5: Adding security headers")
            from .presentation.middleware.security_middleware import add_security_headers
            add_security_headers(res)

            logger.info("📊 Step 6: Serializing response")
            response_json = json.dumps(response, default=str)

            logger.info("📊 Step 7: Sending response")
            res.end(response_json)

            total_time = time.time() - start_time
        except Exception as e:
            logger.error(f"❌ ERROR in get_upholder_status: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            res.write_status(500)
            res.write_header("Content-Type", "application/json")
            res.end(json.dumps({"error": str(e)}))

    def run_upholder_audit(res, req):
        """Run immediate upholder audit."""
        try:
            logger.info("🔍 Running manual PostgreSQL audit...")
            report = upholder.run_full_audit()

            response = {
                "audit_completed": True,
                "duration_seconds": report.duration_seconds,
                "optimizations_applied": report.optimizations_applied,
                "alerts_generated": report.alerts_generated,
                "recommendations_pending": report.recommendations_pending,
                "performance_improvements": report.performance_improvements
            }

            logger.info(f"✅ Manual audit completed in {report.duration_seconds:.2f}s")
            res.write_header("Content-Type", "application/json")
            res.write_header('Access-Control-Allow-Origin', '*')
            res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
            res.write_header('Access-Control-Allow-Credentials', 'false')
            res.write_header('Access-Control-Max-Age', '86400')
            # Add security headers
            from .presentation.middleware.security_middleware import add_security_headers
            add_security_headers(res)
            res.end(json.dumps(response, default=str))

        except Exception as e:
            logger.error(f"Error running upholder audit: {e}")
            res.write_status(500)
            res.write_header("Content-Type", "application/json")
            res.end(json.dumps({"error": str(e)}))

    def get_upholder_config(res, req):
        """Get upholder configuration."""
        try:
            status = upholder.get_status()
            config = status.get('config', {})

            res.write_header("Content-Type", "application/json")
            res.write_header('Access-Control-Allow-Origin', '*')
            res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
            res.write_header('Access-Control-Allow-Credentials', 'false')
            res.write_header('Access-Control-Max-Age', '86400')
            # Add security headers
            from .presentation.middleware.security_middleware import add_security_headers
            add_security_headers(res)
            res.end(json.dumps(config))

        except Exception as e:
            logger.error(f"Error getting upholder config: {e}")
            res.write_status(500)
            res.write_header("Content-Type", "application/json")
            res.end(json.dumps({"error": str(e)}))

    def get_connection_pool_status(res, req):
        """Get connection pool status."""
        logger.info("🏊 START: GET /v1/system/upholder/connection-pool/status")
        pool_start = time.time()

        try:
            print("DEBUG: Connection pool status handler called")
            logger.info("🏊 Step 1: Getting pool status from monitor")
            monitor_start = time.time()
            pool_status = upholder.connection_pool_monitor.get_pool_status()
            monitor_time = time.time() - monitor_start
            logger.info("🏊 Step 2: Setting response headers")
            res.write_header("Content-Type", "application/json")
            res.write_header('Access-Control-Allow-Origin', '*')
            res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
            res.write_header('Access-Control-Allow-Credentials', 'false')
            res.write_header('Access-Control-Max-Age', '86400')

            logger.info("🏊 Step 3: Adding security headers")
            from .presentation.middleware.security_middleware import add_security_headers
            add_security_headers(res)

            logger.info("🏊 Step 4: Serializing and sending response")
            response_json = json.dumps(pool_status, default=str)
            res.end(response_json)

            total_time = time.time() - pool_start
        except Exception as e:
            logger.error(f"❌ ERROR in get_connection_pool_status: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            res.write_status(500)
            res.write_header("Content-Type", "application/json")
            res.end(json.dumps({"error": str(e)}))

    def get_connection_pool_suggestions(res, req):
        """Get connection pool optimization suggestions."""
        try:
            suggestions = upholder.connection_pool_monitor.get_optimization_suggestions()

            res.write_header("Content-Type", "application/json")
            res.write_header('Access-Control-Allow-Origin', '*')
            res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
            res.write_header('Access-Control-Allow-Credentials', 'false')
            res.write_header('Access-Control-Max-Age', '86400')
            # Add security headers
            from .presentation.middleware.security_middleware import add_security_headers
            add_security_headers(res)
            res.end(json.dumps(suggestions, default=str))

        except Exception as e:
            logger.error(f"Error getting connection pool suggestions: {e}")
            res.write_status(500)
            res.write_header("Content-Type", "application/json")
            res.end(json.dumps({"error": str(e)}))

    def apply_connection_pool_optimization(res, req):
        """Apply connection pool optimization."""
        try:
            # Get action from query parameter
            action = req.get_query('action')
            if not action:
                res.write_status(400)
                res.write_header("Content-Type", "application/json")
                res.end(json.dumps({"error": "action parameter required"}))
                return

            dry_run = req.get_query('dry_run') != 'false'  # Default to true

            result = upholder.connection_pool_monitor.apply_optimization(action, dry_run=dry_run)

            res.write_header("Content-Type", "application/json")
            res.write_header('Access-Control-Allow-Origin', '*')
            res.write_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            res.write_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
            res.write_header('Access-Control-Allow-Credentials', 'false')
            res.write_header('Access-Control-Max-Age', '86400')
            # Add security headers
            from .presentation.middleware.security_middleware import add_security_headers
            add_security_headers(res)
            res.end(json.dumps(result, default=str))

        except Exception as e:
            logger.error(f"Error applying connection pool optimization: {e}")
            res.write_status(500)
            res.write_header("Content-Type", "application/json")
            res.end(json.dumps({"error": str(e)}))

    # Register endpoints
    app.get('/v1/system/upholder/status', get_upholder_status)
    app.post('/v1/system/upholder/audit', run_upholder_audit)
    app.get('/v1/system/upholder/config', get_upholder_config)

    # Connection pool specific endpoints
    app.get('/v1/system/upholder/connection-pool/status', get_connection_pool_status)
    app.get('/v1/system/upholder/connection-pool/suggestions', get_connection_pool_suggestions)
    app.post('/v1/system/upholder/connection-pool/optimize', apply_connection_pool_optimization)

    logger.info("📊 PostgreSQL upholder endpoints registered: /v1/system/upholder/*")


def _apply_middleware(app: socketify.App) -> None:
    """Apply middleware to the application."""
    # Import async debug here to avoid circular imports
    try:
        from .utils.async_debug import debug_async_trace
        debug_async_trace("Applying middleware to application")
    except ImportError:
        pass

    from .presentation.middleware.security_middleware import setup_security_middleware
    setup_security_middleware(app)


def _add_cors_headers(app: socketify.App) -> None:
    """Add CORS headers to all responses."""
    # CORS and security headers will be handled by middleware
    # This is now done in the security middleware setup
    pass




if __name__ == "__main__":
    logger.info("🚀 START: Application main execution")
    main_start = time.time()

    import multiprocessing
    import asyncio # Import asyncio here if not already imported

    async def start_server():
        logger.info("🏗️ Creating application (async)...")
        app = await create_app() # Await the async create_app
        app_create_time = time.time() - main_start
        logger.info(f"🏗️ Application created in {app_create_time:.4f} seconds")

        # Compatible listen options for current socketify version
        listen_options = socketify.AppListenOptions(
            port=settings.api.port,
            host=settings.api.host,
        )

        logger.info(f"🏁 Starting high-performance server on {settings.api.host}:{settings.api.port}...")
        server_setup_time = time.time() - main_start

        def on_listen(config):
            total_startup_time = time.time() - main_start
            logger.info(f"🚀 Server listening on {config.host}:{config.port} with maximum performance settings")
            logger.info("✅ Compression: DISABLED | Backlog: 16384 | Idle timeout: NONE | Reuse port: ENABLED")
            # Removed duplicated log line

        # For true multi-CPU scaling, spawn multiple processes
        num_processes = settings.api.workers or multiprocessing.cpu_count()

        if num_processes > 1:
            logger.info(f"🔥 Spawning {num_processes} processes for maximum CPU utilization...")

            def run_worker():
                # Each worker needs its own app instance and event loop
                worker_app = asyncio.run(create_app()) # Run create_app in new event loop for worker
                # Initialize background tasks for each worker as well
                asyncio.run(_start_background_tasks(worker_app))
                worker_app.listen(listen_options, on_listen)
                worker_app.run()

            processes = []
            for i in range(num_processes):
                process = multiprocessing.Process(
                    target=run_worker,
                    name=f"Socketify-Worker-{i+1}",
                    daemon=True
                )
                process.start()
                processes.append(process)

            try:
                logger.info("🎯 All workers started! Server ready for maximum throughput.")
                # Start background tasks in the main process (only once)
                await _start_background_tasks(app) # Await the background tasks

                for process in processes:
                    process.join()
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down workers...")
                for process in processes:
                    process.terminate()
                for process in processes:
                    process.join()
        else:
            # Single process mode
            # Start background tasks in the single process
            await _start_background_tasks(app) # Await here
            
            app.listen(listen_options, on_listen)
            logger.info("🎯 Single-process mode. For maximum performance, set WORKERS environment variable.")
            app.run()

    asyncio.run(start_server()) # Run the async server startup
