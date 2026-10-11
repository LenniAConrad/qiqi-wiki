#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate local references in the published static HTML pages.

Pass a staged site directory (see tools/stage_site.py) to check exactly the
files GitHub Pages publishes; the default checks the repository root.
"""
import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="site directory to check")
    root = parser.parse_args().root.resolve()
    failures = []
    checked = 0
    pages = sorted(root.glob("*.html"))
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
            if path.startswith("/") or not target.is_relative_to(root) or not target.exists():
                failures.append(f"{page.name}: broken/non-portable reference {ref}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(pages)} pages, {checked} local static references in {root.name or root}")

if __name__ == "__main__":
    main()
