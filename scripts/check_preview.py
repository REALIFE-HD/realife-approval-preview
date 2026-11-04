#!/usr/bin/env python3
"""Validate preview shell and PWA assets without deployment or credentials."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/realife-approval-preview/"
class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = False
        self.title_text = []
        self.assets = []
        self.manifest = None
        self.noindex = False
        self.root = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.title = True
        if tag == "div" and a.get("id") == "root":
            self.root = True
        if tag == "meta" and a.get("name") == "robots" and "noindex" in a.get("content", ""):
            self.noindex = True
        if tag == "script" and a.get("src"):
            self.assets.append(a["src"])
        if tag == "link":
            if a.get("rel") in {"stylesheet", "icon", "apple-touch-icon"} and a.get("href"):
                self.assets.append(a["href"])
            if a.get("rel") == "manifest":
                self.manifest = a.get("href")

    def handle_endtag(self, tag):
        if tag == "title":
            self.title = False

    def handle_data(self, text):
        if self.title:
            self.title_text.append(text)

page = Page()
page.feed((ROOT / "index.html").read_text(encoding="utf-8"))
assert page.root and page.noindex and "".join(page.title_text).strip(), "invalid preview HTML shell"
assert page.manifest, "manifest missing"
assert page.assets, "no JS/CSS assets declared"
for ref in page.assets + [page.manifest]:
    parsed = urlsplit(ref)
    if parsed.scheme or parsed.netloc:
        continue
    assert ref.startswith(PREFIX), f"wrong preview base path: {ref}"
    path = ROOT / parsed.path[len(PREFIX):]
    assert path.is_file(), f"missing referenced asset: {path.relative_to(ROOT)}"
manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
assert manifest.get("display") == "standalone" and manifest.get("icons"), "invalid PWA manifest"
for item in manifest["icons"]:
    icon = ROOT / item["src"]
    assert icon.is_file() and icon.stat().st_size > 0, f"missing icon: {icon}"
print("Approval preview assets and manifest: PASS")
