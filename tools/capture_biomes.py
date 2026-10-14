#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage genuine headless biome photographs; never write into the public gallery."""
import argparse
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time

from PIL import Image

from biome_capture_evidence import (ENCODING, LOCATION, SETTINGS, build_input, camera_view,
                                    capture_files, read, survey_inputs, write)
from freeze_media_source import sha
from refresh_survey import private_path

ROOT = Path(__file__).resolve().parents[1]


def capture_contract(game, manifest, survey_dir, build_manifest):
    if 'files' not in read(manifest):
        raise ValueError('Fresh captures require a complete frozen media-source manifest')
    source, survey_record, survey, rows = survey_inputs(game, manifest, survey_dir)
    build, binary = build_input(game, manifest, build_manifest)
    expected = {key: source[key] for key in
                ('generatorVersion', 'generatorSha256', 'generatorSourcesSha256')}
    expected.update(binarySha256=build['binarySha256'], sourceManifestSha256=sha(manifest),
                    surveyManifestSha256=sha(survey_dir / 'survey-manifest.json'),
                    buildManifestSha256=sha(build_manifest))
    contract = {'schema': 2, 'source': source, 'expected': expected,
                'surveySha256': survey_record['surveySha256'], 'settings': SETTINGS,
                'encoding': ENCODING, 'resolution': [960, 540],
                'driverHashes': {name: sha(ROOT / 'tools' / name) for name in
                                 ('capture_biomes.py', 'biome_capture_evidence.py')}}
    return contract, binary, survey, rows


def native_adapter(game):
    # Import only from the verified export, without adding an unrecorded __pycache__.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('wiki_frozen_game_debug', game / 'tools/game_debug.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DebugGame


