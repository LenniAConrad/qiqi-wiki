#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Block icons cropped from the game's own creative Catalogue, one sprite for the Blocks page.

`replays OUT_DIR` writes two replays for Voxelgame's `tools/game_debug.py replay`: each opens the
creative Catalogue in a disposable seed-42 world (1280 x 720, offscreen, no packs), captures a page,
then clicks every slot so the debug state records which block that slot selects. `build SESSION...`
reads those evidence directories, keeps only slots whose click changed the selected block (so items
that are not blocks are never mislabelled), crops each slot and writes `images/blocks/icons.webp`
plus `data/block-icons.json`. Pixels are copied 1:1; nothing is redrawn, scaled or recoloured.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SPRITE = 'images/blocks/icons.webp'
MANIFEST = 'data/block-icons.json'
# Catalogue geometry at 1280 x 720 (the debug state's catalog_first and catalog_search rects).
FIRST_X, FIRST_Y, SLOT = 430.0, 209.2857, 52.3214
PITCH = (797.5 - 14 * SLOT) / 13 + SLOT
COLUMNS, ROWS, PAGES = 14, 6, 4
NEXT_PAGE, PARK = [1209, 587], [640, 690]
INSET = 3  # drop the slot rim so a selected slot's brass frame never shows
SIZE = 52 - 2 * INSET
SPRITE_COLUMNS = 16


def slot_centre(slot):
    return [FIRST_X + SLOT / 2 + (slot % COLUMNS) * PITCH, FIRST_Y + SLOT / 2 + (slot // COLUMNS) * PITCH]


def click(point):
    return [{'command': 'step', 'frames': 1, 'pointer': point, 'buttons': ['primary']},
            {'command': 'step', 'frames': 1, 'pointer': point}]


def next_page():
    return click(NEXT_PAGE) + [{'command': 'step', 'frames': 1, 'pointer': PARK}]


def replay(pages):
    commands = [{'command': 'reset', 'seed': '42', 'mods': [], 'viewport': [1280, 720], 'scene': 'inspection'},
                {'command': 'configure', 'screen': 'inventory', 'inventory_view': 'build', 'mode': 'creative',
                 'view_distance': 4, 'shader': 'fast'},
                {'command': 'render', 'frames': 10}]
    for _ in range(pages[0] - 1):
        commands += next_page()
    for index, page in enumerate(pages):
        if index:
            commands += next_page()
        commands += [{'command': 'step', 'frames': 1, 'pointer': PARK}, {'command': 'render', 'frames': 3},
                     {'command': 'capture_frame', 'name': f'page{page}.png'}]
        for slot in range(COLUMNS * ROWS):
            commands += click(slot_centre(slot))
    return {'version': 1, 'license': 'SPDX-License-Identifier: GPL-3.0-only',
            'description': f'Creative Catalogue pages {list(pages)}: capture each page, then click every slot to '
                           'record its block. Disposable world, no normal saves or window.',
            'commands': commands}


def slots(session):
    """Yield (page, slot, label or None) from one replay transcript."""
    rows = [json.loads(line) for line in (session / 'transcript.jsonl').read_text().splitlines()]
    page = previous = None
    for index, row in enumerate(rows):
        request = row['request']
        if request['command'] == 'capture_frame':
            page, slot = int(request['name'][4]), 0
            previous = rows[index - 1]['response']['result']['selected_block']
        elif page and request['command'] == 'step' and request.get('buttons') and request['pointer'] != NEXT_PAGE:
            label = rows[index + 1]['response']['result']['selected_block']
            # The catalogue opens with the first slot already selected.
            yield page, slot, label if label != previous or (page, slot) == (1, 0) else None
            previous, slot = label, slot + 1


def build(sessions, root=ROOT):
    crops, receipts = {}, []
    for session in sessions:
        metadata = json.loads((session / 'metadata.json').read_text())
        pages = {}
        for page, slot, label in slots(session):
            if page not in pages:
                path = session / f'page{page}.png'
                pages[page] = Image.open(path).convert('RGB')
                receipts.append({'page': page, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            if label and label not in crops:
                x = round(FIRST_X + (slot % COLUMNS) * PITCH) + INSET
                y = round(FIRST_Y + (slot // COLUMNS) * PITCH) + INSET
                crops[label] = pages[page].crop((x, y, x + SIZE, y + SIZE))
    names = sorted(crops)
    sprite = Image.new('RGB', (SPRITE_COLUMNS * SIZE, -(-len(names) // SPRITE_COLUMNS) * SIZE))
    for index, name in enumerate(names):
        sprite.paste(crops[name], ((index % SPRITE_COLUMNS) * SIZE, (index // SPRITE_COLUMNS) * SIZE))
    (root / SPRITE).parent.mkdir(parents=True, exist_ok=True)
    sprite.save(root / SPRITE, 'WEBP', lossless=True, method=6)
    manifest = {'schema': 1, 'sprite': SPRITE, 'size': SIZE, 'columns': SPRITE_COLUMNS,
                'spriteSha256': hashlib.sha256((root / SPRITE).read_bytes()).hexdigest(),
                'source': {'method': 'Creative Catalogue slots cropped 1:1 from headless captures made with '
                                     "Voxelgame's tools/game_debug.py replay (seed 42, 1280 x 720, no packs).",
                           'captured': '2026-11-08', 'binarySha256': metadata['binary_sha256'],
                           'pages': sorted(receipts, key=lambda r: r['page'])},
                'icons': {name: index for index, name in enumerate(names)}}
    (root / MANIFEST).write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    sub.add_parser('replays').add_argument('out', type=Path)
    sub.add_parser('build').add_argument('sessions', type=Path, nargs='+')
    args = parser.parse_args()
    if args.mode == 'replays':
        for name, pages in (('a', (1, 2)), ('b', (3, 4))):
            (args.out / f'catalogue_{name}.json').write_text(json.dumps(replay(pages)) + '\n')
    else:
        print(f'Wrote {len(build(args.sessions)["icons"])} block icons to {SPRITE}')


if __name__ == '__main__':
    main()
