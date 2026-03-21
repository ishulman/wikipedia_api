"""
Fetch a user's read books from Goodreads public RSS feed.
No login or API key required — works as long as the profile is public.
"""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ReadingAnalysisTool/1.0)"}
_RSS_URL = "https://www.goodreads.com/review/list_rss/{user_id}?shelf=read&per_page=200&page={page}"


def extract_user_id(profile_url_or_id: str) -> str:
    """
    Accept either a raw user ID ('12345678') or a full profile URL
    ('https://www.goodreads.com/user/show/12345678-username') and return
    the numeric user ID string.
    """
    match = re.search(r"/user/show/(\d+)", profile_url_or_id)
    if match:
        return match.group(1)
    if re.fullmatch(r"\d+", profile_url_or_id.strip()):
        return profile_url_or_id.strip()
    raise ValueError(
        f"Cannot extract Goodreads user ID from: {profile_url_or_id!r}. "
        "Provide a profile URL like https://www.goodreads.com/user/show/12345678-name "
        "or a raw numeric user ID."
    )


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse Goodreads RSS date strings to aware datetime objects."""
    if not date_str:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _parse_feed_page(xml_text: str) -> list[dict]:
    """Parse one page of RSS XML and return a list of book dicts."""
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    books = []
    for item in channel.findall("item"):

        def text(tag: str) -> str:
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        # Goodreads uses a custom namespace for some fields
        isbn = text("isbn") or text("{http://www.goodreads.com/}isbn")
        isbn13 = text("isbn13") or text("{http://www.goodreads.com/}isbn13")

        # Strip Goodreads' ="..." ISBN wrapping if present
        for val in (isbn, isbn13):
            val = re.sub(r'^="?|"?$', "", val)

        isbn = re.sub(r'^="?|"?$', "", isbn)
        isbn13 = re.sub(r'^="?|"?$', "", isbn13)

        user_rating_str = text("user_rating") or text("{http://www.goodreads.com/}user_rating")
        try:
            user_rating = int(user_rating_str)
        except (ValueError, TypeError):
            user_rating = 0

        user_read_at = text("user_read_at") or text("{http://www.goodreads.com/}user_read_at")
        read_date = _parse_date(user_read_at)

        # Extract book_id from the guid or link URL
        guid = text("guid")
        book_id_match = re.search(r"/review/show/(\d+)", guid) or re.search(r"(\d+)", guid)
        book_id = book_id_match.group(1) if book_id_match else ""

        # Extract title (strip series info in parentheses e.g. "Name (Series #1)")
        title = text("title")

        author = text("author_name") or text("{http://www.goodreads.com/}author_name")

        books.append(
            {
                "title": title,
                "author": author,
                "isbn": isbn,
                "isbn13": isbn13 or isbn,
                "user_rating": user_rating,
                "date_read": read_date,
                "book_id": book_id,
            }
        )
    return books


def fetch_read_books(profile_url_or_id: str, since_days: int = 730) -> list[dict]:
    """
    Fetch all books read within the last `since_days` days from the user's
    Goodreads public RSS feed.

    Returns a list of book dicts with keys:
      title, author, isbn13, user_rating, date_read, book_id
    """
    user_id = extract_user_id(profile_url_or_id)
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=since_days)
    books: list[dict] = []
    page = 1

    while True:
        url = _RSS_URL.format(user_id=user_id, page=page)
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            print(f"  Warning: failed to fetch Goodreads RSS page {page}: {exc}")
            break

        page_books = _parse_feed_page(resp.text)
        if not page_books:
            break  # No more results

        # Filter and check if we've gone past the cutoff
        reached_cutoff = False
        for book in page_books:
            read_date = book.get("date_read")
            if read_date is None or read_date >= cutoff:
                books.append(book)
            else:
                reached_cutoff = True

        if reached_cutoff:
            break  # All remaining pages are older than cutoff

        page += 1
        time.sleep(1)  # Be polite

    return books
