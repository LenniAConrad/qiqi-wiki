# SPDX-License-Identifier: GPL-3.0-only
"""Shared navigation and topic membership for the static player wiki."""
from html import escape
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
TOPICS = json.loads((DATA / 'topics.json').read_text())['topics']
CATEGORIES = tuple((topic['id'], topic['title'], topic['page']) for topic in TOPICS)
ATLAS = (('atlas.html', 'Biomes'), ('animals.html', 'Animals'),
         ('islands.html', 'Islands'), ('scale.html', 'Scale'),
         ('performance.html', 'Performance'), ('features.html', 'Features'))
NAV = (('index.html', 'Home'),) + tuple(
    (page, label) for _, label, page in CATEGORIES
) + (('guides.html', 'All guides'), ('atlas.html', 'Atlas'), ('changelog.html', 'Changelog'))
GUIDE_SLUGS = {guide['page']: guide['id'] for guide in json.loads((DATA / 'guides.json').read_text())['guides']}


def topic_for_guide(slug):
    return next((topic for topic in TOPICS if slug in topic['guides']), None)


def topic_for_page(page):
    # Assigned guide membership takes precedence over a topic's cross-links.
    if page in GUIDE_SLUGS:
        return topic_for_guide(GUIDE_SLUGS[page])
    return next((topic for topic in TOPICS if page == topic['page'] or
                 any(href == page for href, _ in topic['references'])), None)


def links_html(links, current, related=None):
    out = []
    for href, label in links:
        marker = ' aria-current="page"' if href == current else (
            ' aria-current="true"' if href == related else '')
        out.append(f'<a href="{href}"{marker}>{escape(label)}</a>')
    return ''.join(out)


def nav_html(current):
    topic = topic_for_page(current)
    related = topic['page'] if topic else None
    if current == 'changelog-wiki.html':
        related = 'changelog.html'
    if current in {href for href, _ in ATLAS} and current != 'atlas.html':
        related = 'atlas.html'
    elif current.startswith('guide-') and not topic:
        related = 'guides.html'
    return '<nav class="wiki-nav" aria-label="Main">' + links_html(NAV, current, related) + '</nav>'


def header_html(current):
    header = ('<header class="site-header"><div class="site-brand">'
              '<a class="wordmark" href="index.html">Qiqi<span class="wordmark-light">Voxelgame wiki</span></a>'
              '<a class="header-search" href="index.html#search">Search the wiki <kbd>/</kbd></a></div>'
              '<details class="site-menu" open><summary>Browse the wiki</summary>' + nav_html(current))
    if current in {href for href, _ in ATLAS}:
        header += '<nav class="atlas-nav" aria-label="Atlas">' + links_html(ATLAS, current) + '</nav>'
    return header + '</details></header>'


def footer_html():
    return ('<footer><a class="wordmark" href="index.html">Qiqi</a>'
            '<p>Voxelgame player wiki · Base game</p><nav aria-label="Footer">'
            '<a href="guides.html">All guides</a><a href="changelog.html">Changelog</a><a href="features.html">Coverage and sources</a>'
            '<a href="ABOUT.md">About and provenance</a><a href="LICENSE">Licence</a></nav></footer>')
