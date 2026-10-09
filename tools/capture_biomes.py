#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Capture actual procedural habitats through Voxelgame's disposable renderer.

Requires the sibling Voxelgame checkout, a devtools release binary, and Pillow.
No normal saves are loaded or written. Raw PNGs and replay evidence stay in .cache.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import tempfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--game',type=Path,default=ROOT.parent/'Voxelgame')
 parser.add_argument('--binary',type=Path,default=ROOT/'.cache/voxelgame')
 parser.add_argument('--source-manifest',type=Path,help='Frozen build manifest; validates executable and records its exact source hashes')
 parser.add_argument('--ids',nargs='*')
 parser.add_argument('--manifest',type=Path,default=ROOT/'data/captures.json')
 parser.add_argument('--overwrite',action='store_true')
 parser.add_argument('--batches',type=int,help='Override per-viewpoint warm-up with this many 120-frame batches')
 args=parser.parse_args()
 args.game=args.game.resolve()
 args.binary=args.binary.resolve()
 if args.source_manifest:args.source_manifest=args.source_manifest.resolve()
 if args.batches is not None and args.batches<1:parser.error('--batches must be positive')
 binary_sha256=hashlib.sha256(args.binary.read_bytes()).hexdigest()
 snapshot=json.loads(args.source_manifest.read_text()) if args.source_manifest else None
 snapshot_sha=hashlib.sha256(args.source_manifest.read_bytes()).hexdigest() if snapshot else None
 if snapshot:
  assert snapshot['binarySha256']==binary_sha256,'Frozen manifest does not match capture executable'
  generator_sha256=snapshot['generatorSha256']
  generator_sources=snapshot['generatorSourcesSha256']
 else:
  generator_sha256=hashlib.sha256((args.game/'crates/voxelgame-core/src/world/generator.rs').read_bytes()).hexdigest()
  generator_sources={str(path.relative_to(args.game)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((args.game/'crates/voxelgame-core/src/world/generator').rglob('*.rs'))}
  generator_sources['crates/voxelgame-core/src/world/block.rs']=hashlib.sha256((args.game/'crates/voxelgame-core/src/world/block.rs').read_bytes()).hexdigest()
 sys.path.insert(0,str(args.game/'tools'))
 from game_debug import DebugGame
 data=json.loads((ROOT/'data/survey.json').read_text())
 survey_sha=hashlib.sha256((ROOT/'data/survey.json').read_bytes()).hexdigest()
 if args.ids:
  unknown=set(args.ids)-{b['id'] for b in data['biomes']}
  if unknown:parser.error(f'Unknown biome ids: {sorted(unknown)}')
 if snapshot:
  assert snapshot['generatorVersion']==data['generatorVersion'],'Survey and frozen build use different generators'
  survey_record=json.loads((args.source_manifest.parent/'survey-manifest.json').read_text())
  assert survey_record['sourceManifestSha256']==snapshot_sha,'Survey uses another source snapshot'
  assert survey_record['surveySha256']==survey_sha,'Survey changed after source verification'
 manifest=args.manifest
 captures=json.loads(manifest.read_text()) if manifest.exists() else {}
 overrides_path=ROOT/'data/viewpoints.json'
 overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
 for name,entry in overrides.items():
  if {'seed','x','z','height','water','camera','look','framingNote'}.intersection(entry):
   assert entry.get('surveySha256')==survey_sha,(name,'stale viewpoint; prepare it for this survey')
 rows=[{**b,**overrides.get(b['id'],{})} for b in data['biomes'] if args.ids is None or b['id'] in args.ids]
 for index,b in enumerate(rows):
  image_path=ROOT/'images'/f"{b['id']}.webp"
  previous=captures.get(b['id'],{})
  warmup_frames=args.batches*120 if args.batches is not None else b.get('warmupFrames',600)
  if not isinstance(warmup_frames,int) or warmup_frames<120 or warmup_frames%120:
   raise ValueError(f"{b['id']}: warmupFrames must be a positive multiple of 120")
  camera=b['camera'][:]
  target=[b['x'],max(b['height']+3,b['water']),b['z']]
  # Underwater photographs reveal the sea-floor habitats instead of only water.
  if 'look' not in b and b['id'] in ['OceanFloor','DeepKelpForest','SeagrassLagoon','CoralShallows'] and b['water']-b['height']>8:
   camera=[b['x']-10,b['height']+5,b['z']-14]
   target=[b['x'],b['height']+1.5,b['z']]
  dx,dz=target[0]-camera[0],target[2]-camera[2]
  look=b.get('look',[math.degrees(math.atan2(dx,dz)),math.degrees(math.atan2(target[1]-camera[1]-1.62,math.hypot(dx,dz)))])
  if (not args.overwrite and image_path.exists()
      and all(previous.get(key)==b[key] for key in ['seed','x','z','height','water'])
      and previous.get('encoding')=={'format':'WebP','quality':94,'method':6}
      and previous.get('camera')==camera and previous.get('look')==look
      and previous.get('viewDistance')==64
      and previous.get('generatorVersion')==data['generatorVersion']
      and previous.get('warmupFrames',0)>=warmup_frames
      and previous.get('binarySha256')==binary_sha256
      and previous.get('generatorSha256')==generator_sha256
      and previous.get('generatorSourcesSha256')==generator_sources
      and (not snapshot or previous.get('sourceManifestSha256')==snapshot_sha)
      and previous.get('imageSha256')==hashlib.sha256(image_path.read_bytes()).hexdigest()):continue
  began=time.monotonic()
  capture_root=ROOT/'.cache/captures'
  capture_root.mkdir(parents=True,exist_ok=True)
  evidence=Path(tempfile.mkdtemp(prefix=b['id']+'-',dir=capture_root))
  game=DebugGame(args.binary,evidence,120)
  try:
   game.call('reset',{'seed':b['seed'],'generator':'current','mods':[]})
   game.call('configure',{'position':camera,'look':look,'mode':'creative','flying':True,'time':0.43,'weather':'clear','shader':'fast','view_distance':64})
   game.call('step',{'frames':1,'keys':['F1']})
   actual_warmup=warmup_frames
   for _ in range(warmup_frames//120):state=game.call('step',{'frames':120,'render':True})
   # Fixed simulation frames do not guarantee asynchronous terrain readiness
   # when another job uses the GPU. Wait for the detailed terrain handoff,
   # preserving the actual extra warm-up in the reproducible capture record.
   for _ in range(24):
    renderer=state['renderer']
    if renderer['detail_clip_radius_metres']+0.01>=renderer['detail_clip_target_metres']:break
    state=game.call('step',{'frames':120,'render':True});actual_warmup+=120
   renderer=state['renderer']
   if renderer['detail_clip_radius_metres']+0.01<renderer['detail_clip_target_metres']:
    raise RuntimeError(f"{b['id']}: detailed terrain did not settle")
   # Fix the final daylight phase after the simulation warm-up.
   game.call('configure',{'time':0.43})
   result=game.call('capture_frame',{'name':f"{b['id']}.png"})
   state=result['state']
   assert state['generator_version']==data['generatorVersion']
   assert state['save_writes'] is False and state['world']['edited_voxels']==0
   source=Path(result['path'])
   with Image.open(source) as image:
    assert image.size==(960,540)
    pending_image=image_path.with_suffix('.tmp')
    image.save(pending_image,'WEBP',quality=94,method=6)
    pending_image.replace(image_path)
   captures[b['id']]={'file':str(image_path.relative_to(ROOT)),'imageSha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'seed':b['seed'],'x':b['x'],'z':b['z'],'height':b['height'],'water':b['water'],'camera':camera,'look':look,'time':0.43,'weather':'clear','shader':'fast','viewDistance':64,'warmupFrames':actual_warmup,'generatorVersion':state['generator_version'],'renderer':state['renderer'],'evidence':str(evidence.relative_to(ROOT))}
   if b.get('framingNote'):captures[b['id']]['framingNote']=b['framingNote']
   captures[b['id']]['encoding']={'format':'WebP','quality':94,'method':6}
   captures[b['id']]['binarySha256']=binary_sha256
   captures[b['id']]['generatorSha256']=generator_sha256
   captures[b['id']]['generatorSourcesSha256']=generator_sources
   if snapshot:captures[b['id']]['sourceManifestSha256']=snapshot_sha
   temporary=manifest.with_suffix('.tmp');temporary.write_text(json.dumps(captures,indent=2)+'\n');temporary.replace(manifest)
   print(f"[{index+1}/{len(rows)}] {b['id']} seed {b['seed']}, {time.monotonic()-began:.1f}s, {image_path.stat().st_size//1024} KiB",flush=True)
  finally:game.close()
if __name__=='__main__':main()
