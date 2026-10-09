#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate local references in the published static HTML pages."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.refs.append(value)

def main():
    failures = []
    checked = 0
    pages = sorted(ROOT.glob("*.html"))
    assert pages, "No published HTML pages"
    for page in pages:
        parser = References()
        parser.feed(page.read_text())
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc or not url.path:
                continue
            checked += 1
            path = unquote(url.path)
            target = (page.parent / path).resolve()
            if path.startswith("/") or not target.is_relative_to(ROOT) or not target.exists():
                failures.append(f"{page.name}: broken/non-portable reference {ref}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(pages)} pages, {checked} local static references")

if __name__ == "__main__":
    main()
