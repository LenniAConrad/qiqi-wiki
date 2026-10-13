#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build the animal field guide from source metadata and production-mesh renders."""
import argparse
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from PIL import Image
from freeze_media_source import verify_snapshot

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    'Birds': 'Chicken Gull Goose Swan Duck Turkey Peafowl Ostrich Roadrunner Hummingbird Sunbird Shoebill Crow Emu BaldEagle Toucan Potoo BlueJay Penguin',
    'Reptiles & amphibians': 'Frog Turtle Crocodile Rattlesnake KomodoDragon AlligatorSnappingTurtle Anaconda Terrapin Caiman',
    'Fish': 'Salmon Trout Carp HammerheadShark Blobfish FrilledShark DevilsHolePupfish Catfish FlyingFish Mudskipper',
    'Invertebrates': 'Crab Butterfly Fly Lobster CaveCentipede Cockroach MantisShrimp LeafcutterAnt TarantulaHawk MimicOctopus CombJelly GiantSquid BananaSlug Triops',
}
VIEWS = [('idle', 'three-quarter', 'Resting · ¾ view'), ('idle', 'side', 'Resting · side'),
         ('stride', 'three-quarter', 'Moving · ¾ view'), ('stride', 'side', 'Moving · side')]
DESCRIPTIONS = {
    'Anteater': 'A long-snouted animal with large foreclaws and a sweeping tail.',
    'Fly': 'A tiny airborne insect with compact wings and a hovering silhouette.',
    'LeafcutterAnt': 'A tiny foraging ant carrying a green leaf.',
    'MimicOctopus': 'A shallow-water octopus with long, articulated arms.',
    'Butterfly': 'A small flower-country pollinator with broad wings and a fluttering path.',
    'Bat': 'A small woodland mammal with broad angular membrane wings and large ears.',
    'RiverOtter': 'A long-bodied riverbank mammal with a cream muzzle, webbed feet and a tapering swimming tail.',
    'Penguin': 'A cold-shore bird with a dark back, pale belly, short waddling feet and swimming flippers.',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def animal_category(species):
    """Return the field-guide grouping for a built-in species."""
    return next((group for group, members in GROUPS.items() if species in members.split()), 'Mammals')


def capture_receipts(game, meshes, renders, manifest_path, render_receipt_path):
    """Bind fresh portraits to the full frozen inputs and the actual rendering run."""
    snapshot = verify_snapshot(game, manifest_path)
    receipt = json.loads(render_receipt_path.read_text())
    if (receipt['sourceCommit'] != snapshot['commit']
            or receipt['sourceManifestSha256'] != sha(manifest_path)
            or receipt['wikiRenderScriptSha256'] != sha(ROOT / 'tools/render_animals.py')
            or receipt['gameRenderScriptSha256'] != sha(game / 'tools/render_creature_gallery.py')):
        raise ValueError('Render receipt does not match the frozen source and render scripts')
    for directory, key in ((meshes, 'meshHashes'), (renders, 'renderHashes')):
        for name, expected in receipt[key].items():
            path = directory / name
            if (Path(name).is_absolute() or '..' in Path(name).parts
                    or not path.resolve().is_relative_to(directory.resolve())
                    or not path.is_file() or sha(path) != expected):
                raise ValueError('Changed or missing render input/output: ' + name)
    material_files = {str(p.relative_to(meshes)) for p in meshes.rglob('*')
                      if p.is_file() and p.suffix != '.obj'}
    if not material_files <= receipt['meshHashes'].keys():
        raise ValueError('Render receipt is missing material inputs')
    capture = {key: receipt[key] for key in ('blenderVersion', 'engine', 'resolution',
                                            'renderSettings', 'exporterSha256', 'captureDriverSha256')}
    capture.update({'gameCommit': snapshot['commit'], 'gameTree': snapshot['tree'],
                    'sourceManifestSha256': sha(manifest_path),
                    'renderReceiptSha256': sha(render_receipt_path)})
    return capture, receipt


def source_habitats(source, catalog, biome_names):
    """Read ambient candidates, including the reviewed conditional Swan branch.

    These are possible habitats, not guaranteed spawns or spawn probabilities.
    Refuse unrecognized pre-guild logic instead of silently losing a species.
    """
    body = source.split('fn ambient_species_for_biome(', 1)[1].split('(!guild.is_empty())', 1)[0]
    body = re.sub(r'//[^\n]*', '', body).split('{', 1)[1]
    prelude, guilds = re.split(r'let\s+guild\s*:\s*&\[Species\]\s*=\s*match\s+biome', body, maxsplit=1)
    habitats = {key: set() for key in catalog}
    assigned = set()

    def add(biome_text, members):
        biomes = set(re.findall(r'Biome::(\w+)', biome_text))
        if not biomes <= set(biome_names):
            raise ValueError('Unknown biome in ambient source: ' + str(biomes - set(biome_names)))
        for species in members:
            if species not in habitats:
                raise ValueError('Unknown species in ambient source: ' + species)
            habitats[species].update(biomes)
        return biomes

    # This exact supported hash condition has attainable branches. More complex
    # guards need a fresh source review before their habitats become wiki facts.
    conditional = re.compile(
        r'if\s+matches!\(\s*biome\s*,\s*((?:Biome::\w+\s*\|?\s*)+)\)\s*'
        r'&&\s*\(\s*hash\s*>>\s*40\s*\)\s*%\s*8\s*==\s*0\s*'
        r'\{\s*return\s+Some\(Species::(\w+)\);\s*\}', re.S)
    for rule in conditional.finditer(prelude):
        add(rule.group(1), [rule.group(2)])
    if conditional.sub('', prelude).strip():
        raise ValueError('Update habitat parser for changed pre-guild logic')
    for biome_text, members in re.findall(r'((?:Biome::\w+\s*\|?\s*)+) =>\s*(?:\{\s*)?&\[(.*?)\]', guilds, re.S):
        assigned.update(add(biome_text, re.findall(r'Species::(\w+)', members)))
    if assigned != set(biome_names):
        raise ValueError('Update habitat parser for changed biome guilds')
    return habitats, assigned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=ROOT.parent / 'Voxelgame')
    parser.add_argument('--meshes', type=Path, default=ROOT / '.cache/animal-refresh/meshes')
    parser.add_argument('--renders', type=Path, default=ROOT / '.cache/animal-refresh/renders')
    parser.add_argument('--date', type=date.fromisoformat, default=date.today(), help='Snapshot date (YYYY-MM-DD; defaults to today)')
    parser.add_argument('--source-manifest', type=Path, help='Complete frozen media source manifest')
    parser.add_argument('--render-receipt', type=Path, help='Matching hashes and environment of the actual render run')
    args = parser.parse_args()
    if bool(args.source_manifest) != bool(args.render_receipt):
        parser.error('--source-manifest and --render-receipt must be supplied together')
    capture, receipt = (capture_receipts(args.game, args.meshes, args.renders,
                                        args.source_manifest, args.render_receipt)
                        if args.source_manifest else (None, None))
    source_path = args.game / 'crates/voxelgame-core/src/entities/mod.rs'
    source = source_path.read_text()
    enum = source.split('pub enum Species {', 1)[1].split('\n}', 1)[0]
    descriptions = dict((key, desc.strip()) for desc, key in re.findall(r'/// ([^\n]+)\n\s+(\w+),', enum))
    catalog_match = re.search(r'pub const ALL: \[Self; (\d+)\] = \[(.*?)\];', source, re.S)
    assert catalog_match, 'Update catalog parser for changed game source'
    catalog = re.findall(r'Self::(\w+)', catalog_match.group(2))
    assert len(catalog) == len(set(catalog)) == len(descriptions) == int(catalog_match.group(1))
    names = dict(re.findall(r'Self::(\w+) => "([^"]+)"', source.split('fn name(self)', 1)[1].split('\n    }', 1)[0]))
    biome_data = json.loads((ROOT / 'data/biomes.json').read_text())['biomes']
    biome_names = {b['id']: b['name'] for b in biome_data}
    habitats, assigned = source_habitats(source, catalog, biome_names)
    manifest = list(csv.DictReader((args.meshes / 'manifest.tsv').open(), delimiter='\t'))
    slugs = {row['label']: row['species'] for row in manifest}
    rows = []
    output = ROOT / 'images/animals'
    output.mkdir(parents=True, exist_ok=True)
    for species in catalog:
        name = names[species]
        slug = slugs[name]
        category = animal_category(species)
        points = [list(map(float, line.split()[1:4])) for line in (args.meshes / f'{slug}--idle.obj').read_text().splitlines() if line.startswith('v ')]
        size = [round(max(p[i] for p in points) - min(p[i] for p in points), 4) for i in range(3)]
        views = []
        for pose, angle, label in VIEWS:
            filename = f'{slug}--{pose}--{angle}'
            png = args.renders / (filename + '.png')
            webp = output / (filename + '.webp')
            if receipt and (receipt['renderHashes'].get(png.name) != sha(png)
                            or receipt['meshHashes'].get(f'{slug}--{pose}.obj')
                            != sha(args.meshes / f'{slug}--{pose}.obj')):
                raise ValueError('Portrait missing from the verified render run: ' + filename)
            with Image.open(png) as image:
                assert image.size == (512, 512), png
                image.save(webp, 'WEBP', quality=92, method=6)
            views.append({'label': label, 'pose': pose, 'angle': angle,
                          'image': str(webp.relative_to(ROOT)), 'imageSha256': sha(webp),
                          'renderSha256': sha(png), 'meshSha256': sha(args.meshes / f'{slug}--{pose}.obj')})
        display_name = name[0].upper() + name[1:]
        if species == 'DevilsHolePupfish': display_name = 'Devils Hole pupfish'
        rows.append({'id': species, 'slug': slug, 'name': display_name, 'category': category,
                     'description': DESCRIPTIONS.get(species, descriptions[species]),
                     'habitats': sorted(habitats[species], key=biome_names.get), 'sizeMetres': size, 'views': views})
    paths = ['crates/voxelgame-core/src/entities/mod.rs', 'crates/voxelgame-core/src/entities/models.rs',
             'crates/voxelgame-core/src/entities/models/bird_models.rs',
             'crates/voxelgame-core/src/entities/visual_qa.rs', 'crates/voxelgame-render/src/creature_visual_qa.rs',
             'crates/voxelgame-render/examples/export_creature_gallery.rs',
             'crates/voxelgame-render/src/atlas.rs', 'crates/voxelgame-render/src/shader.wgsl',
             'tools/render_creature_gallery.py']
    data = {'date': args.date.isoformat(), 'catalogCount': len(catalog), 'animals': sorted(rows, key=lambda a: a['name']), 'biomes': biome_names,
            'provenance': {'sourceRepository': '../Voxelgame', 'sourceHashes': {p: sha(args.game / p) for p in paths},
                           'renderScriptSha256': sha(ROOT / 'tools/render_animals.py'),
                           'materialsSha256': {str(p.relative_to(args.meshes)): sha(p) for p in sorted(args.meshes.rglob('*')) if p.is_file() and p.suffix != '.obj'},
                           'method': 'Production creature geometry and texture exports, rendered in Blender with neutral lighting scaled to each model’s bounds. Four static poses/views, individually framed; images do not share a scale. Habitat lists are ambient spawn candidates, subject to terrain, water and population checks.'}}
    if capture:
        data['provenance']['sourceRepository'] = 'https://github.com/LenniAConrad/qiqi'
        data['provenance']['capture'] = capture
    content = json.dumps(data, indent=2, ensure_ascii=False)
    (ROOT / 'data/animals.json').write_text(content + '\n')
    (ROOT / 'data/animals.js').write_text('// SPDX-License-Identifier: GPL-3.0-only\nwindow.ANIMAL_ATLAS = ' + content + ';\n')
    print(f'Built {len(rows)} animals, {sum(len(a["views"]) for a in rows)} images, {len(assigned)} biome rules.')

if __name__ == '__main__':
    main()
