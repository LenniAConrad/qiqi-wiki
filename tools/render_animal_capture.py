# SPDX-License-Identifier: GPL-3.0-only
"""Run with headless Blender; wrap the unchanged portrait renderer in capture receipts."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from freeze_media_source import sha, verify_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--exporter', type=Path, required=True)
    parser.add_argument('--species', nargs='*', default=[])
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    snapshot = verify_snapshot(args.game, args.source_manifest)
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Use a new output directory; previous captures are never overwritten')
    args.output.mkdir(parents=True, exist_ok=True)
    slugs = sorted(args.species or [p.name.removesuffix('--idle.obj')
                                  for p in args.input.glob('*--idle.obj')])
    pose_files = {f'{slug}--{pose}.obj' for slug in slugs for pose in ('idle', 'stride')}
    meshes = {str(p.relative_to(args.input)): sha(p) for p in sorted(args.input.rglob('*'))
              if p.is_file() and (p.suffix != '.obj' or p.name in pose_files)}
    portrait_script = ROOT / 'tools/render_animals.py'
    receipt = {'sourceCommit': snapshot['commit'],
               'sourceManifestSha256': sha(args.source_manifest),
               'wikiRenderScriptSha256': sha(portrait_script),
               'gameRenderScriptSha256': sha(args.game / 'tools/render_creature_gallery.py'),
               'captureDriverSha256': sha(Path(__file__)),
               'exporterSha256': sha(args.exporter), 'meshHashes': meshes,
               'started': datetime.now(timezone.utc).isoformat(), 'species': slugs}
    # A failed/interrupted render has only a start receipt, never a completed receipt.
    (args.output / 'capture-start.json').write_text(json.dumps(receipt, indent=2) + '\n')
    sys.argv = [str(portrait_script), '--', '--game', str(args.game), '--input', str(args.input),
                '--output', str(args.output), '--species', *slugs]
    state = runpy.run_path(str(portrait_script), run_name='__main__')
    bpy = state['gallery'].bpy
    scene = bpy.context.scene
    expected = {f'{slug}--{pose}--{angle}.png' for slug in slugs
                for pose in ('idle', 'stride') for angle in ('three-quarter', 'side')}
    if {p.name for p in args.output.glob('*.png')} != expected:
        raise ValueError('Incomplete or unexpected portrait outputs')
    receipt.update({'renderHashes': {name: sha(args.output / name) for name in sorted(expected)},
                    'finished': datetime.now(timezone.utc).isoformat(),
                    'blenderVersion': bpy.app.version_string, 'engine': scene.render.engine,
                    'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                    'renderSettings': {'viewTransform': scene.view_settings.view_transform,
                                       'look': scene.view_settings.look,
                                       'exposure': scene.view_settings.exposure,
                                       'gamma': scene.view_settings.gamma,
                                       'samples': getattr(scene.eevee, 'taa_render_samples', None),
                                       'threads': scene.render.threads,
                                       'threadsMode': scene.render.threads_mode,
                                       'background': bpy.app.background}})
    (args.output / 'render-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'CAPTURE COMPLETE: {len(slugs)} animals, {len(expected)} portraits with input/output hashes.', flush=True)


if __name__ == '__main__':
    main()
