import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from auto_check import fetch_latest_listing_links
from commands import start, ping, myid, check
# --------------------
# Load env
# --------------------
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# NEW: multiple chat IDs
CHAT_IDS_RAW = os.getenv("TELEGRAM_CHAT_IDS", "")
CHAT_ID_LIST = [int(cid.strip()) for cid in CHAT_IDS_RAW.split(",") if cid.strip()]

WG_SEARCH_URL_ERLANGEN = os.getenv("WG_SEARCH_URL_ERLANGEN")
WG_SEARCH_URL_NUERNBERG = os.getenv("WG_SEARCH_URL_NUERNBERG")
CHECK_SECONDS = int(os.getenv("CHECK_SECONDS", "180"))  # default 3 minutes
LAST_SEEN_ERLANGEN = "last_seen_erlangen.txt"
LAST_SEEN_NUERNBERG = "last_seen_nuernberg.txt"


# --------------------
# Save / load last seen listing (avoid duplicates)
# --------------------
def load_last_seen(last_seen: str) -> str:
    try:
        with open(last_seen, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def save_last_seen(value: str, last_seen: str):
    with open(last_seen, "w", encoding="utf-8") as f:
        f.write(value)




# --------------------
# Helper: send message to all users
# --------------------
async def send_to_all(bot, text: str):
    for chat_id in CHAT_ID_LIST:
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            # If one user didn't start the bot, Telegram will reject; ignore and continue
            pass


# --------------------
# Automatic check job (runs every CHECK_SECONDS)
# --------------------
async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    WG_SEARCH_URL = job_data["url"]
    LAST_SEEN = job_data["file"]
    city = job_data["city"]

    if not WG_SEARCH_URL or not CHAT_ID_LIST:
        return

    try:
        links = fetch_latest_listing_links(WG_SEARCH_URL, limit=1)
        if not links:
            return

        latest = links[0]
        last_seen = load_last_seen(LAST_SEEN)

        if latest != last_seen:
            save_last_seen(latest, LAST_SEEN)
            await send_to_all(
                context.bot,
                f"🏠 New WG-Gesucht listing in {city}:\n{latest}"
            )

    except Exception as e:
        await send_to_all(context.bot, f"Bot error ({city}):\n{e}")


# --------------------
# Main
# --------------------
def main():
    if not TOKEN:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in .env")

    if not CHAT_ID_LIST:
        print("WARNING: TELEGRAM_CHAT_IDS is empty in .env (no one will receive messages).")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("check", check))

    # ✅ Run automatic checker every 3 minutes (or CHECK_SECONDS from .env)
    # Erlangen checker
    app.job_queue.run_repeating(
        auto_check,
        interval=CHECK_SECONDS,
        first=10,
        data={
            "url": WG_SEARCH_URL_ERLANGEN,
            "file": LAST_SEEN_ERLANGEN,
            "city": "Erlangen"
        }
    )

    # Nürnberg checker
    app.job_queue.run_repeating(
        auto_check,
        interval=CHECK_SECONDS,
        first=15,
        data={
            "url": WG_SEARCH_URL_NUERNBERG,
            "file": LAST_SEEN_NUERNBERG,
            "city": "Nürnberg"
        }
    )


    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
