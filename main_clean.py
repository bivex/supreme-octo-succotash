#!/usr/bin/env python3
"""
Clean Architecture Affiliate Marketing API Server
"""

from src.main import create_app
from src.config.settings import settings  
from loguru import logger

if __name__ == "__main__":
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
