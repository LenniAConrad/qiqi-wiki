#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Assemble a portable, offline-friendly catalog from the measured survey."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
 'Woodlands': 'BirchGrove DenseForest Orchard PineHighlands Rainforest BambooThicket CherryGrove AutumnForest OldGrowthForest BorealBurn CloudForest MediterraneanWoodland TemperateRainforest RedwoodForest MonsoonForest TropicalDryForest MiomboWoodland MontaneForest',
 'Grasslands': 'Meadow FlowerMeadow Savanna Steppe Heathland LavenderFields RollingDowns TallgrassPrairie Pampas AustralianBushland AfricanThornveld ChalkHeath RedRockSteppe',
 'Drylands': 'Desert RedDesert Badlands Oasis SaltFlats DuneSea Scrubland PaintedHills Chaparral',
 'Cold & alpine': 'SnowyTundra SnowyPeaks FrozenLake IceSpikes AuroraTundra FirnField PolarDesert AlpineMeadow GlacialMoraine GlacialOutwash RockyHighlands MossyHighlands',
 'Wetlands': 'TaigaBog Marsh RiverDelta WetlandFen PeatBog BlackwaterBayou FloodedGrassland Muskeg FloodplainForest InlandDelta ColdRiver TropicalRiver TemperateSaltMarsh',
 'Coasts & seas': 'MangroveCoast GravelShore OceanFloor CoralShallows RockyCliffs FrozenFjord BlackSandBeach ShellBeach TidePools SeaStacks DeepKelpForest Atoll CoastalDunes OpenOcean SeagrassLagoon',
 'Geological': 'Volcanic HotSprings KarstPinnacles TepuiPlateau MeteorField GeyserBasin LavaTubes GraniteDomes SlateQuarryHills AmethystGorge LimestonePavement VolcanicCaldera'
}
TAGS = {'Volcanic':'volcano lava magma', 'VolcanicCaldera':'volcano crater lava', 'RockyCliffs':'cliff island steep mountain', 'SeaStacks':'cliff island steep towers', 'LavaTubes':'volcano caves tunnels', 'AmethystGorge':'crystal crystals canyon amethyst metystone ametyst amethist', 'SnowyPeaks':'mountain mountains steep', 'RockyHighlands':'mountain mountains steep', 'AlpineMeadow':'mountain mountains', 'MontaneForest':'mountain mountains', 'CloudForest':'mountain mountains', 'MeteorField':'meteor impact crater', 'GeyserBasin':'steam vents geothermal', 'HotSprings':'steam vents geothermal'}
def build(root=ROOT):
 survey = json.loads((root/'data/survey.json').read_text())
 habitats = json.loads((root/'data/habitats.json').read_text())
 descriptions = json.loads((root/'data/descriptions.json').read_text())
 capture_path = root/'data/captures.json'
 captures = json.loads(capture_path.read_text()) if capture_path.exists() else {}
 provenance=json.loads((root/'data/provenance.json').read_text())
 assert provenance['generator_version']==survey['generatorVersion'],'Survey and provenance generations differ'
 assert set(captures)=={b['id'] for b in survey['biomes']},'Every surveyed biome needs a genuine capture'
 rows = sorted(survey['biomes'],key=lambda b:(-b['count'],b['name']))
 for rank,b in enumerate(rows,1):
  matching = [group for group,ids in GROUPS.items() if b['id'] in ids.split()]
  assert len(matching)==1,(b['id'],matching)
  b.update(rank=rank,percent=b['count']/survey['totalSamples']*100,category=matching[0],description=descriptions[b['id']],habitat=habitats[b['id']],image=f"images/{b['id']}.webp",tags=TAGS.get(b['id'],''))
  if b['id'] in captures:
   c=captures[b['id']]
   assert c['generatorVersion']==survey['generatorVersion'],(b['id'],'stale capture generation')
   b['camera']=c['camera']; b['look']=c['look']; b['capture']=c['file']
   if c.get('framingNote'):b['framingNote']=c['framingNote']
   for key in ['seed','x','z','height','water']:
    if key in c:b[key]=c[key]
 data={**survey,'biomes':rows,'featuredId':'DenseForest','provenance':provenance}
 content=json.dumps(data,indent=2,ensure_ascii=False)
 (root/'data/biomes.json').write_text(content+'\n')
 (root/'data/biomes.js').write_text('// SPDX-License-Identifier: GPL-3.0-only\nwindow.BIOME_ATLAS = '+content+';\n')
 print(f"Built {len(rows)} biomes; {survey['totalSamples']:,} samples; percentages sum to {sum(b['percent'] for b in rows):.12f}%")
if __name__=='__main__':build()
