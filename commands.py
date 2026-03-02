"""Telegram bot commands."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from auto_check import fetch_latest_listing_links
from config import ALLOWED_USER_IDS, CHECK_INTERVAL_SECONDS, CITIES

logger = logging.getLogger(__name__)


def format_listing_links(links: list[str]) -> str:
    """Format listing links for better readability.
    
    Args:
        links: List of WG-Gesucht listing URLs
        
    Returns:
        Formatted string with numbered listings
    """
    formatted = []
    for i, link in enumerate(links, 1):
        # Extract listing ID from URL (e.g., 13163705.html -> 13163705)
        listing_id = link.split('.')[-2].split('/')[-1] if '.' in link else str(i)
        # Create a readable format with emoji, number, and clickable link
        formatted.append(f"{i}. 🏠 <a href='{link}'>View Listing #{listing_id}</a>")
    return "\n".join(formatted)


def is_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the bot.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if authorized (or if no restrictions configured)
    """
    # If no ALLOWED_USER_IDS configured, allow all users
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "<b>WG Alerts Bot is running 🚀</b>\n\n"
        "Commands:\n"
        "/check - Manually check for listings\n"
        "/status - Show bot status\n"
        "/myid - Get your chat ID\n"
        "/ping - Test bot responsiveness",
        parse_mode="HTML"
    )
    logger.info(f"User {update.effective_user.id} started bot")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ping command."""
    await update.message.reply_text("Pong ✅")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myid command to get user's chat ID."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"<b>Your IDs:</b>\n"
        f"Chat ID: <code>{chat_id}</code>\n"
        f"User ID: <code>{user_id}</code>",
        parse_mode="HTML"
    )
    logger.info(f"User {user_id} requested chat ID: {chat_id}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command to show bot status and statistics."""
    from state import bot_start_time, metrics
    
    uptime = datetime.now() - bot_start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Count configured cities
    from config import _CITY_CONFIGS
    configured_cities = sum(1 for city in _CITY_CONFIGS.values() if city["url"])
    
    status_msg = (
        f"<b>✅ Bot Status</b>\n\n"
        f"🕒 <b>Uptime:</b> {hours}h {minutes}m {seconds}s\n"
        f"🏛 <b>Cities monitored:</b> {configured_cities}\n"
        f"⏱ <b>Check interval:</b> {CHECK_INTERVAL_SECONDS}s\n\n"
        f"<b>📊 Statistics:</b>\n"
        f"Total checks: {metrics['checks_total']}\n"
        f"Listings found: {metrics['listings_found']}\n"
        f"Notifications sent: {metrics['notifications_sent']}\n"
        f"Errors: {metrics['errors']}"
    )
    
    await update.message.reply_text(status_msg, parse_mode="HTML")
    logger.info(f"User {update.effective_user.id} requested bot status")


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /check command to fetch latest listings.
    
    Usage:
        /check erlangen - Check Erlangen listings
        /check nuernberg - Check Nürnberg listings
        /check - Check all configured cities
    """
    user_id = update.effective_user.id
    
    # Authorization check
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ <b>Unauthorized</b>\nYou don't have permission to use this bot.", parse_mode="HTML")
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        return
    
    city_arg = context.args[0].lower() if context.args else ""
    
    logger.info(f"User {user_id} requested check for: {city_arg or 'all cities'}")
    
    if city_arg and city_arg in CITIES:
        await _check_single_city(update, city_arg)
    elif not city_arg:
        await _check_all_cities(update)
    else:
        await update.message.reply_text(
            "<b>Usage:</b> /check [erlangen|nuernberg]\n\n"
            "Omit parameter to check all cities.",
            parse_mode="HTML"
        )


async def _check_single_city(update: Update, city_key: str) -> None:
    """Check listings for a specific city."""
    city_config = CITIES[city_key]
    city_name = city_config["name"]
    url = city_config["url"]
    
    if not url:
        logger.warning(f"URL not configured for {city_name}")
        await update.message.reply_text(
            f"⚠️ <b>Configuration missing for {city_name}</b>",
            parse_mode="HTML"
        )
        return
    
    try:
        links = fetch_latest_listing_links(url, limit=5)
        if not links:
            await update.message.reply_text(
                f"📍 <b>{city_name}</b>: No listings found (website may be unavailable)",
                parse_mode="HTML"
            )
        else:
            # Format links with better readability
            formatted_links = format_listing_links(links)
            message = f"📍 <b>{city_name} - Latest listings:</b>\n\n{formatted_links}"
            await update.message.reply_text(message, parse_mode="HTML", disable_web_page_preview=True)
            logger.info(f"Sent {len(links)} listings for {city_name}")
    except Exception as e:
        logger.error(f"Error checking {city_name}: {e}")
        await update.message.reply_text(
            f"❌ <b>Error checking {city_name}:</b> {str(e)[:100]}",
            parse_mode="HTML"
        )


async def _check_all_cities(update: Update) -> None:
    """Check listings for all configured cities."""
    await update.message.reply_text("<b>Checking all cities...</b>", parse_mode="HTML")
    
    for city_key, city_config in CITIES.items():
        # Skip aliases (nürnberg is alias for nuernberg)
        if city_key.startswith("nürnberg"):
            continue
        
        url = city_config["url"]
        city_name = city_config["name"]
        
        if not url:
            logger.warning(f"URL not configured for {city_name}")
            await update.message.reply_text(
                f"⚠️ <b>Configuration missing for {city_name}</b>",
                parse_mode="HTML"
            )
            continue
        
        try:
            links = fetch_latest_listing_links(url, limit=5)
            if not links:
                await update.message.reply_text(
                    f"📍 <b>{city_name}</b>: No listings found (website may be unavailable)",
                    parse_mode="HTML"
                )
            else:
                formatted_links = format_listing_links(links)
                message = f"📍 <b>{city_name} - Latest listings:</b>\n\n{formatted_links}"
                await update.message.reply_text(message, parse_mode="HTML", disable_web_page_preview=True)
                logger.info(f"Sent {len(links)} listings for {city_name}")
        except Exception as e:
            logger.error(f"Error checking {city_name}: {e}")
            await update.message.reply_text(
                f"❌ <b>Error checking {city_name}:</b> {str(e)[:100]}",
                parse_mode="HTML"
            )
