"""
Enrich books with subject/topic data from the Open Library API.
Free, no API key required. Supports batch ISBN lookups.
"""

import time

import requests

_BASE_URL = "https://openlibrary.org/api/books"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ReadingAnalysisTool/1.0)"}
_BATCH_SIZE = 20
_MAX_SUBJECTS = 8


def _fetch_batch(isbn13s: list[str]) -> dict[str, list[str]]:
    """
    Fetch subjects for up to _BATCH_SIZE ISBN13s in one request.
    Returns a dict mapping isbn13 -> list[subject_name].
    """
    bibkeys = ",".join(f"ISBN:{isbn}" for isbn in isbn13s)
    try:
        resp = requests.get(
            _BASE_URL,
            params={"bibkeys": bibkeys, "format": "json", "jscmd": "data"},
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        print(f"  Warning: Open Library request failed: {exc}")
        return {}
    except ValueError:
        return {}

    result: dict[str, list[str]] = {}
    for isbn in isbn13s:
        key = f"ISBN:{isbn}"
        book_data = data.get(key, {})
        subjects = [
            s["name"]
            for s in book_data.get("subjects", [])
            if isinstance(s, dict) and "name" in s
        ]
        result[isbn] = subjects[:_MAX_SUBJECTS]
    return result


def enrich_with_subjects(books: list[dict]) -> list[dict]:
    """
    Add a 'subjects' key (list[str]) to each book dict in-place.
    Books without an ISBN13 get an empty subjects list.
    Batches requests to minimize API calls.
    """
    # Collect books that have a usable ISBN
    isbn_books: list[tuple[int, str]] = []  # (index, isbn13)
    for i, book in enumerate(books):
        isbn = (book.get("isbn13") or book.get("isbn") or "").strip()
        # Validate it looks like a real ISBN (10 or 13 digits)
        if isbn and isbn.isdigit() and len(isbn) in (10, 13):
            isbn_books.append((i, isbn))
        else:
            book["subjects"] = []

    # Process in batches
    for batch_start in range(0, len(isbn_books), _BATCH_SIZE):
        batch = isbn_books[batch_start : batch_start + _BATCH_SIZE]
        isbn13s = [isbn for _, isbn in batch]
        subjects_map = _fetch_batch(isbn13s)

        for idx, isbn in batch:
            books[idx]["subjects"] = subjects_map.get(isbn, [])

        if batch_start + _BATCH_SIZE < len(isbn_books):
            time.sleep(0.5)

    return books
