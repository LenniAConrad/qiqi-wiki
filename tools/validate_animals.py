#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate the portable animal catalog, images, habitats and optional source match."""
import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
from PIL import Image
from build_animals import browser_catalog

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, help='Also verify exact source hashes against this checkout')
    args = parser.parse_args()
    data = json.loads((ROOT / 'data/animals.json').read_text())
    assert date.fromisoformat(data['date']).isoformat() == data['date']
    assert {'crates/voxelgame-render/src/atlas.rs', 'crates/voxelgame-render/src/shader.wgsl'} <= set(data['provenance']['sourceHashes']), 'Animal provenance must include texture and flat-palette sources'
    if capture := data['provenance'].get('capture'):
        assert all(re.fullmatch('[0-9a-f]{40}', capture[key]) for key in ('gameCommit', 'gameTree'))
        assert all(re.fullmatch('[0-9a-f]{64}', capture[key]) for key in
                   ('sourceManifestSha256', 'renderReceiptSha256', 'exporterSha256', 'captureDriverSha256'))
        assert capture['resolution'] == [512, 512] and capture['blenderVersion']
        assert capture['engine'] in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE')
        assert capture['renderSettings']['background'] is True
    encoded = (ROOT / 'data/animals.js').read_text().split('window.ANIMAL_ATLAS = ', 1)[1].rstrip().removesuffix(';')
    assert json.loads(encoded) == browser_catalog(data), 'Offline display data differs from the full catalog'
    assert hashlib.sha256((ROOT / 'tools/render_animals.py').read_bytes()).hexdigest() == data['provenance']['renderScriptSha256']
    rows = data['animals']
    assert isinstance(data['catalogCount'], int) and data['catalogCount'] > 0
    assert len(rows) == len({a['id'] for a in rows}) == len({a['slug'] for a in rows}) == data['catalogCount']
    assert [a['name'] for a in rows] == sorted(a['name'] for a in rows)
    biomes = json.loads((ROOT / 'data/biomes.json').read_text())['biomes']
    assert data['biomes'] == {b['id']: b['name'] for b in biomes}
    assert {a['category'] for a in rows} == {'Mammals', 'Birds', 'Fish', 'Reptiles & amphibians', 'Invertebrates'}
    paths = set()
    hashes = set()
    for a in rows:
        assert a['description'] and a['habitats'], a['id']
        assert len(a['habitats']) == len(set(a['habitats']))
        assert set(a['habitats']) <= set(data['biomes'])
        assert len(a['sizeMetres']) == 3 and all(math.isfinite(n) and 0 < n < 30 for n in a['sizeMetres'])
        assert len(a['views']) == 4
        assert {(v['pose'], v['angle']) for v in a['views']} == {(p, v) for p in ['idle', 'stride'] for v in ['three-quarter', 'side']}
        for v in a['views']:
            path = ROOT / v['image']
            assert path.resolve().is_relative_to((ROOT / 'images/animals').resolve())
            assert path not in paths; paths.add(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == v['imageSha256'], path
            assert digest not in hashes, ('duplicate view', path)
            hashes.add(digest)
            assert all(len(v[k]) == 64 for k in ['meshSha256', 'renderSha256'])
            with Image.open(path) as image:
                assert image.size == (512, 512)
                image.verify()
    if args.game:
        for name, expected in data['provenance']['sourceHashes'].items():
            assert hashlib.sha256((args.game / name).read_bytes()).hexdigest() == expected, name
    print(f'PASS: {len(rows)} animals, {len(paths)} unique 512px model views, habitat links, dimensions and provenance.')

if __name__ == '__main__':
    main()
