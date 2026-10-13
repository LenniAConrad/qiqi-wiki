#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate chronology and source receipts; optionally recheck pinned Git history."""
import argparse
from datetime import date
import re
import subprocess

from build_changelog import ROOT, read, render

KINDS = {'Added', 'Changed', 'Fixed', 'Compatibility'}
HEX = re.compile(r'[0-9a-f]{40}')


def validate(data):
    assert data['schema'] == 2
    reviewed = date.fromisoformat(data['reviewed'])
    sources = {item['id']: item for item in data['sources']}
    assert set(sources) == {'game', 'wiki'} and len(data['sources']) == 2
    for key, source in sources.items():
        assert source['page'] == ('changelog.html' if key == 'game' else 'changelog-wiki.html')
        assert source['repository'] == f'https://github.com/LenniAConrad/{"qiqi" if key == "game" else "qiqi-wiki"}'
        assert source['releases'] in {'none', 'unavailable', 'listed'}
        assert isinstance(source['publicCommitLinks'], bool)
        assert date.fromisoformat(source['first']['date']) <= date.fromisoformat(source['last']['date']) <= reviewed
        assert HEX.fullmatch(source['first']['commit']) and HEX.fullmatch(source['last']['commit'])
        assert source['commitCount'] > 0
    ids, days = set(), {'game': [], 'wiki': []}
    for period in data['periods']:
        source = sources[period['source']]
        assert period['id'] == f'{source["id"]}-{period["date"]}'
        assert period['id'] not in ids, 'Duplicate date group'
        ids.add(period['id'])
        days[source['id']].append(period['date'])
        assert source['first']['date'] <= period['date'] <= source['last']['date'], 'Date outside covered range'
        assert period['title'].strip() and period['entries']
        assert period['publicTitle'].strip() and len(period['publicTitle']) <= 100
        assert any(row['publicSummary'] is not None for row in period['entries']), 'Empty public date group'
        for row in period['entries']:
            validate_entry(row, source)
            assert all(ref['date'] == period['date'] for ref in row['refs']), 'Backdated source in date group'
    for key, values in days.items():
        assert values == sorted(values, reverse=True), 'Dates must be newest first'
        assert values[-1] == sources[key]['first']['date'], 'Earliest history missing'
        assert values[0] == sources[key]['last']['date'], 'Latest history missing'
    assert data['method'] and data['gaps'] and data['compatibility']
    for row in data['compatibility']:
        validate_entry(row, sources['game'])


def validate_entry(row, source):
    assert row['kind'] in KINDS and row['area'].strip() and row['text'].strip()
    assert 'publicSummary' in row, 'Review a public summary explicitly'
    summary = row['publicSummary']
    if summary is None:
        assert row.get('privateReason', '').strip(), 'Explain an internal-only entry'
    else:
        assert isinstance(summary, str) and summary.strip() and len(summary) <= 220, 'Keep public entries brief'
        assert not re.search(r'\b(?:[0-9a-f]{8,40}|commits?|gate|receipts?)\b', summary, re.I), \
            'Keep development receipts out of public summaries'
    assert row['refs'], 'A change needs source evidence'
    assert len({ref['commit'] for ref in row['refs']}) == len(row['refs'])
    for ref in row['refs']:
        assert HEX.fullmatch(ref['commit']), 'Use full source hashes'
        date.fromisoformat(ref['date'])
        assert source['first']['date'] <= ref['date'] <= source['last']['date'], 'Source outside covered range'


def verify_repository(data, key, repo):
    """Read committed objects only, without fetching or altering either checkout."""
    source = next(item for item in data['sources'] if item['id'] == key)
    output = subprocess.check_output(['git', '-C', str(repo), 'log', '--format=%H\t%cs', source['last']['commit']], text=True)
    history = dict(row.split('\t') for row in output.splitlines())
    assert len(history) == source['commitCount'], 'Pinned history count differs'
    roots = subprocess.check_output(['git', '-C', str(repo), 'rev-list', '--max-parents=0', source['last']['commit']], text=True).splitlines()
    assert roots == [source['first']['commit']], 'History must start at the repository root'
    refs = [source['first'], source['last']]
    refs += [ref for period in data['periods'] if period['source'] == key for row in period['entries'] for ref in row['refs']]
    if key == 'game':
        refs += [ref for row in data['compatibility'] for ref in row['refs']]
    for ref in refs:
        assert history.get(ref['commit']) == ref['date'], f'Unreachable or misdated source: {ref["commit"]}'
    print(f'PASS: {key}, {len(history)} commits in pinned history; {len(refs)} source receipts')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', help='read-only game repository')
    parser.add_argument('--wiki', help='read-only wiki repository')
    args = parser.parse_args()
    data = read()
    validate(data)
    for source in data['sources']:
        assert (ROOT / source['page']).read_text() == render(data, source['id']), 'Stale changelog page'
    for key in ('game', 'wiki'):
        if getattr(args, key):
            verify_repository(data, key, getattr(args, key))
    print('PASS: chronology, evidence, coverage ranges and generated changelogs')


if __name__ == '__main__':
    main()
