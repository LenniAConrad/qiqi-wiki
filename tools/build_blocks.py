#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Extract the base-game core registry and render its player reference.

Use --game with a read-only exported snapshot to refresh data/blocks.json.
Without --game, render only from the existing audited dataset.
"""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re

from reference_layout import article_open, article_close
from build_guides import recipe_anchor

ROOT = Path(__file__).resolve().parents[1]
TABLE = 'crates/voxelgame-core/src/world/block/table.rs'
FAMILIES = (
    ('ground', 'Natural ground'), ('stone', 'Stone and minerals'),
    ('wood', 'Wood and leaves'), ('building', 'Building materials'),
    ('glass-light', 'Glass and light'), ('water-ice', 'Water and ice'),
    ('plants', 'Plants and shore life'), ('utility', 'Utility and empty space'),
)
# Editorial groupings, independent of the engine's collision/material flags.
FAMILY_MEMBERS = {
    'ground': '''GRASS DIRT SAND GRAVEL CLAY PODZOL SNOW PACKED_SNOW FROZEN_TURF
        PEAT RED_SAND DRY_TURF BANDED_CLAY MUD SEA_SAND ASH RICH_TURF LEAF_LITTER
        PETAL_CARPET FIRN SALT CRACKED_CLAY FINE_SAND OCHRE_CLAY UMBER_CLAY SIENNA_CLAY
        BLACK_SAND SHELL_SAND''',
    'stone': '''STONE RED_ROCK BOULDER_STONE SANDSTONE RED_SANDSTONE COBBLE BASALT
        OBSIDIAN MAGMA_STONE MINERAL_CRUST STEAM_VENT CHALK FLINT SLATE_SCREE
        LIMESTONE SHARP_LIMESTONE BOG_IRON WET_STONE BARNACLE_ROCK LAYERED_SANDSTONE
        GUANO_ROCK HOLDFAST_ROCK SCORCHED_STONE IRON_ORE GEYSERITE SULFUR_CRUST
        PAHOEHOE LAVA_ROCK GRANITE EXFOLIATED_GRANITE SLATE_SHALE AMETHYST_BLOCK DARK_STONE''',
    'wood': '''WOOD LEAVES BIRCH_WOOD BIRCH_LEAVES PINE_WOOD PINE_NEEDLES OAK_WOOD
        OAK_LEAVES MOSSY_WOOD FRUIT_WOOD BLOSSOM_LEAVES ACACIA_WOOD ACACIA_LEAVES
        WILLOW_WOOD WILLOW_LEAVES MANGROVE_WOOD MANGROVE_ROOTS JUNGLE_WOOD JUNGLE_LEAVES
        BAMBOO CHERRY_WOOD CHERRY_BLOSSOM_LEAVES AMBER_LEAVES RUSSET_LEAVES GIANT_WOOD
        DEADWOOD CHARRED_WOOD PALM_WOOD PALM_FRONDS MESQUITE_WOOD FIG_WOOD BROAD_LEAVES
        CYPRESS_WOOD CYPRESS_KNEES DRIFTWOOD''',
    'building': '''PLANKS BIRCH_PLANKS PINE_PLANKS GRAY_BRICK GLAZED_ROOF_TILE
        IMPERIAL_ROOF_TILE LACQUERED_WOOD PAPER_PANEL WHITE_PLASTER CARVED_STONE
        CHALK_BRICKS RED_ROCK_BRICKS MOSSY_COBBLE BASALT_BRICKS POLISHED_GRANITE
        REED_THATCH PINK_PLASTER ROSE_BOARDS FUCHSIA_TILE DOOR WIDE_DOOR CHEST''',
    'glass-light': 'GLOWSTONE GLASS RED_LANTERN GLOW_LICHEN IMPACT_GLASS AMETHYST_CLUSTER',
    'water-ice': '''WATER WARM_WATER DARK_WATER FRESH_WATER BLACK_WATER BOILING_WATER
        ICE GLACIER_ICE BLACK_ICE ICE_SPIRE CREVASSE_ICE''',
    'plants': '''WOODLAND_FUNGI PLUME_GRASS DUNE_GRASS FALLEN_FRUIT FLAX MOSS
        WILDFLOWERS TALL_GRASS FRUIT LICHEN CACTUS DRY_SHRUB REEDS DUCKWEED VINES
        FERN KELP SEAGRASS CORAL_RED CORAL_GOLD CORAL_BLUE MOUNTAIN_FLOWERS BAMBOO_SHOOT
        HEATHER LAVENDER SHORT_GRASS SEDGE FIREWEED DATES THORN_BUSH HANGING_VINE
        EPIPHYTE_MOSS COTTON_GRASS MOSS_VEIL TALL_REEDS WATER_LILY BROMELIAD ENDEMIC_FLOWERS
        ANEMONE STARFISH GIANT_KELP''',
    'utility': 'AIR TNT CAMP_CRATE BEEHIVE',
}
FAMILY_BY_BLOCK = {name: family for family, names in FAMILY_MEMBERS.items() for name in names.split()}
# The open leaf of a placed door is a state of DOOR, not an item a player holds.
STATE_ONLY = {'DOOR_OPEN'}
CREATIVE_ONLY = {'IMPERIAL_ROOF_TILE': 'Jade glazed tile (creative)',
                 'AMETHYST_CLUSTER': 'Amethyst cluster (creative only)'}
ROW = re.compile(r'\s*([A-Z][A-Z_0-9]*)\s*=\s*(\d+),\s*("(?:[^"\\]|\\.)*"),\s*\[([^\]]+)\];')
# Player sentences stay close to the registry's documentation; no inferred drops.
DESCRIPTIONS = dict(line.split('|', 1) for line in """
AIR|Air is empty space you can move through.
GRASS|Meadow turf covers the surface of meadows.
DIRT|Loam lies beneath the surface.
STONE|Slate is a dense rock.
SAND|Pale sand is loose sand found on shores.
WATER|Water flows and can be swum through.
WOOD|Alder logs form branches and trunks.
LEAVES|Alder leaves form the tree’s foliage.
PLANKS|Alder boards are crafted from alder wood.
GLOWSTONE|Lumen crystal gives off coloured light.
GLASS|Glass is translucent fired glass.
TNT|A TNT charge is an explosive you can ignite.
GRAVEL|Shore gravel consists of loose rounded stones in shoreline deposits.
CLAY|River clay is dense clay beneath wet shorelines.
BIRCH_WOOD|Birch logs have pale bark.
BIRCH_LEAVES|Birch leaves form light foliage.
BIRCH_PLANKS|Birch boards are pale crafted boards.
PINE_WOOD|Pine logs are dark timber.
PINE_NEEDLES|Pine needles form dense evergreen foliage.
PINE_PLANKS|Pine boards are warm-coloured crafted boards.
GRAY_BRICK|Gray brick is kiln-fired courtyard brick.
GLAZED_ROOF_TILE|Glazed roof tile has a dark blue-gray finish.
IMPERIAL_ROOF_TILE|Jade glazed tile is a green ceremonial roof tile.
LACQUERED_WOOD|Lacquered timber is structural wood with a red finish.
PAPER_PANEL|A paper lattice panel is a rice-paper screen in a wooden lattice.
WHITE_PLASTER|White plaster is smooth whitewashed lime plaster.
CARVED_STONE|Carved stone is finely dressed gray stone.
RED_LANTERN|A red lantern gives off a warm glow.
CHALK_BRICKS|Chalk bricks are pale dressed masonry.
RED_ROCK|Red ironstone is rust-red sedimentary stone rich in iron.
RED_ROCK_BRICKS|Red ironstone bricks are dressed stone masonry.
MOSSY_COBBLE|Mossy cobble is weathered stone covered with living moss.
BASALT_BRICKS|Basalt bricks are dressed dark volcanic masonry.
POLISHED_GRANITE|Polished granite is smooth pink-gray crystalline stone.
WOODLAND_FUNGI|Woodland fungi have small ochre caps and grow beside damp fallen timber.
PLUME_GRASS|Plume grass has pale feathery seed heads in open pampas grassland.
DUNE_GRASS|Dune grass grows in stiff straw-green tufts in sheltered coastal sand.
FALLEN_FRUIT|Fallen orchard fruit can be harvested as fruit.
CAMP_CRATE|A home crate is a storage crate that anchors a player-built home.
REED_THATCH|Reed thatch is woven reed and flax roofing for light coastal buildings.
FLAX|Wild flax grows in blue-flowered colonies in open temperate meadows.
PINK_PLASTER|Blush plaster is lime plaster tinted light pink with flower petals.
ROSE_BOARDS|Rose boards are timber boards painted medium rose pink.
DOOR|A wooden door is a one-metre double door you hang on solid ground. Craft it from boards and right click to open or close it.
WIDE_DOOR|A wide wooden door is a two-metre folding double door for barns and halls.
CHEST|A wooden chest is a lidded storage block. Right click to set it down and open it.
FUCHSIA_TILE|Fuchsia glazed tile is fired clay roof tile with a deep pink glaze.
OAK_WOOD|Oak logs are heavy timber.
OAK_LEAVES|Oak leaves form broad foliage in dense forests.
MOSS|Moss is soft living groundcover.
MOSSY_WOOD|Mossy fallen wood is fallen timber covered with moss.
WILDFLOWERS|Wildflowers are a mix of temperate flowers.
TALL_GRASS|Tall grass grows in meadows.
BEEHIVE|A beehive contains wild-bee comb and its casing.
FRUIT_WOOD|Fruit tree logs form branches and trunks.
BLOSSOM_LEAVES|Blossom leaves form pale orchard foliage.
FRUIT|A fruit block is a compact block of ripe orchard fruit.
PODZOL|Podzol is dark forest soil rich in needles.
SNOW|Snow is loose powder snow.
PACKED_SNOW|Packed snow is compressed snow that can bear weight.
FROZEN_TURF|Frozen turf is cold turf locked by permafrost.
ICE|Ice is clear frozen water.
GLACIER_ICE|Glacier ice is dense blue ice.
BLACK_ICE|Black ice is dark, exceptionally smooth lake ice.
PEAT|Peat is waterlogged taiga soil.
LICHEN|Lichen has pale branching growth.
SANDSTONE|Sandstone is pale layered stone.
CACTUS|A cactus is a ribbed desert plant.
DRY_SHRUB|A dry shrub is a brittle plant from dry country.
RED_SAND|Red sand is desert sand rich in iron.
RED_SANDSTONE|Red sandstone is cemented red sand.
DRY_TURF|Dry turf is sun-bleached grassland turf.
ACACIA_WOOD|Acacia logs form twisted branches and trunks.
ACACIA_LEAVES|Acacia leaves form a flat canopy.
BANDED_CLAY|Banded clay is mesa clay with several natural layers.
BOULDER_STONE|Boulder stone is weathered rock.
MUD|Mud is saturated marsh soil.
REEDS|Reeds are tall wetland plants.
WILLOW_WOOD|Willow logs are pale, flexible timber.
WILLOW_LEAVES|Willow leaves hang from the tree.
DUCKWEED|Duckweed has tiny leaves that float on water.
MANGROVE_WOOD|Mangrove logs form salt-tolerant branches and trunks.
MANGROVE_ROOTS|Mangrove roots form exposed arches.
JUNGLE_WOOD|Jungle logs form tall rainforest branches and trunks.
JUNGLE_LEAVES|Jungle leaves form large rainforest foliage.
VINES|Vines hang in rainforests.
FERN|A fern is a broad understory plant.
KELP|Kelp is long underwater vegetation.
SEAGRASS|Seagrass is short vegetation on the ocean floor.
CORAL_RED|Red coral forms branching growths.
CORAL_GOLD|Gold coral forms branching growths.
CORAL_BLUE|Blue coral forms branching growths.
SEA_SAND|Sea sand is fine pale sand washed by the sea.
COBBLE|Natural cobble is rough, naturally broken stone.
MOUNTAIN_FLOWERS|Mountain flowers are hardy flowers growing among rocks.
BASALT|Basalt is dark volcanic stone.
OBSIDIAN|Obsidian is glassy volcanic stone.
MAGMA_STONE|Magma stone is hot, cracked rock.
ASH|Volcanic ash is loose gray material.
MINERAL_CRUST|Mineral crust forms pale deposits around geothermal water.
WARM_WATER|Warm mineral water is naturally heated and tinted by minerals.
STEAM_VENT|A steam vent is a porous geothermal opening.
BAMBOO|Bamboo forms jointed stems in temperate thickets.
BAMBOO_SHOOT|Bamboo shoots are tender shoots you can walk through.
CHERRY_WOOD|Cherry logs have rose-coloured bark.
CHERRY_BLOSSOM_LEAVES|Pink blossom leaves form dense cherry foliage.
PETAL_CARPET|A petal carpet is a thin layer of fallen pink petals.
AMBER_LEAVES|Amber leaves are golden autumn foliage.
RUSSET_LEAVES|Russet leaves are deep orange-red autumn foliage.
LEAF_LITTER|Leaf litter is a thin carpet of dry fallen leaves.
HEATHER|Heather has low purple flowers in heathland.
LAVENDER|Lavender has tall violet flowers.
RICH_TURF|Rich turf is dark fertile grassland turf.
CHALK|Chalk is soft white stone from rolling downs.
FLINT|Flint is hard dark stone embedded in chalk country.
SHORT_GRASS|Short grass is closely cropped grass from the downs.
SEDGE|Sedge is fine wetland vegetation.
GIANT_WOOD|Giant old-growth logs form the trunks of two-by-two trees.
DEADWOOD|Deadwood is weathered fallen or standing dead timber.
ICE_SPIRE|An ice spire is a wind-carved formation of packed ice.
DARK_WATER|Dark fjord water is cold, deep water.
SLATE_SCREE|Slate scree consists of loose angular slate fragments.
GLOW_LICHEN|Glow lichen gives off faint light in aurora country.
FIRN|Firn is old compacted alpine snow.
CREVASSE_ICE|Crevasse ice is blue ice exposed inside a snowfield crevasse.
CHARRED_WOOD|A charred log is fire-blackened timber.
FIREWEED|Fireweed has pink flowers and grows after a forest burn.
PALM_WOOD|Palm logs form ringed tropical trunks.
PALM_FRONDS|Palm fronds form broad radial foliage.
DATES|A date cluster is a compact cluster of ripe dates.
FRESH_WATER|Fresh water is clear oasis water.
SALT|A salt block is crystalline salt-flat crust.
CRACKED_CLAY|Cracked clay is sun-baked clay with polygonal cracks.
FINE_SAND|Fine dune sand forms deep, loose deposits.
MESQUITE_WOOD|Mesquite logs are thorny scrub-country timber.
THORN_BUSH|Thorn bushes are dense bushes you can walk through.
OCHRE_CLAY|Ochre clay is yellow-orange clay from painted hills.
UMBER_CLAY|Umber clay is dark brown clay from painted hills.
SIENNA_CLAY|Sienna clay is warm red-brown clay from painted hills.
LIMESTONE|Limestone is pale soluble karst stone.
SHARP_LIMESTONE|Sharp limestone is jagged exposed karst stone.
HANGING_VINE|A hanging vine is a long vine from karst country.
EPIPHYTE_MOSS|Epiphyte moss is moist moss from cloud forests.
FIG_WOOD|Fig logs are pale tropical timber.
BROAD_LEAVES|Broad leaves form glossy cloud-forest foliage.
BOG_IRON|Bog iron is a rust-dark deposit rich in iron.
COTTON_GRASS|Cotton grass has white tufts in peat bogs.
CYPRESS_WOOD|Cypress logs are dark timber from water-loving trees.
CYPRESS_KNEES|Cypress knees are raised roots.
BLACK_WATER|Black water is bayou water darkened by tannins.
MOSS_VEIL|A moss veil is hanging bayou moss.
TALL_REEDS|Tall reeds grow very tall in flooded grassland.
WATER_LILY|A water lily has a floating pad and flowers.
WET_STONE|Wet stone is rain-darkened tepui rock.
BROMELIAD|A bromeliad is a tropical plant shaped like a rosette.
ENDEMIC_FLOWERS|Endemic flowers are bright flowers native to tepuis.
BLACK_SAND|Black sand is volcanic beach sand.
SHELL_SAND|Shell sand is pale beach sand made of shell fragments.
DRIFTWOOD|Driftwood is salt-bleached timber.
BARNACLE_ROCK|Barnacle rock is tide-pool stone covered with barnacles.
ANEMONE|An anemone is a colourful tide-pool animal.
STARFISH|A starfish is a small tide-pool animal.
LAYERED_SANDSTONE|Layered sandstone has horizontal beds in sea stacks.
GUANO_ROCK|Guano rock is sea-stack stone capped with white guano.
GIANT_KELP|Giant kelp is tall deep-ocean vegetation.
HOLDFAST_ROCK|Holdfast rock is rough stone anchoring giant kelp.
IMPACT_GLASS|Impact glass is glass fused by a meteor impact.
SCORCHED_STONE|Scorched stone is heat-darkened meteor-field rock.
IRON_ORE|Iron ore chunks are exposed pieces of iron ore.
GEYSERITE|Geyserite is porous white stone from geyser basins.
BOILING_WATER|Boiling water is hazardously hot geothermal water.
SULFUR_CRUST|Sulfur crust is a bright yellow deposit.
PAHOEHOE|Pahoehoe stone is cooled basaltic lava with a ropy surface.
LAVA_ROCK|Lava rock is rough, recently cooled lava.
GRANITE|Granite is coarse crystalline stone.
EXFOLIATED_GRANITE|Exfoliated granite forms pale slabs with peeling layers.
SLATE_SHALE|Slate shale is thin layered quarry rock.
AMETHYST_BLOCK|An amethyst block is solid violet amethyst.
AMETHYST_CLUSTER|An amethyst cluster is a pointed, luminous growth.
DARK_STONE|Dark gorge stone is near-black bedrock.
""".strip().splitlines())


def parse_table(value):
    """Fail on an unrecognized registry row instead of silently dropping it."""
    body = value.split('blocks! {', 1)[1]
    docs, rows = [], []
    for line_number, line in enumerate(value.splitlines(), 1):
        if line.strip() == 'blocks! {':
            start = line_number
            break
    for line_number, line in enumerate(body.splitlines(), start):
        stripped = line.strip()
        if stripped.startswith('///'):
            docs.append(stripped[3:].strip())
        elif match := ROW.fullmatch(line):
            symbol, block_id, label, rgb = match.groups()
            if not docs:
                raise ValueError(f'{symbol}: missing documentation')
            rows.append(dict(symbol=symbol, id=int(block_id), name=json.loads(label),
                             color=[float(x.strip()) for x in rgb.split(',')],
                             sourceDescription=' '.join(docs), evidence=f'{TABLE}:{line_number}'))
            docs = []
        elif stripped and not stripped.startswith('//') and stripped != '}':
            raise ValueError(f'Unrecognized block row: {stripped}')
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Empty or duplicate block registry')
    if any(len(r['color']) != 3 or any(not 0 <= c <= 1 for c in r['color']) for r in rows):
        raise ValueError('Invalid registry colour')
    return rows


def player_description(row):
    return DESCRIPTIONS[row['symbol']]


def build_data(game, recipes, ledger):
    commit = (game / 'SNAPSHOT_COMMIT').read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Snapshot must supply a full audited commit')
    source = (game / TABLE).read_bytes()
    blocks = [b for b in parse_table(source.decode()) if b['symbol'] not in STATE_ONLY]
    catalogue = next(f for f in ledger['features'] if f['id'] == 'block-materials-catalogue')
    for block in blocks:
        symbol = block['symbol']
        block.update(anchor='block-' + symbol.lower().replace('_', '-'),
                     family=FAMILY_BY_BLOCK[symbol], description=player_description(block))
        matches = [r['name'] for r in recipes['recipes'] if r['output'] == block['name']]
        if matches:
            block['recipes'] = matches
        elif symbol in CREATIVE_ONLY:
            if CREATIVE_ONLY[symbol] not in catalogue['notes']:
                raise ValueError(f'{symbol}: creative-only ledger evidence changed')
            block['creativeOnly'] = True
            block['acquisitionEvidence'] = 'data/features.json: block-materials-catalogue notes'
    return dict(schema=1, game=dict(commit=commit, source=TABLE,
                                   sourceSha256=hashlib.sha256(source).hexdigest()),
                recipeGame=recipes['game'], acquisitionGame=ledger['game'], catalogCount=len(blocks),
                families=[dict(id=key, name=label) for key, label in FAMILIES], blocks=blocks)


def render(data):
    sections = [(f['id'], f['name']) for f in data['families']]
    out = [article_open('Blocks', 'blocks.html',
                       'Compare ground, stone, wood and building materials. Follow a recipe link to see its ingredients and amounts.',
                       sections, 'build_blocks.py')]
    for family, label in sections:
        members = [b for b in data['blocks'] if b['family'] == family]
        out.append(f'<section class="guide-section" id="{family}"><h2>{escape(label)}</h2>'
                   '<div class="table-wrap"><table class="key-table block-table">'
                   f'<caption>{len(members)} materials</caption><thead><tr><th scope="col">Block</th>'
                   '<th scope="col">Description</th><th scope="col">How to get it</th></tr></thead><tbody>')
        for block in members:
            color = ','.join(str(round(v * 255)) for v in block['color'])
            recipes = '<br>'.join(f'<a href="guide-crafting.html#{recipe_anchor(name)}">{escape(name)}</a>'
                                 for name in block.get('recipes', []))
            if block.get('creativeOnly'):
                recipes = 'Creative only'
            out.append(f'<tr id="{block["anchor"]}"><th scope="row">'
                       f'<span class="block-swatch" style="background:rgb({color})" aria-hidden="true"></span>'
                       f'<a href="#{block["anchor"]}">{escape(block["name"])}</a></th>'
                       f'<td data-label="Description">{escape(block["description"])}</td>'
                       f'<td data-label="How to get it">{recipes}</td></tr>')
        out.append('</tbody></table></div></section>')
    out.append('<p class="reference-receipt">Colours are base tints; textures and lighting change their appearance. '
               f'<a href="data/blocks.json">Block reference</a>: {data["catalogCount"]} entries, including air, '
               f'Voxelgame <code>{data["game"]["commit"][:7]}</code>. '
               f'<a href="guide-crafting.html#recipes">Recipes</a>: '
               f'<code>{data["recipeGame"]["commit"][:7]}</code>. Creative-only entries: '
               f'<a href="features.html#f-block-materials-catalogue">material ledger</a>, '
               f'<code>{data["acquisitionGame"]["commit"][:7]}</code>.</p>')
    return ''.join(out) + article_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path)
    args = parser.parse_args()
    path = ROOT / 'data/blocks.json'
    if args.game:
        data = build_data(args.game, json.loads((ROOT / 'data/recipes.json').read_text()),
                          json.loads((ROOT / 'data/features.json').read_text()))
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    else:
        data = json.loads(path.read_text())
    (ROOT / 'blocks.html').write_text(render(data))
    print(f'Built {data["catalogCount"]} base-game block entries')


if __name__ == '__main__':
    main()
