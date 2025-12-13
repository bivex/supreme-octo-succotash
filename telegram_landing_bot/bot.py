#!/usr/bin/env python3
"""
Main file for Telegram bot tracking clicks to landing pages
Uses aiogram 3.x and integrates with Supreme Tracker
"""

import asyncio
import signal
import sys
import argparse
import os
from typing import Optional

# Add project root to sys.path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from loguru import logger

from config import settings
from handlers import router, handle_conversion_webhook, handle_click_webhook
from tracking import init_tracking, close_tracking


class LandingBot:
    """Main bot class"""

    def __init__(self):
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.webhook_app: Optional[FastAPI] = None

    async def setup_bot(self):
        """Set up bot and dispatcher"""

        # Create bot instance
        self.bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        # Create dispatcher
        self.dp = Dispatcher()

        # Register router with handlers
        self.dp.include_router(router)

        # Configure logging
        logger.add(
            "logs/bot.log",
            rotation="1 day",
            retention="7 days",
            level=settings.log_level
        )

        logger.info("Bot setup completed")

    def setup_webhook_app(self, webhook_path: str = "/webhook"):
        """Set up FastAPI app for webhook handling"""

        if not self.bot or not self.dp:
            raise RuntimeError("Bot not initialized. Call setup_bot() first.")

        self.webhook_app = FastAPI(title="Telegram Bot Webhook")

        @self.webhook_app.post(webhook_path)
        async def telegram_webhook(request: Request):
            """Handle Telegram webhook updates"""
            try:
                update_data = await request.json()
                update = request.app.state.telegram_update_class(**update_data)
                await self.dp.feed_update(self.bot, update)
                return JSONResponse(content={"ok": True})
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)

        @self.webhook_app.post("/conversion-webhook")
        async def conversion_webhook(request: Request):
            """Handle conversion webhooks from tracker"""
            try:
                data = await request.json()
                await handle_conversion_webhook(data)
                return JSONResponse(content={"status": "ok"})
            except Exception as e:
                logger.error(f"Conversion webhook error: {e}")
                return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

        @self.webhook_app.post("/click-webhook")
        async def click_webhook(request: Request):
            """Handle click webhooks from tracker"""
            try:
                data = await request.json()
                await handle_click_webhook(data)
                return JSONResponse(content={"status": "ok"})
            except Exception as e:
                logger.error(f"Click webhook error: {e}")
                return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

        # Store update class for webhook handling
        from aiogram.types import Update
        self.webhook_app.state.telegram_update_class = Update

        logger.info(f"Webhook app setup completed with path: {webhook_path}")

    async def set_webhook(self, webhook_url: str):
        """Set webhook URL for Telegram bot"""
        if not self.bot:
            raise RuntimeError("Bot not initialized. Call setup_bot() first.")

        await self.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")

    async def delete_webhook(self):
        """Delete webhook for Telegram bot"""
        if not self.bot:
            return

        await self.bot.delete_webhook()
        logger.info("Webhook deleted")

    async def start_polling(self):
        """Start bot in polling mode"""

        if not self.bot or not self.dp:
            raise RuntimeError("Bot not initialized. Call setup_bot() first.")

        logger.info("Starting bot polling...")

        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            raise

    async def stop_bot(self):
        """Stop bot"""

        if self.bot:
            await self.bot.session.close()
            logger.info("Bot stopped")

    async def send_message_to_user(self, user_id: int, text: str, **kwargs):
        """Send message to user"""

        if not self.bot:
            logger.error("Bot not initialized")
            return

        try:
            await self.bot.send_message(chat_id=user_id, text=text, **kwargs)
            logger.info(f"Message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")


async def main(mode: str = "polling", webhook_url: str = None, port: int = 3000):
    """Main function"""

    # Initialize tracking
    await init_tracking()

    # Create bot instance
    bot_app = LandingBot()

    try:
        # Set up bot
        await bot_app.setup_bot()

        if mode == "webhook":
            if not webhook_url:
                raise ValueError("webhook_url is required for webhook mode")

            # Set up webhook app
            bot_app.setup_webhook_app()

            # Set webhook URL
            await bot_app.set_webhook(webhook_url)

            # Start webhook server
            logger.info(f"Starting webhook server on port {port}")
            config = uvicorn.Config(
                bot_app.webhook_app,
                host="0.0.0.0",
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)

            # Run server
            await server.serve()

        else:  # polling mode (default)
            # Start polling
            await bot_app.start_polling()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise

    finally:
        # Delete webhook if in webhook mode
        if mode == "webhook":
            await bot_app.delete_webhook()

        # Close connections
        await close_tracking()
        await bot_app.stop_bot()


def handle_shutdown(signum, frame):
    """Handle shutdown signals"""

    logger.info(f"Received signal {signum}. Shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Telegram Landing Bot")
    parser.add_argument(
        "--mode",
        choices=["polling", "webhook"],
        default="polling",
        help="Bot running mode"
    )
    parser.add_argument(
        "--webhook-url",
        help="Webhook URL for webhook mode (required when mode=webhook)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for webhook server (default: 3000)"
    )

    args = parser.parse_args()

    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Start bot
    try:
        asyncio.run(main(
            mode=args.mode,
            webhook_url=args.webhook_url,
            port=args.port
        ))
    except KeyboardInterrupt:
        logger.info("Bot shutdown complete")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        sys.exit(1)
