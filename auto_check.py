"""WG-Gesucht scraper module for fetching apartment listings."""

import logging
import re

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import SCRAPER_TIMEOUT, SCRAPER_USER_AGENT

logger = logging.getLogger(__name__)


def create_session_with_retries() -> requests.Session:
    """Create a requests session with retry logic.
    
    Returns:
        Configured Session with exponential backoff retry strategy
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_latest_listing_links(search_url: str, limit: int = 5) -> list[str]:
    """Fetch latest apartment listing links from WG-Gesucht.
    
    Args:
        search_url: The WG-Gesucht search URL
        limit: Maximum number of listings to return
        
    Returns:
        List of listing URLs (up to limit items)
        
    Raises:
        requests.RequestException: If the HTTP request fails
    """
    headers = {
        "User-Agent": SCRAPER_USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    logger.debug(f"Fetching listings from: {search_url}")
    
    session = create_session_with_retries()
    
    try:
        response = session.get(
            search_url,
            headers=headers,
            timeout=SCRAPER_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.Timeout:
        logger.error(f"Request timeout while fetching {search_url}")
        raise
    except requests.RequestException as e:
        logger.error(f"Request failed for {search_url}: {e}")
        raise
    finally:
        session.close()

    if response.url.rstrip("/") == "https://www.wg-gesucht.de":
        logger.warning("WG-Gesucht redirected to homepage (may be blocking or temporarily unavailable)")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for link in soup.select("a[href]"):
        # Explicitly cast to string for type safety
        href = str(link.get("href", ""))

        if not href or not re.search(r"(\d{5,})\.html", href):
            continue

        # Sanitize and validate URLs
        if href.startswith("/"):
            href = "https://www.wg-gesucht.de" + href

        # Security: Only allow wg-gesucht.de URLs
        if "wg-gesucht.de" not in href or href in links:
            continue

        links.append(href)
        if len(links) >= limit:
            break

    logger.info(f"Fetched {len(links)} listings from {search_url}")
    return links

