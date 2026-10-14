#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Shared checks for private biome evidence and the published atlas."""
import json
import math
from pathlib import Path

from freeze_media_source import sha
from prepare_viewpoints import LOCATION_KEYS
from refresh_survey import validate_survey, verified_source

ENCODING = {'format': 'WebP', 'quality': 94, 'method': 6}
SETTINGS = {'time': 0.43, 'weather': 'clear', 'shader': 'fast', 'viewDistance': 64}
LOCATION = ('seed', 'x', 'z', 'height', 'water')


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def inside(root, name):
    """Evidence paths must name ordinary files within their own evidence tree."""
    path = root / name
    if (Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve()) or not path.is_file()):
        raise ValueError('Invalid evidence path: ' + name)
    return path


def camera_view(row):
    camera = row['camera'][:]
    target = [row['x'], max(row['height'] + 3, row['water']), row['z']]
    if ('look' not in row and row['id'] in
            {'OceanFloor', 'DeepKelpForest', 'SeagrassLagoon', 'CoralShallows'}
            and row['water'] - row['height'] > 8):
        camera = [row['x'] - 10, row['height'] + 5, row['z'] - 14]
        target = [row['x'], row['height'] + 1.5, row['z']]
    dx, dz = target[0] - camera[0], target[2] - camera[2]
    look = row.get('look', [math.degrees(math.atan2(dx, dz)), math.degrees(
        math.atan2(target[1] - camera[1] - 1.62, math.hypot(dx, dz)))])
    return camera, look


def survey_inputs(game, manifest, directory):
    """Accept only an intact completed survey, including its checked camera sites."""
    source = verified_source(game, manifest)
    record = read(directory / 'survey-manifest.json')
    if (record['sourceManifestSha256'] != sha(manifest)
            or any(record.get(key) != value for key, value in source.items())):
        raise ValueError('Survey uses another source snapshot')
    files = {'survey.json': 'surveySha256', 'viewpoints.json': 'viewpointsSha256',
             'survey-sites.csv': 'sitesSha256', 'survey-sites-checked.json': 'checkedSitesSha256',
             'survey-project/main.rs': 'surveySourceSha256',
             'survey-project/check_sites.rs': 'siteCheckerSourceSha256',
             'survey-project/Cargo.toml': 'surveyCargoManifestSha256',
             'survey-project/Cargo.lock': 'surveyCargoLockSha256'}
    for name, key in files.items():
        if sha(inside(directory, name)) != record[key]:
            raise ValueError('Changed survey evidence: ' + name)
    survey = read(directory / 'survey.json')
    validate_survey(survey, source['generatorVersion'])
    overrides = read(directory / 'viewpoints.json')
    ids = {row['id'] for row in survey['biomes']}
    if set(overrides) - ids:
        raise ValueError('Unknown viewpoint biome')
    for entry in overrides.values():
        if LOCATION_KEYS.intersection(entry) and entry.get('surveySha256') != record['surveySha256']:
            raise ValueError('Stale viewpoint')
    rows = [{**row, **overrides.get(row['id'], {})} for row in survey['biomes']]
    checked = read(directory / 'survey-sites-checked.json')
    if set(checked) != ids:
        raise ValueError('Incomplete checked camera sites')
    lines = []
    for row in rows:
        camera, _ = camera_view(row)
        lines.append(f"{row['id']},{row['seed']},{row['x']},{row['z']},{camera[0]},{camera[2]}\n")
        actual = checked[row['id']]
        if (row['height'] != actual['height'] or row['water'] != actual['water']
                or not camera[1] > actual['cameraGround'] + 0.1):
            raise ValueError('Stale or buried camera: ' + row['id'])
    if ''.join(lines) != (directory / 'survey-sites.csv').read_text():
        raise ValueError('Capture cameras differ from checked sites')
    return source, record, survey, rows


