"""
Command handlers for Telegram bot
"""

import os
import sys
from typing import Dict, Any

# Add project root to sys.path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode

from loguru import logger

from config import BOT_MESSAGES, settings
from tracking import get_tracking_manager


# Create router for handlers
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""

    user_id = message.from_user.id
    username = message.from_user.username or "user"

    logger.info(f"User {user_id} ({username}) started the bot")

    # Create inline keyboard with transition button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=BOT_MESSAGES["cta_button"],
            callback_data="get_offer"
        )]
    ])

    await message.reply(
        BOT_MESSAGES["welcome"],
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )


@router.callback_query(F.data.startswith("visit_landing:"))
async def callback_visit_landing(callback: CallbackQuery):
    """Handle visit landing page request"""

    # Extract click_id from callback data
    click_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    try:
        # Generate fresh tracking URL
        tracking_result = await get_tracking_manager().generate_tracking_link(
            user_id=user_id,
            source="telegram_bot_visit",
            additional_params={
                "sub3": "direct_visit",
                "sub4": callback.from_user.username or "user",
                "click_id": click_id
            },
            lp_id=settings.default_lp_id,
            offer_id=settings.default_offer_id,
            ts_id=settings.default_ts_id
        )

        tracking_url = tracking_result["tracking_url"]

        # Send URL as message
        await callback.message.reply(
            f"🌐 Ваша персональная ссылка на предложение:\n\n{tracking_url}\n\n"
            f"📱 Нажмите на ссылку или скопируйте её в браузер для перехода к Supreme Company.",
            parse_mode=ParseMode.HTML
        )

        # Track the visit event
        await get_tracking_manager().track_event(
            click_id=click_id,
            event_type="landing_page_visit",
            event_data={
                "user_id": user_id,
                "username": callback.from_user.username,
                "source": "telegram_callback"
            }
        )

        await callback.answer("Ссылка отправлена! 📨")

    except Exception as e:
        logger.error(f"Error sending tracking URL for user {user_id}: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.", show_alert=True)


@router.callback_query(F.data == "get_offer")
async def callback_get_offer(callback: CallbackQuery):
    """Handle offer button click"""

    user_id = callback.from_user.id
    username = callback.from_user.username or "user"

    try:
        # Generate tracking link
        tracking_result = await get_tracking_manager().generate_tracking_link(
            user_id=user_id,
            source="telegram_bot_visit",
            additional_params={
                "sub1": "telegram_bot_visit", # Added sub1
                "sub2": "callback", # Added sub2
                "sub3": "direct_visit",
                "sub4": callback.from_user.username or "user",
                "sub5": "offer_page", # Added sub5
                "aff_sub": "test_aff_sub_1", # Added for testing aff_sub
                "aff_sub2": "test_aff_sub_2", # Added for testing aff_sub2
                "aff_sub3": "test_aff_sub_3", # Added for testing aff_sub3
                "aff_sub4": "test_aff_sub_4", # Added for testing aff_sub4
                "aff_sub5": "test_aff_sub_5", # Added for testing aff_sub5
                # "click_id": click_id # Removed click_id here
            },
            lp_id=settings.default_lp_id,
            offer_id=settings.default_offer_id,
            ts_id=settings.default_ts_id
        )

        click_id = tracking_result["click_id"] # click_id is assigned here
        tracking_url = tracking_result["tracking_url"]

        logger.info(f"Generated tracking link for user {user_id}: {click_id}")

        # Create button with link to landing
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🌐 Перейти к предложению",
                url=tracking_url
            )],
            [InlineKeyboardButton(
                text="❓ Задать вопрос",
                callback_data="ask_question"
            )]
        ])

        # Send message with offer
        await callback.message.edit_text(
            BOT_MESSAGES["main_offer"],
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

        # Mark link generation event
        await get_tracking_manager().track_event(
            click_id=click_id,
            event_type="click",
            event_data={
                "user_id": user_id,
                "username": username,
                "source": "telegram_callback"
            }
        )

        await callback.answer("Link generated! Go to offer.")

    except Exception as e:
        logger.error(f"Error generating tracking link for user {user_id}: {e}")
        await callback.answer("An error occurred. Try again later.", show_alert=True)


@router.callback_query(F.data == "ask_question")
async def callback_ask_question(callback: CallbackQuery):
    """Handle ask question button click"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Call",
            callback_data="contact_call"
        )],
        [InlineKeyboardButton(
            text="Write in chat",
            callback_data="contact_chat"
        )],
        [InlineKeyboardButton(
            text="Back",
            callback_data="back_to_offer"
        )]
    ])

    await callback.message.edit_text(
        "How is it more convenient to contact you?\n\n"
        "Choose contact method, and our specialist will contact you soon.",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "contact_call")
async def callback_contact_call(callback: CallbackQuery):
    """Handle call option selection"""

    await callback.message.edit_text(
        "**Contact information:**\n\n"
        "Phone: +7 (999) 123-45-67\n"
        "Email: info@yourcompany.com\n\n"
        "Call us or write, we will answer all questions!\n\n"
        "To return press /start"
    )

    await callback.answer("Contacts sent!")


@router.callback_query(F.data == "contact_chat")
async def callback_contact_chat(callback: CallbackQuery):
    """Handle chat option selection"""

    await callback.message.edit_text(
        "**Write your question here**\n\n"
        "Just send a message, and we will answer as soon as possible.\n\n"
        "To return to offer press /start"
    )

    await callback.answer("You can write your question right here!")


@router.callback_query(F.data == "back_to_offer")
async def callback_back_to_offer(callback: CallbackQuery):
    """Return to offer"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=BOT_MESSAGES["cta_button"],
            callback_data="get_offer"
        )]
    ])

    await callback.message.edit_text(
        BOT_MESSAGES["welcome"],
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show statistics (admins only)"""

    user_id = message.from_user.id

    if user_id not in settings.admin_ids:
        await message.reply("You do not have access to this command.")
        return

    # TODO: Add real statistics retrieval from tracker
    await message.reply(
        "**Bot statistics:**\n\n"
        "Active users: -\n"
        "Total clicks: -\n"
        "Conversions: -\n"
        "CTR: -%\n\n"
        "_Statistics integration in development_"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Show help"""

    help_text = """
**Bot for landing page visits**

**Commands:**
/start - Begin work with bot
/help - Show this help
/stats - Statistics (admins only)

**How to use:**
1. Press /start
2. Choose "Learn more details"
3. Follow link to offer

If you have questions - write to bot!
"""

    await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)


