#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Reproducible image derivatives shared by the wiki's preview collections."""
import hashlib
import json
from pathlib import Path

from PIL import Image, features


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoder():
    return {'format': 'WebP', 'method': 6, 'pillow': Image.__version__,
            'libwebp': features.version('webp')}


def variant_path(source, settings, width):
    return f'{settings["directory"]}/{Path(source).stem}--{width}.webp'


def generate_images(root, sources, profiles):
    """Make only declared widths; preserve the complete source frame and bytes."""
    images = []
    targets = set()
    for source, kind in sources.items():
        path = root / source
        settings = profiles[kind]
        entry = {'source': source, 'sourceSha256': digest(path), 'kind': kind, 'variants': []}
        with Image.open(path) as image:
            entry.update(sourceWidth=image.width, sourceHeight=image.height)
            for width in settings['widths']:
                assert 0 < width < image.width, f'Preview must not upscale: {source}'
                height = round(image.height * width / image.width)
                relative = variant_path(source, settings, width)
                assert relative not in targets, f'Duplicate preview path: {relative}'
                targets.add(relative)
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                image.resize((width, height), getattr(Image.Resampling, settings['resample'])).save(
                    target, 'WEBP', quality=settings['quality'], method=6)
                entry['variants'].append({'path': relative, 'width': width, 'height': height,
                                          'bytes': target.stat().st_size, 'sha256': digest(target)})
        images.append(entry)
    return images


def validate_images(root, images, sources, profiles):
    """Reject stale captures, incomplete widths, and changed bytes or dimensions."""
    assert len(images) == len(sources), 'Missing or duplicate preview sources'
    assert {entry['source'] for entry in images} == set(sources), 'Preview source coverage differs'
    targets = set()
    for entry in images:
        source = root / entry['source']
        assert digest(source) == entry['sourceSha256'], f'Stale source: {source}'
        assert entry['kind'] == sources[entry['source']], 'Wrong content policy'
        settings = profiles[entry['kind']]
        with Image.open(source) as original:
            assert original.size == (entry['sourceWidth'], entry['sourceHeight'])
        assert [item['width'] for item in entry['variants']] == list(settings['widths']), 'Missing responsive width'
        for item in entry['variants']:
            assert 0 < item['width'] < entry['sourceWidth'], 'Preview must not upscale'
            expected = variant_path(entry['source'], settings, item['width'])
            assert item['path'] == expected, 'Preview path differs from source'
            assert expected not in targets, f'Duplicate preview path: {expected}'
            targets.add(expected)
            target = root / expected
            assert target.stat().st_size == item['bytes'] and digest(target) == item['sha256'], \
                f'Preview bytes differ: {target}'
            with Image.open(target) as image:
                height = round(entry['sourceHeight'] * item['width'] / entry['sourceWidth'])
                assert image.format == 'WEBP' and image.size == (item['width'], height)
                assert item['height'] == height, 'Wrong preview aspect ratio'


def browser_script(variable, images):
    lookup = {entry['source']: [[item['width'], item['path']] for item in entry['variants']]
              for entry in images}
    return f'/* SPDX-License-Identifier: GPL-3.0-only */\nwindow.{variable} = ' + json.dumps(
        lookup, separators=(',', ':')) + ';\n'
