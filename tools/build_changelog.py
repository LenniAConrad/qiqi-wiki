#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Render dated, curated game and wiki histories without a runtime dataset."""
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


def source_notes(row, source):
    refs = []
    for ref in row['refs']:
        sha = ref['commit']
        label = f'<code>{sha[:8]}</code>'
        if source['publicCommitLinks']:
            label = f'<a href="{source["repository"]}/commit/{sha}">{label}</a>'
        refs.append(f'<li>{label} · <time datetime="{ref["date"]}">{date_label(ref["date"])}</time></li>')
    return ('<details class="change-sources"><summary>Source ' +
            ('commit' if len(refs) == 1 else 'commits') + '</summary><ul>' + ''.join(refs) + '</ul></details>')


def entry_html(row, source):
    return ('<li><p class="change-label">' + escape(row['kind']) + ' · ' + escape(row['area']) +
            '</p><p>' + escape(row['text']) + '</p>' + source_notes(row, source) + '</li>')


def render(data, key):
    source = next(item for item in data['sources'] if item['id'] == key)
    periods = [item for item in data['periods'] if item['source'] == key]
    sections = ([('compatibility', 'Before updating')] if key == 'game' else []) + [
        (period['id'], date_label(period['date'])) for period in periods] + [('coverage', 'Coverage and sources')]
    title = 'Game changelog' if key == 'game' else 'Wiki changelog'
    opening = article_open(title, source['page'],
        'Dated additions, changes and fixes to the base game.' if key == 'game' else
        'Changes to the guides, references and website.', sections, 'build_changelog.py')
    opening = opening.replace('guide-page reference-page', 'guide-page reference-page changelog-page')
    out = [opening, '<nav class="change-switch" aria-label="Changelog">']
    for item in data['sources']:
        marker = ' aria-current="page"' if item['id'] == key else ''
        out.append(f'<a href="{item["page"]}"{marker}>{item["title"]} changes</a>')
    out.append('</nav><p class="change-cutoff">Source history through '
               f'<strong>{date_label(source["last"]["date"])}</strong> · '
               f'<code>{source["last"]["commit"][:8]}</code>. These are commit dates, not numbered releases. '
               '<a href="#coverage">Coverage and limits</a>.</p>')
    if key == 'game':
        out.append('<section class="guide-section" id="compatibility"><h2>Before updating</h2>'
                   '<p>Compatibility at the reviewed revision. See also '
                   '<a href="guide-saves.html">Saves and world files</a> and '
                   '<a href="guide-building.html">Building</a>.</p><ul class="change-list">')
        out.extend(entry_html(row, source) for row in data['compatibility'])
        out.append('</ul></section>')
    for period in periods:
        out.append(f'<section class="guide-section change-date" id="{period["id"]}">'
                   f'<h2><time datetime="{period["date"]}">{date_label(period["date"])}</time></h2>'
                   f'<p class="change-title">{escape(period["title"])}</p><ul class="change-list">')
        out.extend(entry_html(row, source) for row in period['entries'])
        out.append('</ul><p class="change-back"><a href="#title">Back to contents</a></p></section>')
    out.append('<section class="guide-section" id="coverage"><h2>Coverage and sources</h2>'
               f'<p>{escape(data["method"])}</p><dl class="change-range">')
    for label, ref in [('First recorded commit', source['first']), ('Reviewed through', source['last'])]:
        out.append(f'<dt>{label}</dt><dd>{date_label(ref["date"])} · <code>{ref["commit"]}</code></dd>')
    out.append(f'<dt>Available history</dt><dd>{source["commitCount"]} commits; '
               f'{len(periods)} dated groups shown.</dd></dl>')
    if key == 'game':
        out.append('<p>Game commit identifiers come from the checked source repository. Its hosted history '
                   'was unavailable to a public request during review, so these identifiers are shown '
                   'without public links. Compatibility was checked in the save loader, blueprint codec '
                   'and network protocol at the reviewed revision.</p>')
    else:
        out.append(f'<p>Browse the <a href="{source["repository"]}/commits/{source["last"]["commit"]}/">'
                   'wiki source history at this cutoff</a>. Source links below each entry open the '
                   'recorded wiki commit.</p>')
    out.append('<ul>' + ''.join(f'<li>{escape(gap)}</li>' for gap in data['gaps']) + '</ul>'
               '<p><a href="features.html">Feature coverage and sources</a> · '
               '<a href="guide-not-in-game.html">Planned features</a></p></section>' + article_close())
    return ''.join(out)


def search_records(data):
    # Keep history summaries concise: the full chronology stays on its own pages.
    for source in data['sources']:
        yield dict(title=f'{source["title"]} changelog',
                   text=f'Dated {source["title"].lower()} additions, changes and fixes; '
                        f'{source["first"]["date"]} to {source["last"]["date"]}.',
                   href=source['page'], kind='Changelog')
    for period in data['periods']:
        source = next(item for item in data['sources'] if item['id'] == period['source'])
        yield dict(title=f'{source["title"]} changes · {date_label(period["date"])}',
                   text=period['title'], href=source['page'] + '#' + period['id'], kind='Changelog')


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
