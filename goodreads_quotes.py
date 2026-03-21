"""
Scrape popular quotes for books from Goodreads quotes search.
Optional enrichment — off by default to keep API response fast.
Handles rate-limiting gracefully: skips a book rather than failing the pipeline.
"""

import random
import time
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
_QUOTES_URL = "https://www.goodreads.com/quotes/search?q={query}"
_MAX_QUOTES_PER_BOOK = 5


def _scrape_quotes_for_title(title: str) -> list[str]:
    """
    Fetch up to _MAX_QUOTES_PER_BOOK quotes for the given book title.
    Returns an empty list on any error or if no quotes found.
    """
    # Use just the main title (drop series info in parentheses)
    clean_title = title.split("(")[0].strip()
    url = _QUOTES_URL.format(query=quote_plus(clean_title))

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code in (429, 403):
            return []
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    quote_divs = soup.find_all("div", class_="quoteText")

    quotes = []
    for div in quote_divs[:_MAX_QUOTES_PER_BOOK]:
        raw = div.get_text(separator="\n").strip()
        # Split on em-dash attribution line; take the quote part only
        for sep in ("\n―", "\n—", "\n-"):
            if sep in raw:
                raw = raw.split(sep)[0].strip()
                break
        # Strip surrounding quote marks and whitespace
        quote_text = raw.strip('"\u201c\u201d\u2018\u2019 \n')
        if quote_text:
            quotes.append(quote_text)

    return quotes


def fetch_quotes(books: list[dict]) -> list[dict]:
    """
    Add a 'quotes' key (list[str]) to each book dict in-place.
    Fetches quotes sequentially with delays to respect rate limits.
    """
    for i, book in enumerate(books):
        title = book.get("title", "")
        if not title:
            book["quotes"] = []
            continue

        print(f"  Fetching quotes ({i + 1}/{len(books)}): {title[:50]}", flush=True)
        book["quotes"] = _scrape_quotes_for_title(title)

        if i < len(books) - 1:
            time.sleep(2 + random.uniform(0, 1))

    return books
