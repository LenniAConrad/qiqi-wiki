# SPDX-License-Identifier: GPL-3.0-only
"""Shared static navigation for the wiki builders and existing atlas pages."""
from html import escape

CATEGORIES = (
    ('getting-started', 'Getting started', 'guide-getting-started.html'),
    ('controls', 'Controls', 'guide-controls.html'),
    ('crafting', 'Crafting', 'guide-crafting.html'),
    ('blocks', 'Blocks', None), ('mobs', 'Mobs', None),
    ('building', 'Building', None), ('exploration', 'Exploration', None),
    ('troubleshooting', 'Troubleshooting', 'guide-troubleshooting.html'),
)
ATLAS = (('atlas.html', 'Biomes'), ('animals.html', 'Animals'),
         ('islands.html', 'Islands'), ('scale.html', 'Scale'),
         ('performance.html', 'Performance'), ('features.html', 'Features'))
NAV = (('index.html', 'Home'),) + tuple(
    (page or f'index.html#{key}', label) for key, label, page in CATEGORIES
) + (('guides.html', 'Guides'), ('atlas.html', 'Atlas'))


def links_html(links, current, related=None):
    out = []
    for href, label in links:
        marker = ' aria-current="page"' if href == current else (
            ' aria-current="true"' if href == related else '')
        out.append(f'<a href="{href}"{marker}>{escape(label)}</a>')
    return ''.join(out)


def nav_html(current):
    related = None
    if current in {href for href, _ in ATLAS} and current != 'atlas.html':
        related = 'atlas.html'
    elif current.startswith('guide-') and current not in {href for href, _ in NAV}:
        related = 'guides.html'
    return '<nav class="wiki-nav" aria-label="Main">' + links_html(NAV, current, related) + '</nav>'


def header_html(current):
    header = ('<header class="site-header"><div class="site-brand">'
              '<a class="wordmark" href="index.html"><span class="mark" aria-hidden="true">▧</span>'
              ' Qiqi <span class="wordmark-light">Voxelgame wiki</span></a>'
              '<span class="wiki-edition">Player reference</span></div>' + nav_html(current))
    if current in {href for href, _ in ATLAS}:
        header += '<nav class="atlas-nav" aria-label="Atlas">' + links_html(ATLAS, current) + '</nav>'
    return header + '</header>'


def footer_html():
    return ('<footer><a class="wordmark" href="index.html">Qiqi</a>'
            '<p>Voxelgame player wiki</p><a href="ABOUT.md">About and provenance</a></footer>')
