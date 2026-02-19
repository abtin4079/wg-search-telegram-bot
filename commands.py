from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv
import os
from auto_check import fetch_latest_listing_links
load_dotenv()
WG_SEARCH_URL = os.getenv("WG_SEARCH_URL")

# --------------------
# Telegram commands
# --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("WG Alerts Bot is running 🚀")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong ✅")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your chat_id is: {update.effective_chat.id}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not WG_SEARCH_URL:
        await update.message.reply_text("WG_SEARCH_URL is missing in .env")
        return

    try:
        links = fetch_latest_listing_links(WG_SEARCH_URL, limit=5)
        if not links:
            await update.message.reply_text("I found 0 listing links 😕 (WG may redirect/block requests)")
            return

        msg = "Latest listings I found:\n\n" + "\n".join(links)
        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"Error while checking WG page:\n{e}")
