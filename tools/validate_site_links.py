#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate local references in the published static HTML pages.

Pass a staged site directory (see tools/stage_site.py) to check exactly the
files GitHub Pages publishes; the default checks the repository root.
"""
import argparse
import re
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
    pages = sorted(root.rglob("*.html")) if root != ROOT else sorted(root.glob("*.html"))
    assert pages, "No published HTML pages"
    reports = [root / name for name in ("ABOUT.md", "NOTICE.md", "PERFORMANCE_ANALYSIS.md", "PERFORMANCE_OPTIMIZATION.md", "STREAMING_IMPROVEMENTS.md")]
    reports += sorted((root / "data" / "performance").rglob("*.md"))
    for page in [*pages, *reports]:
        if page.suffix == ".html":
            parser = References()
            parser.feed(page.read_text())
            refs = parser.refs
        else:
            refs = re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', page.read_text())
        for ref in refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc or not url.path:
                continue
            checked += 1
            path = unquote(url.path)
            target = (page.parent / path).resolve()
            if path.startswith("/") or not target.is_relative_to(root) or not target.exists():
                failures.append(f"{page.relative_to(root)}: broken/non-portable reference {ref}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(pages)} pages, {checked} local static references in {root.name or root}")

if __name__ == "__main__":
    main()
