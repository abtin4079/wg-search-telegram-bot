"""Main Telegram bot application."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from auto_check import fetch_latest_listing_links
from cache import listing_cache, rate_limiter
from commands import check, myid, ping, start, status
from config import (
    CHECK_INTERVAL_SECONDS,
    LAST_SEEN_FILE_ERLANGEN,
    LAST_SEEN_FILE_NUERNBERG,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_IDS,
    WG_SEARCH_URL_ERLANGEN,
    WG_SEARCH_URL_NUERNBERG,
    validate_config,
)
from state import bot_start_time, metrics
from utils import load_last_seen, save_last_seen

logger = logging.getLogger(__name__)


async def send_to_all(bot, text: str) -> None:
    """Send message to all configured chat IDs.
    
    Args:
        bot: The Telegram bot instance
        text: The message text to send
    """
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            logger.debug(f"Message sent to chat {chat_id}")
            metrics["notifications_sent"] += 1
        except Exception as e:
            logger.error(f"Failed to send message to chat {chat_id}: {e}")
            metrics["errors"] += 1


async def auto_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatic job to check for new listings.
    
    This job runs periodically and checks if there are new listings,
    notifying all users if a new listing is found.
    """
    job_data = context.job.data
    search_url = job_data["url"]
    last_seen_file = job_data["file"]
    city = job_data["city"]
    city_key = city.lower()

    if not search_url or not TELEGRAM_CHAT_IDS:
        logger.debug(f"Skipping check for {city}: missing config or recipients")
        return

    try:
        # Apply rate limiting to avoid being blocked
        await rate_limiter.wait_if_needed(search_url)
        
        metrics["checks_total"] += 1
        links = fetch_latest_listing_links(search_url, limit=1)
        if not links:
            return

        latest_link = links[0]
        last_seen = load_last_seen(last_seen_file)

        # Check if we've already notified about this listing (cache check)
        if listing_cache.has_seen(city_key, latest_link):
            logger.debug(f"Listing already in cache for {city}: {latest_link}")
            return

        if latest_link != last_seen:
            save_last_seen(latest_link, last_seen_file)
            listing_cache.add(city_key, latest_link)
            metrics["listings_found"] += 1
            await send_to_all(
                context.bot,
                f"<b>🏠 New WG-Gesucht listing in {city}</b>\n"
                f"<a href='{latest_link}'>View Apartment</a>"
            )
            logger.info(f"New listing found in {city}: {latest_link}")
        else:
            logger.debug(f"No new listings in {city}")

    except Exception as e:
        logger.error(f"Error checking {city}: {e}", exc_info=True)
        metrics["errors"] += 1
        # Continue running despite errors - improved error recovery
        try:
            await send_to_all(context.bot, f"⚠️ Bot error ({city}): {str(e)[:100]}")
        except Exception:
            logger.error("Failed to send error notification", exc_info=True)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bot errors globally.
    
    Args:
        update: The update that caused the error
        context: The error context
    """
    logger.error(f"Unhandled error: {context.error}", exc_info=context.error)
    metrics["errors"] += 1
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")



def main() -> None:
    """Initialize and run the bot."""
    try:
        validate_config()
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        raise SystemExit(str(e))

    logger.info("Starting WG-Gesucht Telegram Bot...")
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("status", status))

    app.add_error_handler(error_handler)

    if WG_SEARCH_URL_ERLANGEN:
        logger.info("Starting Erlangen checker")
        app.job_queue.run_repeating(
            auto_check,
            interval=CHECK_INTERVAL_SECONDS,
            first=10,
            data={
                "url": WG_SEARCH_URL_ERLANGEN,
                "file": LAST_SEEN_FILE_ERLANGEN,
                "city": "Erlangen",
            },
        )
    else:
        logger.warning("Erlangen checker disabled (URL not configured)")

    if WG_SEARCH_URL_NUERNBERG:
        logger.info("Starting Nürnberg checker")
        app.job_queue.run_repeating(
            auto_check,
            interval=CHECK_INTERVAL_SECONDS,
            first=15,
            data={
                "url": WG_SEARCH_URL_NUERNBERG,
                "file": LAST_SEEN_FILE_NUERNBERG,
                "city": "Nürnberg",
            },
        )
    else:
        logger.warning("Nürnberg checker disabled (URL not configured)")

    logger.info("Bot is running... (Press Ctrl+C to stop)")
    app.run_polling()



if __name__ == "__main__":
    main()
