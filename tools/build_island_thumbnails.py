#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build small island previews without changing the full-size evidence images.

The maps and panoramas were compared with BOX and LANCZOS at 480 pixels;
LANCZOS retained the small terrain boundaries better in these particular views.
This policy is specific to this collection, not a filter preset for other art.
"""
import argparse
import json
from pathlib import Path

from image_variants import browser_script, encoder, generate_images, validate_images

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/island-thumbnails.json'
SCRIPT = 'data/island-thumbnails.js'
WIDTHS = (480, 960)
POLICY = {'map': {'resample': 'LANCZOS', 'quality': 88},
          'panorama': {'resample': 'LANCZOS', 'quality': 88}}


def source_views(root):
    catalog = json.loads((root / 'data/islands.json').read_text())
    return [view for island in catalog['islands'] for view in island['views'] if view['type'] in POLICY]


def profiles():
    return {kind: {**settings, 'widths': WIDTHS, 'directory': 'images/thumbnails/islands'}
            for kind, settings in POLICY.items()}


def sources(root):
    return {view['image']: view['type'] for view in source_views(root)}


def script(manifest):
    return browser_script('ISLAND_THUMBNAILS', manifest['images'])


def generate(root=ROOT):
    manifest = {'schema': 1, 'catalog': 'data/islands.json', 'policy': POLICY,
                'encoder': encoder(), 'images': generate_images(root, sources(root), profiles())}
    (root / MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n')
    (root / SCRIPT).write_text(script(manifest))
    return manifest


def validate(root=ROOT):
    manifest = json.loads((root / MANIFEST).read_text())
    assert manifest['schema'] == 1 and manifest['policy'] == POLICY, 'Stale thumbnail policy'
    validate_images(root, manifest['images'], sources(root), profiles())
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
