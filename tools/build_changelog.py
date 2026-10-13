#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Render brief daily updates; keep full source evidence in the maintenance data."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path

from reference_layout import article_close, article_open

ROOT = Path(__file__).resolve().parents[1]


def read():
    return json.loads((ROOT / 'data/changelog.json').read_text())


def date_label(value):
    return date.fromisoformat(value).strftime('%-d %B %Y')


def public_entries(rows):
    """Use reviewed player summaries only; never fall back to internal narratives."""
    return [row['publicSummary'] for row in rows if row['publicSummary'] is not None]


def list_html(rows):
    return '<ul class="change-list">' + ''.join(
        '<li>' + escape(text) + '</li>' for text in public_entries(rows)) + '</ul>'


def render(data, key):
    source = next(item for item in data['sources'] if item['id'] == key)
    periods = [item for item in data['periods'] if item['source'] == key]
    sections = ([('compatibility', 'Updating a world')] if key == 'game' else []) + [
        (period['id'], date_label(period['date'])) for period in periods] + [('coverage', 'About this list')]
    title = 'Game changelog' if key == 'game' else 'Wiki changelog'
    opening = article_open(title, source['page'],
        'What changed in the game, day by day.' if key == 'game' else
        'New pages, pictures and improvements to the wiki.', sections, 'build_changelog.py')
    opening = opening.replace('guide-page reference-page', 'guide-page reference-page changelog-page')
    out = [opening, '<nav class="change-switch" aria-label="Changelog">']
    for item in data['sources']:
        marker = ' aria-current="page"' if item['id'] == key else ''
        out.append(f'<a href="{item["page"]}"{marker}>{item["title"]} changes</a>')
    out.append('</nav><p class="change-cutoff">Selected updates through '
               f'<time datetime="{source["last"]["date"]}">{date_label(source["last"]["date"])}</time>.</p>')
    if key == 'game':
        out.append('<details class="change-updating" id="compatibility"><summary>Updating a world</summary>'
                   + list_html(data['compatibility']) +
                   '<p><a href="guide-saves.html">Saves and world files</a> · '
                   '<a href="guide-building.html#structure-library">Moving a build</a></p></details>')
    for period in periods:
        out.append(f'<section class="guide-section change-date" id="{period["id"]}">'
                   f'<h2><time datetime="{period["date"]}">{date_label(period["date"])}</time></h2>'
                   + list_html(period['entries']) + '</section>')
    out.append('<section class="guide-section" id="coverage"><h2>About this list</h2>'
               f'<p>Selected {"base-game" if key == "game" else "wiki"} changes from '
               f'{date_label(source["first"]["date"])} to {date_label(source["last"]["date"])}. '
               'Dates follow the recorded history; they are not numbered releases. '
               'Early entries sometimes group several changes.</p></section>' + article_close())
    return ''.join(out)


def search_records(data):
    for source in data['sources']:
        yield dict(title=f'{source["title"]} changelog',
                   text=f'Daily {source["title"].lower()} additions, changes and fixes; '
                        f'{source["first"]["date"]} to {source["last"]["date"]}.',
                   href=source['page'], kind='Changelog')
    for period in data['periods']:
        source = next(item for item in data['sources'] if item['id'] == period['source'])
        yield dict(title=f'{source["title"]} changes · {date_label(period["date"])}',
                   text=period['publicTitle'],
                   href=source['page'] + '#' + period['id'], kind='Changelog')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = read()
    for source in data['sources']:
        path, output = ROOT / source['page'], render(data, source['id'])
        if args.check:
            if not path.exists() or path.read_text() != output:
                raise SystemExit(f'Stale {path.name}: run tools/build_changelog.py')
        else:
            path.write_text(output)
    print('PASS: two current changelog pages' if args.check else 'Built game and wiki changelogs')


if __name__ == '__main__':
    main()
