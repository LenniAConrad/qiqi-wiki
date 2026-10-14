#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check catalog completeness, measurements, capture provenance, and image files."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from biome_capture_evidence import camera_view, sha
from refresh_survey import validate_survey
ROOT=Path(__file__).resolve().parents[1]
def validate_catalog(root=ROOT, game=None):
 data=json.loads((root/'data/biomes.json').read_text())
 survey=json.loads((root/'data/survey.json').read_text())
 captures=json.loads((root/'data/captures.json').read_text())
 provenance=json.loads((root/'data/provenance.json').read_text())
 habitats=json.loads((root/'data/habitats.json').read_text())
 overrides_path=root/'data/viewpoints.json'
 overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
 survey_sha=sha(root/'data/survey.json')
 version=provenance['generator_version']
 validate_survey(survey, version)
 if provenance.get('evidence_version') == 2:
  assert provenance['survey_sha256']==survey_sha, 'Survey differs from published evidence'
  assert provenance['viewpoints_sha256']==sha(overrides_path), 'Viewpoints differ from published evidence'
  assert provenance['captures_sha256']==sha(root/'data/captures.json'), 'Captures differ from published evidence'
  assert provenance['capture_binary_sha256']==[provenance['binary_sha256']]
  for capture in captures.values():
   assert capture['surveyManifestSha256']==provenance['survey_manifest_sha256']
   assert capture['buildManifestSha256']==provenance['build_manifest_sha256']
   assert capture['captureManifestSha256']==provenance['capture_manifest_sha256']
 else:
  assert 'evidence_version' not in provenance and version==9, 'Unknown atlas evidence format'
 for name,entry in overrides.items():
  if {'seed','x','z','height','water','camera','look','framingNote'}.intersection(entry):
   assert entry.get('surveySha256')==survey_sha,(name,'stale viewpoint')
 if game:
  sources={**provenance['related_sources'],**provenance['renderer_sources'],
           'crates/voxelgame-core/src/world/generator.rs':provenance['generator_sha256']}
  for name,expected in sources.items():
   assert sha(game/name)==expected,('stale game source',name)
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
 assert (root/'data/biomes.js').read_text().split('window.BIOME_ATLAS = ',1)[1].rstrip().removesuffix(';')==json.dumps(data,indent=2,ensure_ascii=False)
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
  camera,look=camera_view(expected)
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
  assert capture['generatorVersion']==data['generatorVersion']==survey['generatorVersion']==version
  assert capture['shader']=='fast' and capture['time']==0.43 and capture['weather']=='clear'
  assert capture['viewDistance']==64
  assert capture['renderer']['detail_clip_radius_metres']+0.01>=capture['renderer']['detail_clip_target_metres'],(b['id'],'terrain still streaming')
  assert b['image']==capture['file']==f"images/{b['id']}.webp"
  path=root/b['image']
  assert path.is_file(),path
  digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest not in digests;digests.add(digest)
  assert digest==capture['imageSha256']
  assert b['look']==capture['look'] and b['x']==capture['x'] and b['z']==capture['z']
  with Image.open(path) as image:assert image.size==(960,540);image.verify()
 print(f'PASS: generation {version}, 92 unique screenshots, exact sampling and capture metadata.')

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--game',type=Path,help='Also compare generator and shader hashes with this checkout')
 parser.add_argument('--root',type=Path,default=ROOT,help='Atlas or private publication candidate')
 args=parser.parse_args()
 validate_catalog(args.root, args.game)

if __name__=='__main__':main()
