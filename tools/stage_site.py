#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage the reviewed public website, never the repository's evidence archive.

Pages and the local gate use this allowlist. Add new pages, browser datasets or
licensed assets here deliberately; a new repository file is private by default.
"""

import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    'index.html', 'blocks.html', 'mobs.html', 'atlas.html', 'animals.html', 'islands.html',
    'features.html', 'guides.html', 'guide-getting-started.html',
    'guide-controls.html', 'guide-first-survival-day.html', 'guide-crafting.html',
    'guide-install-and-worlds.html',
    'guide-troubleshooting.html', 'guide-hunting.html', 'guide-seasons.html', 'guide-maps.html', 'guide-building.html',
    'guide-sailing.html', 'guide-explosives.html', 'guide-weather-day-night.html', 'guide-saves.html', 'guide-creatures.html',
    'guide-not-in-game.html', 'guide-settings-performance.html', 'guide-study-grove.html',
    'guide-moving-and-aiming.html', 'guide-caves-and-landmarks.html', 'guide-volcanoes-water-and-expeditions.html',
    'performance.html', 'scale.html', 'ABOUT.md',
    'style.css', 'wiki.css', 'features.css', 'guides.css', 'islands.css',
    'performance.css', 'scale.css',
    'app.js', 'wiki-search.js', 'data/search.js', 'animals.js', 'features.js', 'guides.js', 'islands.js',
    'scale.js', 'favicon.svg', 'LICENSE', 'NOTICE.md',
    'PERFORMANCE_ANALYSIS.md', 'PERFORMANCE_OPTIMIZATION.md',
    'STREAMING_IMPROVEMENTS.md',
    'data/animals.js', 'data/animals.json', 'data/biomes.js', 'data/biomes.json',
    'data/captures.json', 'data/descriptions.json', 'data/features.json',
    'data/guides.json', 'data/habitats.json', 'data/islands.js', 'data/islands.json',
    'data/provenance.json', 'data/recipes.json', 'data/blocks.json', 'data/scale.js',
    'data/survey.json', 'data/viewpoints.json',
    'data/performance/summary.json', 'data/performance/steady-results.csv',
    'data/performance/cpu-attribution.json', 'data/performance/provenance.json',
    'data/performance/PROFILING.md', 'data/performance/VALIDATION.md',
    'data/performance/optimization/summary.json',
    'data/performance/optimization/public-verification.md',
    'images/scale/manifest.json',
)
IMAGE_SUFFIXES = {'.webp', '.png', '.jpg', '.jpeg', '.svg'}
IMAGE_CATALOGS = (
    'data/biomes.json', 'data/animals.json', 'data/islands.json',
    'data/guides.json',
)


def regular_source(path, root):
    """Reject symlinks, including a symlink in a parent directory."""
    return path.is_file() and not any(
        p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root))


def image_paths(root):
    """Publish only images recorded by the original-asset catalogs."""
    names = {'images/performance/component-costs.png'}

    def collect(value):
        if isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, str) and value.startswith('images/'):
            if Path(value).suffix.lower() in IMAGE_SUFFIXES:
                names.add(value)

    for catalog in IMAGE_CATALOGS:
        collect(json.loads((root / catalog).read_text()))
    manifest = json.loads((root / 'images/scale/manifest.json').read_text())
    names.update(f'images/scale/{name}' for name in manifest.get('outputs', {}))
    for name in sorted(names):
        path = Path(name)
        if '..' in path.parts or path.is_absolute() or path.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError(f'Invalid public image path: {name}')
        yield name


def public_sources(root):
    for name in PUBLIC_FILES:
        source = root / name
        if not regular_source(source, root):
            raise ValueError(f'Missing or symlinked public file: {name}')
        yield source
    for name in image_paths(root):
        source = root / name
        if not regular_source(source, root):
            raise ValueError(f'Missing or symlinked public image: {name}')
        yield source


def stage(output, root=ROOT):
    root, output = root.resolve(), output.resolve()
    if output == root or any(output.is_relative_to(root / name) for name in ('images', 'data')):
        raise ValueError('Stage outside the source asset directories')
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f'Refusing to stage into non-empty directory: {output}')
    sources = list(public_sources(root))  # Validate before writing any output.
    output.mkdir(parents=True, exist_ok=True)
    for source in sources:
        target = output / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return len(sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new or empty destination directory')
    args = parser.parse_args()
    print(f'Staged {stage(args.output)} files in {args.output}')


if __name__ == '__main__':
    main()