def capture(game, manifest, survey_dir, build_manifest, output, ids=None, resume=False,
            seconds=3600, batches=None, adapter_factory=None):
    game, manifest = game.resolve(), manifest.resolve()
    survey_dir, build_manifest = survey_dir.resolve(), build_manifest.resolve()
    output = private_path(output, game)
    if (output.is_relative_to(survey_dir) or output.is_relative_to(build_manifest.parent)
            or seconds < 1 or (batches is not None and batches < 1)):
        raise ValueError('Use separate private capture scratch and positive time/frame limits')
    contract, binary, survey, rows = capture_contract(game, manifest, survey_dir, build_manifest)
    if ids is not None and (not ids or set(ids) - {row['id'] for row in rows}):
        raise ValueError('Empty or unknown biome selection')
    contract['minimumWarmupFrames'] = batches * 120 if batches else None
    start_path = output / 'capture-start.json'
    if resume:
        if (output / 'capture-invalid.json').exists():
            raise ValueError('Run invalidated by changed inputs; use a new capture directory')
        if read(start_path) != contract:
            raise ValueError('Resume inputs changed; preserve this run and use a new directory')
    else:
        output.mkdir(parents=True, exist_ok=False)
        (output / 'images').mkdir()
        (output / 'evidence').mkdir()
        write(start_path, contract)
    for directory in ('images', 'evidence'):
        path = output / directory
        if path.is_symlink() or not path.is_dir():
            raise ValueError('Capture output directories must be ordinary private directories')
    captures_path = output / 'captures.json'
    captures = read(captures_path) if captures_path.exists() else {}
    capture_files(output, captures, rows, contract['expected'], complete=False)
    factory = adapter_factory or native_adapter(game)
    deadline = time.monotonic() + seconds
    try:
        for row in rows:
            name = row['id']
            if name in captures or (ids is not None and name not in ids):
                continue
            warmup = max(row.get('warmupFrames', 600), batches * 120 if batches else 120)
            if type(warmup) is not int or warmup < 120 or warmup % 120:
                raise ValueError('Warm-up must be a positive multiple of 120: ' + name)
            camera, look = camera_view(row)
            evidence = Path(tempfile.mkdtemp(prefix=name + '-', dir=output / 'evidence'))
            native = factory(binary, evidence, 120)

            def call(command, arguments):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Capture time budget exhausted; resume the private run')
                native.timeout = min(120, remaining)
                return native.call(command, arguments)

            try:
                call('reset', {'seed': row['seed'], 'generator': 'current', 'mods': []})
                call('configure', {'position': camera, 'look': look, 'mode': 'creative', 'flying': True,
                                   'time': SETTINGS['time'], 'weather': SETTINGS['weather'],
                                   'shader': SETTINGS['shader'], 'view_distance': SETTINGS['viewDistance']})
                call('step', {'frames': 1, 'keys': ['F1']})
                for _ in range(warmup // 120):
                    state = call('step', {'frames': 120, 'render': True})
                for _ in range(24):
                    renderer = state['renderer']
                    if renderer['detail_clip_radius_metres'] + 0.01 >= renderer['detail_clip_target_metres']:
                        break
                    state = call('step', {'frames': 120, 'render': True})
                    warmup += 120
                renderer = state['renderer']
                if not renderer['detail_clip_radius_metres'] + 0.01 >= renderer['detail_clip_target_metres']:
                    raise RuntimeError('Detailed terrain did not settle: ' + name)
                call('configure', {'time': SETTINGS['time']})
                result = call('capture_frame', {'name': name + '.png'})
                source = Path(result['path']).resolve()
                if source != evidence / (name + '.png'):
                    raise ValueError('Native frame escaped its evidence directory')
                write(evidence / 'state.json', result['state'])
            finally:
                # Completion cannot be recorded before the owned native process closes.
                process = native.process
                native.close()
                if process is not None:
                    write(evidence / 'exit.json', {'exitCode': process.returncode})
            if process is None or process.returncode != 0:
                raise RuntimeError('Native capture process did not exit successfully: ' + name)
            path = output / 'images' / (name + '.webp')
            with Image.open(source) as image:
                if image.size != (960, 540):
                    raise ValueError('Unexpected native frame dimensions: ' + name)
                image.save(path, 'WEBP', quality=ENCODING['quality'], method=ENCODING['method'])
            entry = {**{key: row[key] for key in LOCATION}, **SETTINGS, **contract['expected'],
                     'file': str(path.relative_to(output)), 'imageSha256': sha(path),
                     'camera': camera, 'look': look, 'warmupFrames': warmup, 'encoding': ENCODING,
                     'renderer': result['state']['renderer'], 'evidence': str(evidence.relative_to(output)),
                     'captured': datetime.now(timezone.utc).isoformat(),
                     'evidenceHashes': {str(p.relative_to(output)): sha(p)
                                        for p in sorted(evidence.iterdir()) if p.is_file()}}
            if row.get('framingNote'):
                entry['framingNote'] = row['framingNote']
            capture_files(output, {name: entry}, rows, contract['expected'], complete=False)
            captures[name] = entry
            write(captures_path, captures)
            print(f'Staged {name} ({len(captures)}/{len(rows)}); visual review pending.', flush=True)
    finally:
        try:
            final_contract, _, _, _ = capture_contract(game, manifest, survey_dir, build_manifest)
            final_contract['minimumWarmupFrames'] = contract['minimumWarmupFrames']
            if final_contract != contract:
                raise ValueError('Capture inputs changed during execution; no completion receipt')
        except Exception as error:
            write(output / 'capture-invalid.json', {'reason': str(error)})
            raise
    capture_files(output, captures, rows, contract['expected'], complete=False)
    if len(captures) == len(rows):
        receipt = output / 'capture-manifest.json'
        if receipt.exists():
            old = read(receipt)
            if (any(old.get(key) != value for key, value in contract.items())
                    or old['capturesSha256'] != sha(captures_path)):
                raise ValueError('Completed capture receipt changed')
            return captures
        write(receipt, {**contract, 'capturesSha256': sha(captures_path),
              'completed': datetime.now(timezone.utc).isoformat(),
              'review': 'Native/displayed visual review and public replacement still required.'})
    return captures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'source-manifest', 'survey-dir', 'build-manifest', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--ids', nargs='+', help='Pilot subset; no full completion receipt')
    parser.add_argument('--resume', action='store_true', help='Reuse verified captures of identical inputs')
    parser.add_argument('--seconds', type=int, default=3600)
    parser.add_argument('--batches', type=int, help='Minimum warm-up in 120-frame batches')
    args = parser.parse_args()
    os.environ.pop('DISPLAY', None)
    os.environ.pop('WAYLAND_DISPLAY', None)
    capture(args.game, args.source_manifest, args.survey_dir, args.build_manifest, args.output_dir,
            args.ids, args.resume, args.seconds, args.batches)


if __name__ == '__main__':
    main()