def build_input(game, manifest, receipt_path):
    source = verified_source(game, manifest)
    receipt = read(receipt_path)
    binary = Path(receipt['binary'])
    if (receipt.get('schema') != 1 or receipt.get('exitCode') != 0
            or receipt['sourceManifestSha256'] != sha(manifest)
            or receipt['source'] != source or receipt['binarySha256'] != sha(binary)
            or receipt['cargoLockSha256'] != sha(game / 'Cargo.lock')
            or receipt['debugAdapterSha256'] != sha(game / 'tools/game_debug.py')):
        raise ValueError('Capture build does not match the frozen source or executable')
    return receipt, binary


def capture_metadata(capture, row, expected):
    camera, look = camera_view(row)
    if (any(capture.get(key) != row[key] for key in LOCATION)
            or capture.get('camera') != camera or capture.get('look') != look
            or capture.get('framingNote') != row.get('framingNote')
            or capture.get('encoding') != ENCODING
            or any(capture.get(key) != value for key, value in {**SETTINGS, **expected}.items())
            or capture.get('warmupFrames', 0) < row.get('warmupFrames', 600)):
        raise ValueError('Stale capture metadata: ' + row['id'])
    renderer = capture['renderer']
    if not renderer['detail_clip_radius_metres'] + 0.01 >= renderer['detail_clip_target_metres']:
        raise ValueError('Terrain still streaming: ' + row['id'])


def capture_files(directory, captures, rows, expected, complete=True):
    """Check resumable private captures; fixtures must never be public receipts."""
    by_id = {row['id']: row for row in rows}
    if set(captures) - set(by_id) or (complete and set(captures) != set(by_id)):
        raise ValueError('Incomplete or unexpected biome captures')
    for name, capture in captures.items():
        capture_metadata(capture, by_id[name], expected)
        if capture['file'] != f'images/{name}.webp':
            raise ValueError('Unexpected image path: ' + name)
        files = {capture['file']: capture['imageSha256'], **capture['evidenceHashes']}
        for filename, digest in files.items():
            if sha(inside(directory, filename)) != digest:
                raise ValueError('Changed capture evidence: ' + filename)
        evidence = capture['evidence']
        required = {f'{evidence}/{filename}' for filename in
                    (f'{name}.png', 'state.json', 'metadata.json', 'processes.jsonl', 'replay.json', 'exit.json')}
        if not required.issubset(capture['evidenceHashes']):
            raise ValueError('Missing native capture evidence: ' + name)
        state = read(inside(directory, evidence + '/state.json'))
        if (read(inside(directory, evidence + '/exit.json'))['exitCode'] != 0
                or state['generator_version'] != expected['generatorVersion']
                or state['seed'] != capture['seed'] or state['save_writes'] is not False
                or state['mods'] != [] or state['world']['edited_voxels'] != 0
                or state['renderer'] != capture['renderer']):
            raise ValueError('Capture is not an unedited base-game world: ' + name)
        processes = [json.loads(line) for line in
                     inside(directory, evidence + '/processes.jsonl').read_text().splitlines()]
        if (not processes or any(p['binary_sha256'] != expected['binarySha256'] for p in processes)
                or read(inside(directory, evidence + '/metadata.json'))['binary_sha256']
                != expected['binarySha256']):
            raise ValueError('Native process used another executable: ' + name)
        replay = read(inside(directory, evidence + '/replay.json'))
        commands = replay['commands']
        prefix = [
            {'command': 'reset', 'seed': capture['seed'], 'generator': 'current', 'mods': []},
            {'command': 'configure', 'position': capture['camera'], 'look': capture['look'],
             'mode': 'creative', 'flying': True, 'time': SETTINGS['time'],
             'weather': SETTINGS['weather'], 'shader': SETTINGS['shader'],
             'view_distance': SETTINGS['viewDistance']},
            {'command': 'step', 'frames': 1, 'keys': ['F1']},
        ]
        suffix = [{'command': 'configure', 'time': SETTINGS['time']},
                  {'command': 'capture_frame', 'name': name + '.png'}]
        steps = commands[len(prefix):-len(suffix)]
        if (replay.get('version') != 1 or commands[:len(prefix)] != prefix
                or commands[-len(suffix):] != suffix or not steps
                or any(step != {'command': 'step', 'frames': 120, 'render': True} for step in steps)
                or len(steps) * 120 != capture['warmupFrames']):
            raise ValueError('Native replay differs from capture settings: ' + name)
