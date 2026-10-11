#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check block references, recipe evidence and optionally the source registry."""
import argparse
import json
from pathlib import Path
import re

import build_blocks
from build_guides import recipe_anchor
from validate_wiki import Page

ROOT = build_blocks.ROOT


def validate(data, recipes, game=None):
    rows = data['blocks']
    assert len(rows) == len({b['id'] for b in rows}) == len({b['symbol'] for b in rows}) == data['catalogCount']
    assert {b['symbol'] for b in rows} == set(build_blocks.FAMILY_BY_BLOCK), 'Unreviewed registry membership'
    assert re.fullmatch(r'[0-9a-f]{40}', data['game']['commit'])
    assert data['game']['source'] == build_blocks.TABLE, 'Only the core block registry is supported'
    assert data['recipeGame'] == recipes['game'], 'Stale recipe provenance'
    ledger = json.loads((ROOT / 'data/features.json').read_text())
    assert data['acquisitionGame'] == ledger['game'], 'Stale acquisition provenance'
    catalogue = next(f for f in ledger['features'] if f['id'] == 'block-materials-catalogue')
    families = {f['id'] for f in data['families']}
    assert len(families) == len(data['families'])
    page = Page(build_blocks.render(data))
    recipe_page = Page((ROOT / 'guide-crafting.html').read_text())
    for b in rows:
        assert b['family'] in families
        assert b['anchor'] == 'block-' + b['symbol'].lower().replace('_', '-')
        assert b['anchor'] in page.ids and re.fullmatch(r'block-[a-z0-9-]+', b['anchor'])
        assert b['description'] and b['description'].endswith('.')
        assert len(b['color']) == 3 and all(0 <= c <= 1 for c in b['color'])
        expected = [r['name'] for r in recipes['recipes'] if r['output'] == b['name']]
        assert b.get('recipes', []) == expected, f'{b["symbol"]}: unsupported acquisition claim'
        assert 'howToGet' not in b, 'Unsupported acquisition field'
        if b['symbol'] in build_blocks.CREATIVE_ONLY and not expected:
            assert b.get('creativeOnly') is True
            assert build_blocks.CREATIVE_ONLY[b['symbol']] in catalogue['notes']
            assert b['acquisitionEvidence'] == 'data/features.json: block-materials-catalogue notes'
        else:
            assert 'creativeOnly' not in b and 'acquisitionEvidence' not in b, 'Unsupported acquisition claim'
        assert all(recipe_anchor(name) in recipe_page.ids for name in expected), 'Recipe link target missing'
    if game:
        assert data == build_blocks.build_data(game, recipes, ledger), 'Block data differs from the snapshot registry'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, help='Read-only exported snapshot with SNAPSHOT_COMMIT')
    args = parser.parse_args()
    data = json.loads((ROOT / 'data/blocks.json').read_text())
    validate(data, json.loads((ROOT / 'data/recipes.json').read_text()), args.game)
    assert (ROOT / 'blocks.html').read_text() == build_blocks.render(data), 'Stale blocks.html'
    print(f'PASS: {data["catalogCount"]} core blocks, stable anchors, colours and supported recipe links'
          + ('; exact snapshot match' if args.game else ''))


if __name__ == '__main__':
    main()
