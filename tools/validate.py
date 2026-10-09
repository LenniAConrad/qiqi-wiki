#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check catalog completeness, measurements, capture provenance, and image files."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--game',type=Path,help='Also compare generator and shader hashes with this checkout')
 args=parser.parse_args()
 data=json.loads((ROOT/'data/biomes.json').read_text())
 survey=json.loads((ROOT/'data/survey.json').read_text())
 captures=json.loads((ROOT/'data/captures.json').read_text())
 provenance=json.loads((ROOT/'data/provenance.json').read_text())
 habitats=json.loads((ROOT/'data/habitats.json').read_text())
 overrides_path=ROOT/'data/viewpoints.json'
 overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
 survey_sha=hashlib.sha256((ROOT/'data/survey.json').read_bytes()).hexdigest()
 for name,entry in overrides.items():
  if {'seed','x','z','height','water','camera','look','framingNote'}.intersection(entry):
   assert entry.get('surveySha256')==survey_sha,(name,'stale viewpoint')
 if args.game:
  sources={**provenance['related_sources'],**provenance['renderer_sources'],
           'crates/voxelgame-core/src/world/generator.rs':provenance['generator_sha256']}
  for name,expected in sources.items():
   assert hashlib.sha256((args.game/name).read_bytes()).hexdigest()==expected,('stale game source',name)
 assert data['provenance']==provenance
 capture_snapshots={provenance['generator_sha256']:provenance['related_sources'],
                    **provenance.get('capture_generator_snapshots',{})}
 rows=data['biomes'];ids={b['id'] for b in rows}
 assert len(rows)==len(ids)==92
 assert set(captures)==ids
 assert set(habitats)==ids
 assert sum(b['count'] for b in rows)==data['totalSamples']==6_504_971
 assert abs(sum(b['percent'] for b in rows)-100)<1e-9
 assert [b['rank'] for b in rows]==list(range(1,93))
 assert [b['count'] for b in rows]==sorted((b['count'] for b in rows),reverse=True)
 assert len(data['seeds'])==11
 assert data['totalSamples']==len(data['seeds'])*(data['radiusMetres']*2//data['strideMetres']+1)**2
 assert (ROOT/'data/biomes.js').read_text().split('window.BIOME_ATLAS = ',1)[1].rstrip().removesuffix(';')==json.dumps(data,indent=2,ensure_ascii=False)
 reference={b['id']:b for b in survey['biomes']}
 digests=set()
 for b in rows:
  assert b['count']==reference[b['id']]['count']>0
  assert abs(b['percent']-b['count']/data['totalSamples']*100)<1e-12
  assert isinstance(b['seed'],str) and b['seed'].isdecimal()
  assert b['description'] and b['category']
  assert b['habitat']==habitats[b['id']] and all(b['habitat'].values())
  capture=captures[b['id']]
  expected={**reference[b['id']],**overrides.get(b['id'],{})}
  assert all(capture[key]==expected[key] for key in ['seed','x','z','height','water']),b['id']
  camera=expected['camera'][:]
  target=[expected['x'],max(expected['height']+3,expected['water']),expected['z']]
  if 'look' not in expected and b['id'] in ['OceanFloor','DeepKelpForest','SeagrassLagoon','CoralShallows'] and expected['water']-expected['height']>8:
   camera=[expected['x']-10,expected['height']+5,expected['z']-14]
   target=[expected['x'],expected['height']+1.5,expected['z']]
  dx,dz=target[0]-camera[0],target[2]-camera[2]
  look=expected.get('look',[math.degrees(math.atan2(dx,dz)),math.degrees(math.atan2(target[1]-camera[1]-1.62,math.hypot(dx,dz)))])
  assert capture['camera']==camera and capture['look']==look,(b['id'],'stale viewpoint')
  assert b.get('framingNote')==capture.get('framingNote')==expected.get('framingNote'),(b['id'],'stale framing note')
  assert capture['warmupFrames']>=expected.get('warmupFrames',600),(b['id'],'insufficient warm-up')
  assert capture['generatorSha256'] in capture_snapshots,b['id']
  assert capture['generatorSourcesSha256']==capture_snapshots[capture['generatorSha256']],b['id']
  assert capture['binarySha256'] in provenance['capture_binary_sha256'],b['id']
  assert capture['sourceManifestSha256']==provenance['capture_source_manifest_sha256'],b['id']
  assert capture['seed']==b['seed'] and capture['camera']==b['camera']
  assert capture['encoding']=={'format':'WebP','quality':94,'method':6}
  assert b['water']==capture['water']
  assert capture['generatorVersion']==data['generatorVersion']==survey['generatorVersion']==provenance['generator_version']==9
  assert capture['shader']=='fast' and capture['time']==0.43 and capture['weather']=='clear'
  assert capture['viewDistance']==64
  assert capture['renderer']['detail_clip_radius_metres']+0.01>=capture['renderer']['detail_clip_target_metres'],(b['id'],'terrain still streaming')
  path=ROOT/b['image']
  assert path.is_file(),path
  digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest not in digests;digests.add(digest)
  assert digest==capture['imageSha256']
  assert b['look']==capture['look'] and b['x']==capture['x'] and b['z']==capture['z']
  with Image.open(path) as image:assert image.size==(960,540);image.verify()
 print('PASS: 92 unique screenshots, all biomes, exact sample totals, ranks, percentages, seeds, and capture metadata.')
if __name__=='__main__':main()
