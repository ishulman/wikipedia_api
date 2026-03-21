"""
FastAPI backend for the Reading Analysis tool.
Exposes a single POST /analyze endpoint that returns an HTML report.
Deploy to Render (free tier) and call from an iOS Shortcut.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import claude_analysis
import goodreads_quotes
import goodreads_rss
import open_library
import report

app = FastAPI(
    title="Reading Analysis API",
    description="Analyze your Goodreads reading history with Claude AI.",
    version="1.0.0",
)


class AnalyzeRequest(BaseModel):
    goodreads_profile_url: str = Field(
        ...,
        description="Your Goodreads profile URL (e.g. https://www.goodreads.com/user/show/12345678-name) or numeric user ID.",
        examples=["https://www.goodreads.com/user/show/12345678-username"],
    )
    since_days: int = Field(
        default=730,
        ge=1,
        le=3650,
        description="How many days back to include in the analysis (default: 730 = 2 years).",
    )
    include_quotes: bool = Field(
        default=False,
        description="Whether to scrape popular quotes from Goodreads. Adds several minutes for large libraries.",
    )


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    """Simple health check / landing page."""
    return """
    <html><body style="font-family:sans-serif;padding:2rem;max-width:600px;margin:0 auto">
    <h1>Reading Analysis API</h1>
    <p>POST to <code>/analyze</code> with your Goodreads profile URL to get a reading analysis report.</p>
    <h2>Request body (JSON)</h2>
    <pre>{
  "goodreads_profile_url": "https://www.goodreads.com/user/show/YOUR_ID",
  "since_days": 730,
  "include_quotes": false
}</pre>
    <p>See <a href="/docs">/docs</a> for interactive API documentation.</p>
    </body></html>
    """


@app.post("/analyze", response_class=HTMLResponse)
def analyze(req: AnalyzeRequest) -> str:
    """
    Fetch reading history from Goodreads, enrich it, analyze with Claude,
    and return a mobile-optimized HTML report.
    """
    # 1. Fetch reading history
    print(f"[1/4] Fetching reading history for: {req.goodreads_profile_url}")
    try:
        books = goodreads_rss.fetch_read_books(req.goodreads_profile_url, since_days=req.since_days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not books:
        raise HTTPException(
            status_code=404,
            detail=(
                "No books found for this profile in the requested time window. "
                "Make sure your Goodreads profile is public and books are on the 'read' shelf."
            ),
        )

    print(f"  Found {len(books)} books")

    # 2. Enrich with Open Library subjects
    print(f"[2/4] Enriching {len(books)} books with Open Library subjects...")
    open_library.enrich_with_subjects(books)

    # 3. Optionally fetch quotes
    if req.include_quotes:
        print(f"[3/4] Fetching quotes from Goodreads (this may take a few minutes)...")
        goodreads_quotes.fetch_quotes(books)
    else:
        print("[3/4] Skipping quote scraping (include_quotes=false)")
        for book in books:
            book.setdefault("quotes", [])

    # 4. Analyze with Claude
    print("[4/4] Analyzing with Claude...")
    try:
        analysis = claude_analysis.analyze(books)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Claude analysis failed: {exc}")

    # 5. Render and return HTML
    print("Done. Returning HTML report.")
    return report.render(analysis, books)
