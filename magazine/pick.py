"""Compose issue.json from real feed items.

Each pick is (feed url, substring of the headline, section). The text shown on
the page is the publisher's own headline, byline and excerpt; nothing is rewritten.
Usage: python3 magazine/pick.py
"""
import hashlib, html, io, json, re
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image

from feeds import fetch, UA

HERE = Path(__file__).parent
HAGERTY = "https://www.hagerty.com/media/feed/"
CNT = "https://www.cntraveler.com/feed/rss"
LITHUB = "https://lithub.com/feed/"
AEON = "https://aeon.co/feed.rss"
PUBLISHERS = {HAGERTY: ("Hagerty", "https://www.hagerty.com/media"), CNT: ("Condé Nast Traveler", "https://www.cntraveler.com"),
              LITHUB: ("Literary Hub", "https://lithub.com"), AEON: ("Aeon", "https://aeon.co")}

PICKS = [
    (HAGERTY, "Chasing Autumn Colors", "Cars and the road"),
    (CNT, "Lofoten", "Travel"),
    (LITHUB, "Nina Simone", "Literature and culture"),
    (AEON, "Roman) man", "Ideas"),
    (CNT, "Finnish Ritual", "Slow living"),
    (HAGERTY, "Bullitt Isn", "Cars and the road"),
]


def clean(t):
    t = html.unescape(re.sub(r"\s+", " ", t)).strip()
    t = re.sub(r"\s*\[…\]$|\s*\[&hellip;\]$", "…", t)
    return re.sub(r"\s*-?\s*by [^-]+Read on Aeon$", "", t).strip()


def main():
    cache, items = {}, []
    for feed, key, section in PICKS:
        cache.setdefault(feed, fetch(feed))
        it = next(i for i in cache[feed] if key in i["title"])
        iid = hashlib.sha1(it["link"].encode()).hexdigest()[:10]
        image = None
        if it["img"]:
            r = requests.get(it["img"], headers=UA, timeout=30)
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            im.thumbnail((1000, 1000))
            name = f"{iid}.jpg"
            im.save(HERE / "images" / name, quality=72, optimize=True, progressive=True)
            image = name
        pub, pub_url = PUBLISHERS[feed]
        items.append({
            "id": iid, "section": section, "publisher": pub, "publisher_url": pub_url,
            "title": clean(it["title"]), "byline": it["by"] or None,
            "date": datetime.strptime(it["date"][:16], "%a, %d %b %Y").strftime("%-d %B %Y"),
            "excerpt": clean(it["desc"]), "url": it["link"], "image": image,
        })
    issue = {"title": "The Long Afternoon", "number": 1, "date": "Sunday 25 October 2026", "items": items,
             "sources_on_trial": [
                 {"id": "classic-driver", "name": "Classic Driver Magazine", "url": "https://www.classicdriver.com/en/magazine", "topics": "Cars"},
                 {"id": "paris-review-daily", "name": "The Paris Review Daily", "url": "https://www.theparisreview.org/blog", "topics": "Literature"},
                 {"id": "cereal", "name": "Cereal", "url": "https://readcereal.com", "topics": "Travel, slow living"},
                 {"id": "monocle", "name": "Monocle", "url": "https://monocle.com", "topics": "Travel, design, lifestyle"}]}
    (HERE / "issue.json").write_text(json.dumps(issue, indent=2, ensure_ascii=False))
    for i in items: print(i["section"], "|", i["publisher"], "|", i["title"][:60], "|", i["image"])


if __name__ == "__main__":
    main()
