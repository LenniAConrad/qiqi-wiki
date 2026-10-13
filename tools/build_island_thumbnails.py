#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build small island previews without changing the full-size evidence images.

The maps and panoramas were compared with BOX and LANCZOS at 480 pixels;
LANCZOS retained the small terrain boundaries better in these particular views.
This policy is specific to this collection, not a filter preset for other art.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, features

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/island-thumbnails.json'
SCRIPT = 'data/island-thumbnails.js'
WIDTHS = (480, 960)
POLICY = {'map': {'resample': 'LANCZOS', 'quality': 88},
          'panorama': {'resample': 'LANCZOS', 'quality': 88}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_views(root):
    catalog = json.loads((root / 'data/islands.json').read_text())
    return [view for island in catalog['islands'] for view in island['views'] if view['type'] in POLICY]


def script(manifest):
    lookup = {entry['source']: [[item['width'], item['path']] for item in entry['variants']]
              for entry in manifest['images']}
    return '/* SPDX-License-Identifier: GPL-3.0-only */\nwindow.ISLAND_THUMBNAILS = ' + json.dumps(
        lookup, separators=(',', ':')) + ';\n'


def generate(root=ROOT):
    manifest = {'schema': 1, 'catalog': 'data/islands.json', 'policy': POLICY,
                'encoder': {'format': 'WebP', 'method': 6, 'pillow': Image.__version__,
                            'libwebp': features.version('webp')}, 'images': []}
    for view in source_views(root):
        source = root / view['image']
        entry = {'source': view['image'], 'sourceSha256': digest(source),
                 'kind': view['type'], 'variants': []}
        with Image.open(source) as image:
            entry.update(sourceWidth=image.width, sourceHeight=image.height)
            for width in WIDTHS:
                assert width < image.width, f'Thumbnails must not upscale: {source}'
                height = round(image.height * width / image.width)
                relative = f'images/thumbnails/islands/{source.stem}--{width}.webp'
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                settings = POLICY[view['type']]
                image.resize((width, height), getattr(Image.Resampling, settings['resample'])).save(
                    target, 'WEBP', quality=settings['quality'], method=6)
                entry['variants'].append({'path': relative, 'width': width, 'height': height,
                                          'bytes': target.stat().st_size, 'sha256': digest(target)})
        manifest['images'].append(entry)
    (root / MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n')
    (root / SCRIPT).write_text(script(manifest))
    return manifest


def validate(root=ROOT):
    manifest = json.loads((root / MANIFEST).read_text())
    assert manifest['schema'] == 1 and manifest['policy'] == POLICY, 'Stale thumbnail policy'
    views = {view['image']: view for view in source_views(root)}
    assert len(manifest['images']) == len(views), 'Missing or duplicate thumbnail sources'
    assert {entry['source'] for entry in manifest['images']} == set(views), 'Thumbnail source coverage differs'
    for entry in manifest['images']:
        source = root / entry['source']
        assert digest(source) == entry['sourceSha256'], f'Stale source: {source}'
        assert entry['kind'] == views[entry['source']]['type'], 'Wrong content policy'
        with Image.open(source) as original:
            assert original.size == (entry['sourceWidth'], entry['sourceHeight'])
        assert tuple(item['width'] for item in entry['variants']) == WIDTHS, 'Missing responsive width'
        for item in entry['variants']:
            expected = f'images/thumbnails/islands/{source.stem}--{item["width"]}.webp'
            assert item['path'] == expected, 'Thumbnail path differs from source'
            target = root / expected
            assert target.stat().st_size == item['bytes'] and digest(target) == item['sha256'], \
                f'Thumbnail bytes differ: {target}'
            with Image.open(target) as image:
                height = round(entry['sourceHeight'] * item['width'] / entry['sourceWidth'])
                assert image.format == 'WEBP' and image.size == (item['width'], height)
                assert item['height'] == height, 'Wrong thumbnail aspect ratio'
    assert (root / SCRIPT).read_text() == script(manifest), 'Stale thumbnail browser lookup'
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate source/derivative hashes, sizes and browser data')
    args = parser.parse_args()
    manifest = validate() if args.check else generate()
    variants = [item for entry in manifest['images'] for item in entry['variants']]
    print(f'{"Validated" if args.check else "Built"} {len(variants)} island thumbnails, '
          f'{sum(item["bytes"] for item in variants):,} bytes; full-size source images unchanged')


if __name__ == '__main__':
    main()
