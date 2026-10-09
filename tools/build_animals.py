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

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    'Birds': 'Chicken Gull Goose Duck Turkey Peafowl Ostrich Roadrunner Hummingbird Sunbird Shoebill Crow Emu BaldEagle Toucan Potoo BlueJay Penguin',
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=ROOT.parent / 'Voxelgame')
    parser.add_argument('--meshes', type=Path, default=ROOT / '.cache/animal-refresh/meshes')
    parser.add_argument('--renders', type=Path, default=ROOT / '.cache/animal-refresh/renders')
    parser.add_argument('--date', type=date.fromisoformat, default=date.today(), help='Snapshot date (YYYY-MM-DD; defaults to today)')
    args = parser.parse_args()
    source_path = args.game / 'crates/voxelgame-core/src/entities/mod.rs'
    source = source_path.read_text()
    enum = source.split('pub enum Species {', 1)[1].split('\n}', 1)[0]
    descriptions = dict((key, desc.strip()) for desc, key in re.findall(r'/// ([^\n]+)\n\s+(\w+),', enum))
    catalog_match = re.search(r'pub const ALL: \[Self; (\d+)\] = \[(.*?)\];', source, re.S)
    assert catalog_match, 'Update catalog parser for changed game source'
    catalog = re.findall(r'Self::(\w+)', catalog_match.group(2))
    assert len(catalog) == len(set(catalog)) == len(descriptions) == int(catalog_match.group(1))
    names = dict(re.findall(r'Self::(\w+) => "([^"]+)"', source.split('fn name(self)', 1)[1].split('\n    }', 1)[0]))
    guilds = source.split('fn ambient_species_for_biome(', 1)[1].split('(!guild.is_empty())', 1)[0]
    guilds = re.sub(r'//[^\n]*', '', guilds)
    habitats = {key: set() for key in catalog}
    assigned = set()
    for biome_text, members in re.findall(r'((?:Biome::\w+\s*\|?\s*)+) =>\s*(?:\{\s*)?&\[(.*?)\]', guilds, re.S):
        biomes = re.findall(r'Biome::(\w+)', biome_text)
        assigned.update(biomes)
        for species in re.findall(r'Species::(\w+)', members):
            habitats[species].update(biomes)
    biome_data = json.loads((ROOT / 'data/biomes.json').read_text())['biomes']
    biome_names = {b['id']: b['name'] for b in biome_data}
    assert assigned == set(biome_names), 'Update habitat parser for changed game source'
    manifest = list(csv.DictReader((args.meshes / 'manifest.tsv').open(), delimiter='\t'))
    slugs = {row['label']: row['species'] for row in manifest}
    rows = []
    output = ROOT / 'images/animals'
    output.mkdir(parents=True, exist_ok=True)
    for species in catalog:
        name = names[species]
        slug = slugs[name]
        category = next((group for group, members in GROUPS.items() if species in members.split()), 'Mammals')
        points = [list(map(float, line.split()[1:4])) for line in (args.meshes / f'{slug}--idle.obj').read_text().splitlines() if line.startswith('v ')]
        size = [round(max(p[i] for p in points) - min(p[i] for p in points), 4) for i in range(3)]
        views = []
        for pose, angle, label in VIEWS:
            filename = f'{slug}--{pose}--{angle}'
            png = args.renders / (filename + '.png')
            webp = output / (filename + '.webp')
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
    content = json.dumps(data, indent=2, ensure_ascii=False)
    (ROOT / 'data/animals.json').write_text(content + '\n')
    (ROOT / 'data/animals.js').write_text('// SPDX-License-Identifier: GPL-3.0-only\nwindow.ANIMAL_ATLAS = ' + content + ';\n')
    print(f'Built {len(rows)} animals, {sum(len(a["views"]) for a in rows)} images, {len(assigned)} biome rules.')

if __name__ == '__main__':
    main()