@router.message(F.text)
async def handle_text_messages(message: Message):
    """Handle text messages"""

    user_id = message.from_user.id
    text = message.text.lower()

    # Simple responses to common questions
    responses = {
        "hello": "Hello! Press /start to begin.",
        "hi": "Hi! Press /start to begin.",
        "help": "Need help? Write /help",
        "price": "Price information on our site. Follow link in /start",
        "cost": "Cost information on our site. Follow link in /start"
    }

    for keyword, response in responses.items():
        if keyword in text:
            await message.reply(response)
            return

    # If user wrote a question, forward to specialist
    if len(text) > 5:  # Consider this a question
        await message.reply(
            "Thank you for your question!\n\n"
            "Our specialist will contact you soon.\n\n"
            "Meanwhile check our offer - press /start"
        )

        logger.info(f"User {user_id} asked: {text}")

        # TODO: Send notification to admins or CRM


@router.message(F.photo | F.document | F.voice | F.video)
async def handle_media(message: Message):
    """Handle media files"""

    await message.reply(
        "Thank you for the file!\n\n"
        "We will review your information and contact you.\n\n"
        "To return to offer press /start"
    )

    logger.info(f"User {message.from_user.id} sent media file")


# Functions for conversion processing (called from webhook or API)

async def handle_conversion_webhook(conversion_data: Dict[str, Any]):
    """
    Handle webhook from tracker about new conversion
    Called when user fills form on landing page
    """

    click_id = conversion_data.get("click_id")
    conversion_type = conversion_data.get("conversion_type", "lead")
    user_data = conversion_data.get("user_data", {})

    if not click_id:
        logger.error("No click_id in conversion webhook")
        return

    # Mark conversion in tracker
    await get_tracking_manager().track_conversion(
        click_id=click_id,
        conversion_type=conversion_type,
        conversion_value=conversion_data.get("value", 0),
        conversion_data=user_data
    )

    # Send notification to bot user
    # TODO: Implement sending message to user

    # Send notification to admins
    for admin_id in settings.admin_ids:
        try:
            notification = BOT_MESSAGES["conversion_notification"].format(
                user_id=user_data.get("name", "Unknown"),
                name=user_data.get("name", "Not specified"),
                email=user_data.get("email", "Not specified")
            )

            # TODO: Send message to admin
            # await bot.send_message(admin_id, notification)

            logger.info(f"Sent conversion notification to admin {admin_id}")

        except Exception as e:
            logger.error(f"Error sending notification to admin {admin_id}: {e}")

    logger.info(f"Processed conversion webhook: {click_id} - {conversion_type}")


async def handle_click_webhook(click_data: Dict[str, Any]):
    """
    Handle webhook from tracker about new click
    Called when user follows link
    """

    click_id = click_data.get("click_id")
    user_id = click_data.get("user_id")

    if not click_id:
        logger.error("No click_id in click webhook")
        return

    # Mark click event
    await get_tracking_manager().track_event(
        click_id=click_id,
        event_type="click_confirmed",
        event_data={
            "user_id": user_id,
            "ip": click_data.get("ip"),
            "user_agent": click_data.get("user_agent")
        }
    )

    logger.info(f"Processed click webhook: {click_id} from user {user_id}")
