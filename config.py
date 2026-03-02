"""Configuration management for WG-Gesucht Telegram Bot."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS_RAW = os.getenv("TELEGRAM_CHAT_IDS", "")
TELEGRAM_CHAT_IDS = [int(cid.strip()) for cid in TELEGRAM_CHAT_IDS_RAW.split(",") if cid.strip()]

# Authorization - restrict commands to specific users (optional)
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = (
    [int(uid.strip()) for uid in ALLOWED_USER_IDS_RAW.split(",") if uid.strip()]
    if ALLOWED_USER_IDS_RAW else []
)

# WG-Gesucht URLs
WG_SEARCH_URL_ERLANGEN = os.getenv("WG_SEARCH_URL_ERLANGEN")
WG_SEARCH_URL_NUERNBERG = os.getenv("WG_SEARCH_URL_NUERNBERG")

# Checker intervals (in seconds)
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_SECONDS", "180"))

# File paths for tracking
LAST_SEEN_FILE_ERLANGEN = Path("last_seen_erlangen.txt")
LAST_SEEN_FILE_NUERNBERG = Path("last_seen_nuernberg.txt")

# Scraper configuration
SCRAPER_TIMEOUT = 25
SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)

# Rate limiting configuration (seconds between requests)
RATE_LIMIT_INTERVAL = 2  # Minimum seconds between requests to avoid being blocked

# Listing cache size (prevent duplicate notifications)
LISTING_CACHE_SIZE = 50  # Keep track of last 50 listings per city

# City configurations
_CITY_CONFIGS = {
    "erlangen": {
        "name": "Erlangen",
        "url": WG_SEARCH_URL_ERLANGEN,
        "last_seen_file": LAST_SEEN_FILE_ERLANGEN,
    },
    "nuernberg": {
        "name": "Nürnberg",
        "url": WG_SEARCH_URL_NUERNBERG,
        "last_seen_file": LAST_SEEN_FILE_NUERNBERG,
    },
}

# City name aliases (avoids data duplication)
CITY_ALIASES = {
    "nürnberg": "nuernberg",
}

# Legacy CITIES for backward compatibility - will be deprecated
CITIES = {
    **_CITY_CONFIGS,
    "nürnberg": _CITY_CONFIGS["nuernberg"],  # Alias
}


def get_city_config(city_key: str) -> dict | None:
    """Get city configuration by key, resolving aliases.
    
    Args:
        city_key: City identifier (e.g., 'erlangen', 'nürnberg')
        
    Returns:
        City configuration dict or None if not found
    """
    key = CITY_ALIASES.get(city_key, city_key)
    return _CITY_CONFIGS.get(key)


def validate_config() -> None:
    """Validate that all required configuration is present."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")

    if not TELEGRAM_CHAT_IDS:
        logger.warning("TELEGRAM_CHAT_IDS is empty in .env (no recipients configured)")

    if not WG_SEARCH_URL_ERLANGEN:
        logger.warning("WG_SEARCH_URL_ERLANGEN not set - Erlangen checker will be disabled")

    if not WG_SEARCH_URL_NUERNBERG:
        logger.warning("WG_SEARCH_URL_NUERNBERG not set - Nürnberg checker will be disabled")

    logger.info(f"Configuration loaded: {len(TELEGRAM_CHAT_IDS)} chat IDs configured")
