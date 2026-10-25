"""Render issue.json into a single self-contained HTML page (dist/index.html).

Usage: python3 magazine/build.py
Images are read from magazine/images and embedded as data: URIs, because the
artifact page can only load images from data: URLs or its own uploads.
"""
import base64
import json
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
LESS_REASONS = ["Not my topic", "Too basic", "Too long", "Dull photograph"]


def words(a):
    return sum(len(p.split()) for p in a["body"]) + len(a["standfirst"].split())


def minutes(a):
    return max(2, -(-words(a) // 190))


def data_uri(name):
    raw = (HERE / "images" / name).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def credit(img):
    return (
        f'<div class="credit">Photograph: <a href="{escape(img["page"], True)}" '
        f'target="_blank" rel="noopener">{escape(img["credit"])}, via Wikimedia Commons</a></div>'
    )


def masthead(issue, total_min):
    return f"""
<header class="masthead gutter">
  <div class="meta label"><span>No. {issue["number"]}</span><span>{escape(issue["date"])}</span></div>
  <h1>The Long <em>Afternoon</em></h1>
  <div class="meta label" style="margin-top:14px"><span>{len(issue["articles"])} features and a notebook</span><span>About {total_min} min</span></div>
</header>"""


def cover(a):
    img = a["image"]
    return f"""
<section class="cover" aria-label="Cover story">
  <figure>
    <img src="{data_uri(img["file"])}" alt="{escape(img["alt"], True)}" style="object-position:{img["pos"]}">
    <div class="scrim"><div class="gutter">
      <div class="kicker">{escape(a["section"])} · Cover story</div>
      <h2>{escape(a["title"])}</h2>
      <p>{escape(a["standfirst"])}</p>
      <a class="begin" href="#{a["id"]}" data-jump="{a["id"]}">Begin reading</a>
    </div></div>
  </figure>
  <div class="gutter">{credit(img)}</div>
</section>"""


def contents(articles):
    items = "".join(
        f'<li><a href="#{a["id"]}" data-jump="{a["id"]}"><span class="t">{escape(a["title"])}</span>'
        f'<span class="s label">{escape(a["section"])}</span><span class="m">{minutes(a)} min</span></a></li>'
        for a in articles
    )
    return f'<nav class="contents gutter" aria-label="In this issue"><div class="label">In this issue</div><ol>{items}</ol></nav>'


def feature(a, first):
    img = a["image"]
    paras = "".join(f"<p>{escape(p)}</p>" for p in a["body"])
    src = a["source"]
    image = "" if first else f"""
  <figure>
    <img src="{data_uri(img["file"])}" alt="{escape(img["alt"], True)}" style="object-position:{img["pos"]}">
    <div class="gutter">{credit(img)}</div>
  </figure>"""
    head = "" if first else f"""
  <div class="head gutter">
    <div class="label">{escape(a["section"])}</div>
    <h2>{escape(a["title"])}</h2>
    <p class="stand">{escape(a["standfirst"])}</p>
  </div>"""
    return f"""
<article class="feature" id="{a["id"]}" data-article="{a["id"]}" style="{"padding-top:44px" if first else ""}">{head}{image}
  <div class="gutter">
    <div class="prose">{paras}</div>
    <p class="further">Read further: <a href="{escape(src["url"], True)}" target="_blank" rel="noopener">{escape(src["name"])}</a></p>
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


def notebook(items):
    dl = "".join(f"<div><dt>{escape(i['label'])}</dt><dd>{escape(i['text'])}</dd></div>" for i in items)
    return f'<section class="notebook"><div class="gutter"><div class="label">Between the features</div><h2>Notebook</h2><dl>{dl}</dl></div></section>'


def trial(items):
    lis = "".join(
        f'<li class="source" data-source="{s["id"]}" data-name="{escape(s["name"], True)}">'
        f'<div class="n"><a href="{escape(s["url"], True)}" target="_blank" rel="noopener">{escape(s["name"])}</a></div>'
        f'<p>{escape(s["why"])}</p>'
        f'<div class="row" style="display:flex;gap:10px;flex-wrap:wrap">'
        f'<button type="button" class="btn" data-decide="add" aria-pressed="false">Add to my sources</button>'
        f'<button type="button" class="btn" data-decide="pass" aria-pressed="false">Pass</button></div></li>'
        for s in items
    )
    return (
        '<section class="trial gutter"><div class="label">Discovery</div><h2>Sources on trial</h2>'
        "<p>New places to read from, proposed from what you saved. Each accepted source gets a month of trial, "
        "and the ones you keep ignoring are dropped.</p>"
        f'<ul class="sources">{lis}</ul></section>'
    )


EDITOR = """
<section class="editor gutter"><div class="label">Standing orders</div><h2>Tell the editor</h2>
<p>Anything you want more or less of, a trip coming up, a mood. It is read before the next issue is assembled.</p>
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
    arts = issue["articles"]
    total = sum(minutes(a) for a in arts) + 2
    features = "".join(feature(a, i == 0) for i, a in enumerate(arts))
    data = {
        "number": issue["number"],
        "lessReasons": LESS_REASONS,
        "articles": [{"id": a["id"], "section": a["section"], "title": a["title"], "options": a["options"]} for a in arts],
    }
    html = (HERE / "template.html").read_text()
    for key, val in {
        "__MASTHEAD__": masthead(issue, total),
        "__COVER__": cover(arts[0]),
        "__CONTENTS__": contents(arts),
        "__FEATURES__": features,
        "__NOTEBOOK__": notebook(issue["notebook"]),
        "__TRIAL__": trial(issue["sources_on_trial"]),
        "__EDITOR__": EDITOR,
        "__END__": END,
        "__DATA__": json.dumps(data),
    }.items():
        html = html.replace(key, val)
    out = HERE / "dist" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"{out} {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
