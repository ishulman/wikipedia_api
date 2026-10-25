"""Render issue.json (real articles picked by pick.py) into one self-contained HTML page (dist/index.html).

Usage: python3 magazine/build.py
Images are read from magazine/images and embedded as data: URIs, because the
artifact page can only load images from data: URLs or its own uploads.
"""
import base64
import json
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
LESS_REASONS = ["Not my topic", "Too basic", "Too commercial", "Dull photograph"]


def data_uri(name):
    raw = (HERE / "images" / name).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def credit(a):
    return (f'<div class="credit">Image: <a href="{escape(a["url"], True)}" target="_blank" rel="noopener">'
            f'{escape(a["publisher"])}</a></div>')


def masthead(issue):
    pubs = len({a["publisher"] for a in issue["items"]})
    return f"""
<header class="masthead gutter">
  <div class="meta label"><span>No. {issue["number"]}</span><span>{escape(issue["date"])}</span></div>
  <h1>The Long <em>Afternoon</em></h1>
  <div class="meta label" style="margin-top:14px"><span>{len(issue["items"])} reads</span><span>{pubs} publications</span></div>
</header>"""


def byline(a):
    bits = [x for x in [("By " + a["byline"]) if a["byline"] else None, a["date"]] if x]
    return " · ".join(escape(x) for x in bits)


def cover(a):
    return f"""
<section class="cover" aria-label="Cover story">
  <figure>
    <img src="{data_uri(a["image"])}" alt="">
    <div class="scrim"><div class="gutter">
      <div class="kicker">{escape(a["section"])} · {escape(a["publisher"])}</div>
      <h2>{escape(a["title"])}</h2>
      <p>{byline(a)}</p>
      <a class="begin" href="#{a["id"]}" data-jump="{a["id"]}">Read the extract</a>
    </div></div>
  </figure>
  <div class="gutter">{credit(a)}</div>
</section>"""


def contents(items):
    lis = "".join(
        f'<li><a href="#{a["id"]}" data-jump="{a["id"]}"><span class="t">{escape(a["title"])}</span>'
        f'<span class="s label">{escape(a["section"])}</span><span class="m">{escape(a["publisher"])}</span></a></li>'
        for a in items)
    return f'<nav class="contents gutter" aria-label="In this issue"><div class="label">In this issue</div><ol>{lis}</ol></nav>'


def feature(a, first):
    image = "" if (first or not a["image"]) else f"""
  <figure>
    <img src="{data_uri(a["image"])}" alt="">
    <div class="gutter">{credit(a)}</div>
  </figure>"""
    head = "" if first else f"""
  <div class="head gutter">
    <div class="label">{escape(a["section"])} · {escape(a["publisher"])}</div>
    <h2>{escape(a["title"])}</h2>
    <p class="by">{byline(a)}</p>
  </div>"""
    return f"""
<article class="feature" id="{a["id"]}" data-article="{a["id"]}" style="{"padding-top:36px" if first else ""}">{head}{image}
  <div class="gutter">
    <blockquote class="excerpt">{escape(a["excerpt"])}</blockquote>
    <p class="readon"><a class="go" href="{escape(a["url"], True)}" target="_blank" rel="noopener">Read the full article on {escape(a["publisher"])}</a></p>
    <div class="react">
      <div class="row">
        <button type="button" class="btn" data-act="more" aria-pressed="false">More like this</button>
        <button type="button" class="btn" data-act="less" aria-pressed="false">Less</button>
        <button type="button" class="btn" data-act="save" aria-pressed="false">Save</button>
      </div>
      <div class="chips" hidden></div>
      <p class="hint" aria-live="polite"></p>
    </div>
  </div>
</article>"""


def trial(items):
    lis = "".join(
        f'<li class="source" data-source="{s["id"]}" data-name="{escape(s["name"], True)}">'
        f'<div class="n"><a href="{escape(s["url"], True)}" target="_blank" rel="noopener">{escape(s["name"])}</a></div>'
        f'<p>{escape(s["topics"])}</p>'
        f'<div class="row" style="display:flex;gap:10px;flex-wrap:wrap">'
        f'<button type="button" class="btn" data-decide="add" aria-pressed="false">Add to my sources</button>'
        f'<button type="button" class="btn" data-decide="pass" aria-pressed="false">Pass</button></div></li>'
        for s in items)
    return ('<section class="trial gutter"><div class="label">Discovery</div><h2>Sources on trial</h2>'
            "<p>Publications that match what you save. Add one and its articles start appearing in the issue.</p>"
            f'<ul class="sources">{lis}</ul></section>')


EDITOR = """
<section class="editor gutter"><div class="label">Standing orders</div><h2>Tell the editor</h2>
<p>Anything you want more or less of, a trip coming up, a mood. It is read before the next issue is picked.</p>
<form id="note-form">
  <label for="note" class="label">Your note</label>
  <textarea id="note" name="note" placeholder="More Italy before I go in spring. Fewer car auctions."></textarea>
  <button type="submit" class="btn">Send</button>
  <p class="hint" id="note-hint" aria-live="polite"></p>
</form></section>"""

END = """
<footer class="end gutter">
  <div class="mark" aria-hidden="true">&#10086;</div>
  <span class="label">End of issue</span>
  <p>That is everything for today. Nothing below this line is waiting for you.</p>
</footer>"""


def main():
    issue = json.loads((HERE / "issue.json").read_text())
    items = issue["items"]
    data = {"number": issue["number"], "lessReasons": LESS_REASONS,
            "articles": [{"id": a["id"], "section": a["section"], "title": a["title"],
                          "options": {"more": ["More from this publication", "More on this topic", "More by this writer"]}} for a in items]}
    html = (HERE / "template.html").read_text()
    for key, val in {
        "__MASTHEAD__": masthead(issue), "__COVER__": cover(items[0]), "__CONTENTS__": contents(items),
        "__FEATURES__": "".join(feature(a, i == 0) for i, a in enumerate(items)),
        "__TRIAL__": trial(issue["sources_on_trial"]), "__EDITOR__": EDITOR, "__END__": END, "__DATA__": json.dumps(data),
    }.items():
        html = html.replace(key, val)
    out = HERE / "dist" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"{out} {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
