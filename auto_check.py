import re
import requests
from bs4 import BeautifulSoup


# --------------------
# Scraper: fetch latest listing links
# --------------------
def fetch_latest_listing_links(search_url: str, limit: int = 5):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    r = requests.get(search_url, headers=headers, timeout=25, allow_redirects=True)
    r.raise_for_status()

    # If WG redirects to homepage, we can’t parse listings with requests
    if r.url.rstrip("/") == "https://www.wg-gesucht.de":
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")

        # Match listing IDs ending with .html
        if re.search(r"(\d{5,})\.html", href):
            if href.startswith("/"):
                href = "https://www.wg-gesucht.de" + href
            if "wg-gesucht.de" not in href:
                continue
            if href not in links:
                links.append(href)

        if len(links) >= limit:
            break

    return links

