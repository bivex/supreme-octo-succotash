"""Main application entry point."""

# uvloop not available on Windows, skipping (would give +20-40% HTTP performance boost on Linux/macOS)

import socketify
from loguru import logger
import json
import os

from .config.settings import settings
from .container import container


def create_app() -> socketify.App:
    """Create and configure socketify application with maximum performance settings."""
    # Create app with basic configuration
    app = socketify.App()

    # Set uWebSockets environment variables for maximum performance
    os.environ.setdefault('UWS_MAX_HEADER_SIZE', '32768')
    os.environ.setdefault('UWS_THREAD_AFFINITY', '1')
    os.environ.setdefault('UWS_SSL_FAST_PATH', '1')

    _configure_socketify_app(app)
    _configure_logging(app)
    _apply_middleware(app)
    _register_routes(app)
    _register_error_handlers(app)
    _add_health_endpoints(app)

    return app


def _configure_socketify_app(app: socketify.App) -> None:
    """Configure socketify application settings."""
    # Socketify doesn't have the same config system as Flask
    # JSON settings and other configurations will be handled in route handlers
    pass


def _configure_logging(app: socketify.App) -> None:
    """Configure logging for the application."""
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


def _register_routes(app: socketify.App) -> None:
    """Register application routes."""
    container.get_campaign_routes().register(app)
    container.get_click_routes().register(app)


def _register_error_handlers(app: socketify.App) -> None:
    """Register error handlers."""
    from .presentation.error_handlers import register_error_handlers
    register_error_handlers(app)


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
        """Reset mock storage for testing."""
        container.get_campaign_repository().__init__()
        container.get_click_repository().__init__()
        res.write_header("Content-Type", "application/json")
        res.end(json.dumps({"message": "Mock storage reset"}))

    # Register the routes
    app.get("/v1/health", health)
    app.post("/v1/reset", reset)


def _apply_middleware(app: socketify.App) -> None:
    """Apply middleware to the application."""
    from .presentation.middleware.security_middleware import setup_security_middleware
    setup_security_middleware(app)


def _add_cors_headers(app: socketify.App) -> None:
    """Add CORS headers to all responses."""
    # CORS and security headers will be handled by middleware
    # This is now done in the security middleware setup
    pass




if __name__ == "__main__":
    import multiprocessing

    app = create_app()

    # Maximum performance listen options
    listen_options = socketify.AppListenOptions(
        port=settings.api.port,
        host=settings.api.host,
        reuse_port=True,                    # Enable SO_REUSEPORT for multi-process scaling
        compression=socketify.CompressOptions.DISABLED,  # Disable expensive compression
        max_backlog=16384,                  # Huge connection backlog for request spikes
        idle_timeout=0,                     # Don't disconnect idle clients
    )

    logger.info(f"Starting high-performance server on {settings.api.host}:{settings.api.port}...")

    def on_listen(config):
        logger.info(f"🚀 Server listening on {config.host}:{config.port} with maximum performance settings")
        logger.info("✅ Compression: DISABLED | Backlog: 16384 | Idle timeout: NONE | Reuse port: ENABLED")

    # For true multi-CPU scaling, spawn multiple processes
    num_processes = settings.api.workers or multiprocessing.cpu_count()

    if num_processes > 1:
        logger.info(f"🔥 Spawning {num_processes} processes for maximum CPU utilization...")

        def run_worker():
            worker_app = create_app()
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
        app.listen(listen_options, on_listen)
        logger.info("🎯 Single-process mode. For maximum performance, set WORKERS environment variable.")
        app.run()
