"""
Analyze reading history with Claude to produce topic clusters,
book recommendations, curated quotes, and a reading personality summary.
"""

import json
import os

import anthropic

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 4096
_MAX_SUBJECTS_PER_BOOK = 8
_MAX_QUOTES_PER_BOOK = 3

_SYSTEM_PROMPT = """You are a literary analyst helping a reader understand their reading patterns.

You will receive a JSON array of books the user has read, each with:
- title, author
- user_rating (1-5, 0 = unrated)
- date_read (ISO date or null)
- subjects (from Open Library, may be empty for some books)
- quotes (popular quotes from Goodreads, may be empty)

Your tasks:
1. Cluster the books into 4-8 thematic topic groups based on subjects, titles, and authors.
   Give each cluster a short, evocative name (e.g., "Behavioral Science", "Dystopian Fiction").
   Assign every book to exactly one cluster.

2. For each cluster, recommend 3-5 books the reader has NOT already read.
   Base recommendations on the cluster's themes. Prefer highly-acclaimed books.
   Include a one-sentence reason tailored to this reader's taste.

3. For each cluster, select the 2-3 most thought-provoking or memorable quotes
   from the books in that cluster (only use quotes provided in the input).
   If no quotes are available for a cluster, leave the quotes array empty.

4. Write a 2-3 paragraph "reading personality" summary describing the reader's
   intellectual interests, reading patterns, and what their book choices reveal.

Return ONLY valid JSON matching this exact schema (no markdown fences, no extra text):
{
  "summary": "string (2-3 paragraphs)",
  "clusters": [
    {
      "name": "string",
      "description": "string (1-2 sentences about the cluster theme)",
      "books": ["Title by Author", ...],
      "recommendations": [
        {"title": "string", "author": "string", "reason": "string"}
      ],
      "quotes": [
        {"text": "string", "book": "string", "author": "string"}
      ]
    }
  ]
}

When subjects are sparse, infer themes from title and author instead.
"""


def _build_book_payload(books: list[dict]) -> list[dict]:
    """Convert book dicts to compact JSON-serializable form for the prompt."""
    payload = []
    for book in books:
        date_read = book.get("date_read")
        if hasattr(date_read, "isoformat"):
            date_read = date_read.date().isoformat()
        elif date_read is not None:
            date_read = str(date_read)

        payload.append(
            {
                "title": book.get("title", ""),
                "author": book.get("author", ""),
                "user_rating": book.get("user_rating", 0),
                "date_read": date_read,
                "subjects": (book.get("subjects") or [])[:_MAX_SUBJECTS_PER_BOOK],
                "quotes": (book.get("quotes") or [])[:_MAX_QUOTES_PER_BOOK],
            }
        )
    return payload


def _extract_json(text: str) -> dict:
    """Parse Claude's response, stripping markdown fences if present."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ``` wrappers
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def analyze(books: list[dict]) -> dict:
    """
    Send all books to Claude and return the structured analysis dict.
    Raises ValueError if the response cannot be parsed as JSON.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    payload = _build_book_payload(books)
    user_prompt = f"Here is my reading history ({len(payload)} books):\n{json.dumps(payload, indent=2)}"

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text
    try:
        return _extract_json(raw)
    except (json.JSONDecodeError, IndexError) as exc:
        raise ValueError(
            f"Claude returned invalid JSON. Raw response:\n{raw}"
        ) from exc
