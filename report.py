"""
Render a mobile-optimized, self-contained HTML reading analysis report.
"""

from datetime import datetime, timezone
from statistics import mean


def _stars(rating: int) -> str:
    if not rating:
        return '<span class="no-rating">unrated</span>'
    filled = "★" * rating
    empty = "☆" * (5 - rating)
    return f'<span class="stars">{filled}{empty}</span>'


def _esc(text: str) -> str:
    """Minimal HTML escaping."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _compute_stats(books: list[dict]) -> dict:
    ratings = [b["user_rating"] for b in books if b.get("user_rating")]
    avg_rating = round(mean(ratings), 1) if ratings else 0

    years: dict[int, int] = {}
    for book in books:
        d = book.get("date_read")
        if d and hasattr(d, "year"):
            years[d.year] = years.get(d.year, 0) + 1

    # Count top subjects across all books
    subject_counts: dict[str, int] = {}
    for book in books:
        for subj in book.get("subjects") or []:
            subject_counts[subj] = subject_counts.get(subj, 0) + 1
    top_subjects = sorted(subject_counts, key=subject_counts.get, reverse=True)[:8]

    return {
        "total": len(books),
        "avg_rating": avg_rating,
        "years": years,
        "top_subjects": top_subjects,
    }


def _books_per_year_bars(years: dict[int, int]) -> str:
    if not years:
        return ""
    max_count = max(years.values())
    rows = []
    for year in sorted(years):
        count = years[year]
        pct = int(count / max_count * 100)
        rows.append(
            f'<div class="bar-row">'
            f'<span class="bar-label">{year}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
            f'<span class="bar-count">{count}</span>'
            f"</div>"
        )
    return "\n".join(rows)


def render(analysis: dict, books: list[dict]) -> str:
    """
    Return a self-contained HTML string for the reading analysis report.
    """
    stats = _compute_stats(books)
    generated = datetime.now(tz=timezone.utc).strftime("%B %d, %Y")

    # Build lookup: book title -> rating
    rating_lookup: dict[str, int] = {}
    for book in books:
        key = book.get("title", "").lower()
        rating_lookup[key] = book.get("user_rating", 0)

    # ── Clusters HTML ────────────────────────────────────────────────────────
    clusters_html_parts = []
    for cluster in analysis.get("clusters", []):
        name = _esc(cluster.get("name", ""))
        description = _esc(cluster.get("description", ""))

        # Books list
        book_items = []
        for book_str in cluster.get("books", []):
            rating = rating_lookup.get(book_str.lower().split(" by ")[0].strip(), 0)
            book_items.append(
                f'<li><span class="book-title">{_esc(book_str)}</span> {_stars(rating)}</li>'
            )
        books_list = "<ul>" + "\n".join(book_items) + "</ul>" if book_items else ""

        # Recommendations table
        rec_rows = []
        for rec in cluster.get("recommendations", []):
            rec_rows.append(
                f"<tr>"
                f'<td><em>{_esc(rec.get("title",""))}</em></td>'
                f'<td>{_esc(rec.get("author",""))}</td>'
                f'<td>{_esc(rec.get("reason",""))}</td>'
                f"</tr>"
            )
        if rec_rows:
            recs_html = (
                '<table class="recs-table">'
                "<thead><tr><th>Title</th><th>Author</th><th>Why you'd like it</th></tr></thead>"
                "<tbody>" + "\n".join(rec_rows) + "</tbody>"
                "</table>"
            )
        else:
            recs_html = ""

        # Quotes
        quote_parts = []
        for q in cluster.get("quotes", []):
            quote_parts.append(
                f'<blockquote>'
                f'<p>{_esc(q.get("text",""))}</p>'
                f'<footer>— <em>{_esc(q.get("book",""))}</em>'
                + (f', {_esc(q.get("author",""))}' if q.get("author") else "")
                + "</footer></blockquote>"
            )
        quotes_html = "\n".join(quote_parts)

        clusters_html_parts.append(
            f'<section class="cluster">'
            f'<h2 class="cluster-name">{name}</h2>'
            f'<p class="cluster-desc">{description}</p>'
            + (f'<h3>Books ({len(cluster.get("books",[]))})</h3>{books_list}' if books_list else "")
            + (f"<h3>Recommended reads</h3>{recs_html}" if recs_html else "")
            + (f'<h3>Notable quotes</h3><div class="quotes">{quotes_html}</div>' if quotes_html else "")
            + "</section>"
        )

    clusters_html = "\n".join(clusters_html_parts)

    # ── Stats HTML ───────────────────────────────────────────────────────────
    top_subjects_html = "".join(
        f'<span class="tag">{_esc(s)}</span>' for s in stats["top_subjects"]
    )
    bars_html = _books_per_year_bars(stats["years"])

    summary_html = "".join(f"<p>{_esc(p.strip())}</p>" for p in analysis.get("summary", "").split("\n\n") if p.strip())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My Reading Analysis</title>
<style>
  :root {{
    --bg: #0f1117;
    --card: #1a1d27;
    --accent: #7c6af7;
    --accent2: #f7a26a;
    --text: #e2e4ed;
    --muted: #8b8fa8;
    --border: #2a2d3e;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 16px;
    line-height: 1.6;
    padding: 1rem;
    max-width: 800px;
    margin: 0 auto;
  }}
  h1 {{ font-size: 1.6rem; color: var(--accent); margin-bottom: 0.25rem; }}
  h2 {{ font-size: 1.2rem; margin: 1.5rem 0 0.5rem; }}
  h3 {{ font-size: 1rem; color: var(--muted); margin: 1rem 0 0.4rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 2rem; }}
  .section-header {{
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin: 2rem 0 1rem;
    color: var(--accent2);
    font-size: 1.3rem;
    font-weight: 600;
  }}
  .personality p {{ margin-bottom: 0.8rem; color: var(--text); }}
  .cluster {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1.5rem;
  }}
  .cluster-name {{ color: var(--accent); margin-top: 0; }}
  .cluster-desc {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 0.8rem; }}
  ul {{ padding-left: 1.2rem; }}
  li {{ margin-bottom: 0.3rem; font-size: 0.95rem; }}
  .book-title {{ font-weight: 500; }}
  .stars {{ color: #f5c518; letter-spacing: 1px; }}
  .no-rating {{ color: var(--muted); font-size: 0.8rem; }}
  .recs-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 0.5rem; }}
  .recs-table th {{ text-align: left; color: var(--muted); padding: 0.3rem 0.5rem; border-bottom: 1px solid var(--border); }}
  .recs-table td {{ padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
  .recs-table tr:last-child td {{ border-bottom: none; }}
  blockquote {{
    border-left: 3px solid var(--accent);
    padding: 0.6rem 1rem;
    margin: 0.6rem 0;
    background: rgba(124,106,247,0.08);
    border-radius: 0 8px 8px 0;
  }}
  blockquote p {{ font-style: italic; margin-bottom: 0.3rem; }}
  blockquote footer {{ font-size: 0.82rem; color: var(--muted); }}
  .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }}
  .stat-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
  }}
  .stat-value {{ font-size: 2rem; font-weight: 700; color: var(--accent); }}
  .stat-label {{ font-size: 0.8rem; color: var(--muted); margin-top: 0.2rem; }}
  .tag {{
    display: inline-block;
    background: rgba(124,106,247,0.15);
    color: var(--accent);
    border: 1px solid rgba(124,106,247,0.3);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.8rem;
    margin: 0.2rem;
  }}
  .bar-row {{ display: flex; align-items: center; gap: 0.6rem; margin: 0.4rem 0; font-size: 0.85rem; }}
  .bar-label {{ width: 2.5rem; color: var(--muted); text-align: right; flex-shrink: 0; }}
  .bar-track {{ flex: 1; background: var(--border); border-radius: 4px; height: 10px; }}
  .bar-fill {{ background: var(--accent); height: 100%; border-radius: 4px; min-width: 4px; }}
  .bar-count {{ width: 1.8rem; color: var(--muted); flex-shrink: 0; }}
  @media (max-width: 480px) {{
    .stats-grid {{ grid-template-columns: 1fr 1fr; }}
    .recs-table th:last-child, .recs-table td:last-child {{ display: none; }}
  }}
</style>
</head>
<body>

<h1>My Reading Analysis</h1>
<p class="meta">Generated {generated} &middot; {stats["total"]} books analyzed (last 2 years)</p>

<h2 class="section-header">Reading Personality</h2>
<div class="personality">
{summary_html}
</div>

<h2 class="section-header">Topic Clusters</h2>
{clusters_html}

<h2 class="section-header">Reading Stats</h2>
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-value">{stats["total"]}</div>
    <div class="stat-label">Books read</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{stats["avg_rating"] or "—"}</div>
    <div class="stat-label">Avg rating</div>
  </div>
</div>

{"<h3>Books per year</h3>" + bars_html if bars_html else ""}

{"<h3>Top subjects</h3><div>" + top_subjects_html + "</div>" if top_subjects_html else ""}

</body>
</html>"""
