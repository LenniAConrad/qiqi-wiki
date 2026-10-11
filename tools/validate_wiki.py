# SPDX-License-Identifier: GPL-3.0-only
"""Check generated home/search, shared navigation and article link targets."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import build_wiki
import wiki_layout

ROOT = build_wiki.ROOT


class Page(HTMLParser):
    def __init__(self, value):
        super().__init__()
        self.ids = set()
        self.nav = None
        self.breadcrumb = False
        self.contents = False
        self.anchors = []
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'nav':
            self.nav = attrs.get('aria-label')
            self.breadcrumb |= self.nav == 'Breadcrumb'
            self.contents |= self.nav == 'On this page'
        if tag == 'a' and self.nav == 'On this page':
            self.anchors.append(attrs.get('href'))

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.nav = None


def validate():
    assert (ROOT / 'index.html').read_text() == build_wiki.render_home(), 'Stale home: run tools/build_wiki.py'
    assert (ROOT / 'data/search.js').read_text() == build_wiki.search_script(), 'Stale search: run tools/build_wiki.py'
    pages = {}
    for path in ROOT.glob('*.html'):
        value = path.read_text()
        assert wiki_layout.header_html(path.name) in value, f'{path.name}: shared header differs'
        assert 'href="wiki.css"' in value, f'{path.name}: shared styles missing'
        page = Page(value)
        pages[path.name] = page
        if path.name.startswith('guide-'):
            assert page.breadcrumb and page.contents, f'{path.name}: article breadcrumb/contents missing'
            assert all(href.startswith('#') and href[1:] in page.ids for href in page.anchors), \
                f'{path.name}: contents target missing'
    for href, _ in wiki_layout.NAV:
        url = urlsplit(href)
        assert url.path in pages, f'Navigation page missing: {href}'
        assert not url.fragment or url.fragment in pages[url.path].ids, f'Category target missing: {href}'
    for record in build_wiki.search_records():
        url = urlsplit(record['href'])
        assert not url.scheme and not url.netloc and not url.path.startswith('/'), 'Search must stay offline/relative'
        assert url.path in pages, f'Search target missing: {record["href"]}'
        if url.fragment and not url.fragment.startswith('biome='):
            assert url.fragment in pages[url.path].ids, f'Search anchor missing: {record["href"]}'
    print(f'PASS: {len(pages)} shared wiki headers, article contents, category targets and '
          f'{len(build_wiki.search_records())} current offline search records')


if __name__ == '__main__':
    validate()
