#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Contact sheets of only the requested genuine capture generation."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation', type=int, default=9)
    parser.add_argument('--ids', nargs='+', help='Limit a review sheet to these biome IDs')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source-manifest', type=Path,
                        help='Include only captures from this exact frozen build')
    args = parser.parse_args()
    output = args.output or ROOT / f'.cache/generation{args.generation}-refresh/contact-sheets'
    output.mkdir(parents=True, exist_ok=True)
    captures = json.loads((ROOT / 'data/captures.json').read_text())
    if args.ids and set(args.ids) - set(captures):
        parser.error(f'Unknown biome IDs: {sorted(set(args.ids) - set(captures))}')
    manifest_sha = hashlib.sha256(args.source_manifest.read_bytes()).hexdigest() if args.source_manifest else None
    rows = sorted((name, row) for name, row in captures.items()
                  if row.get('generatorVersion') == args.generation
                  and (args.ids is None or name in args.ids)
                  and (manifest_sha is None or row.get('sourceManifestSha256') == manifest_sha))
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    for batch in range((len(rows) + 11) // 12):
        subset = rows[batch * 12:(batch + 1) * 12]
        sheet = Image.new('RGB', (1280, 636), (17, 24, 27))
        draw = ImageDraw.Draw(sheet)
        for index, (name, row) in enumerate(subset):
            x, y = (index % 4) * 320, (index // 4) * 212
            with Image.open(ROOT / row['file']) as original:
                sheet.paste(original.resize((320, 180)), (x, y + 29))
            draw.text((x + 5, y + 5), name, fill=(240, 244, 236), font=font)
        path = output / f'biomes-{batch + 1:02d}.jpg'
        sheet.save(path, quality=92)
        print(f'{path}: {len(subset)} photographs')
    print(f'{len(rows)}/92 generation {args.generation} photographs')

if __name__ == '__main__':
    main()
