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

    def on_listen(cfg):
        logger.info(f"Server listening on port {cfg.port}")

    app.listen(port, on_listen)

    app.run()
