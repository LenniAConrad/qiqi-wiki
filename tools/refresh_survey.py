#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Survey frozen game source into private scratch, without publishing atlas data."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from freeze_media_source import sha, verify_snapshot
from prepare_viewpoints import build_viewpoints

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = 'crates/voxelgame-core/src/world/generator.rs'
SEEDS = [812, 7, 91, 614, 913, 4242, 9001, 12039, 14, 2, 33]
RADIUS = 55_296
STRIDE = 144
TOTAL = len(SEEDS) * (RADIUS * 2 // STRIDE + 1) ** 2


def verified_source(game, manifest_path):
    """Read full media receipts or archived manifests without changing either."""
    snapshot = json.loads(manifest_path.read_text())
    if 'files' in snapshot:
        verify_snapshot(game, manifest_path)
        sources = {row['path']: row['sha256'] for row in snapshot['files']}
        # An unrecorded module can affect a build even when all recorded files match.
        actual = {str(p.relative_to(game)) for p in game.rglob('*') if p.is_file()}
        if actual != set(sources):
            differences = sorted(actual.symmetric_difference(sources))
            raise ValueError('Frozen source contains unrecorded or missing files: '
                             + ', '.join(differences[:10]))
        text = (game / GENERATOR).read_text()
        enum = re.search(r'pub enum GeneratorVersion\s*\{(.*?)\n\}', text, re.S)
        current = re.findall(r'^\s*Current\s*=\s*(\d+)\s*,', enum[1], re.M) if enum else []
        if len(current) != 1:
            raise ValueError('Review the changed GeneratorVersion::Current declaration')
        version = int(current[0])
        related = {name: value for name, value in sources.items()
                   if name.startswith('crates/voxelgame-core/src/world/generator/')
                   or name == 'crates/voxelgame-core/src/world/block.rs'}
        return {'generatorVersion': version, 'generatorSha256': sources[GENERATOR],
                'generatorSourcesSha256': related, 'sourceCommit': snapshot['commit']}

    # Preserve the original generation-9 snapshot's format and exact hashes.
    sources = {**snapshot['sourceFilesSha256'], **snapshot['generatorSourcesSha256'],
               GENERATOR: snapshot['generatorSha256']}
    for name, expected in sources.items():
        path = game / name
        if (Path(name).is_absolute() or '..' in Path(name).parts
                or not path.resolve().is_relative_to(game) or path.is_symlink()
                or not path.is_file() or sha(path) != expected):
            raise ValueError('Changed or missing snapshot input: ' + name)
    return {key: snapshot[key] for key in
            ('generatorVersion', 'generatorSha256', 'generatorSourcesSha256', 'sourceCommit')}


def validate_survey(survey, version):
    """Keep the existing sampling contract; changing it needs a separate review."""
    rows = survey['biomes']
    if (survey['generatorVersion'] != version or survey['seeds'] != SEEDS
            or survey['radiusMetres'] != RADIUS or survey['strideMetres'] != STRIDE
            or survey['totalSamples'] != TOTAL or len(rows) != 92
            or len({row['id'] for row in rows}) != 92
            or sum(row['count'] for row in rows) != TOTAL
            or any(type(row['count']) is not int or row['count'] <= 0 for row in rows)):
        raise ValueError('Survey does not match the generator and reference sampling contract')


def private_path(path, game):
    path = path.resolve()
    if path.is_relative_to(game) or path.is_relative_to(ROOT):
        raise ValueError('Survey outputs and build targets must be outside game and wiki source')
    return path


def refresh(game, manifest_path, output, target=None, viewpoints=None, jobs=2, seconds=3600):
    """Stage a complete survey and site check; a failure leaves only private evidence."""
    game, manifest_path = game.resolve(), manifest_path.resolve()
    output = private_path(output, game)
    target = private_path(target, game) if target else output / 'target'
    if jobs not in range(1, 5) or seconds < 1:
        raise ValueError('Use 1–4 build jobs and a positive timeout')
    snapshot = verified_source(game, manifest_path)
    manifest_sha = sha(manifest_path)
    previous_path = viewpoints if viewpoints is not None else ROOT / 'data/viewpoints.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    previous_sha = sha(previous_path) if previous_path.exists() else None
    # No overwrite/resume of a partially reviewed survey; its logs remain recoverable.
    output.mkdir(parents=True, exist_ok=False)
    temporary = output / 'tmp'
    temporary.mkdir()
    project = output / 'survey-project'
    project.mkdir()
    copied = {}
    for source_name, dest_name in [('tools/survey/src/main.rs', 'main.rs'),
                                   ('tools/survey/src/bin/check_sites.rs', 'check_sites.rs')]:
        path = project / dest_name
        shutil.copy2(ROOT / source_name, path)
        copied[dest_name] = sha(path)
    shutil.copy2(game / 'Cargo.lock', project / 'Cargo.lock')
    cargo_manifest = project / 'Cargo.toml'
    cargo_manifest.write_text('\n'.join([
        '# SPDX-License-Identifier: GPL-3.0-only',
        '[package]', 'name = "qiqi-biome-survey-snapshot"', 'version = "0.1.0"',
        'edition = "2021"', '[workspace]', '[[bin]]', 'name = "qiqi-biome-survey"',
        'path = "main.rs"', '[[bin]]', 'name = "check_sites"', 'path = "check_sites.rs"',
        '[dependencies]', 'voxelgame-core = { path = ' +
        json.dumps(str(game / 'crates/voxelgame-core')) + ' }', '',
    ]))
    copied['Cargo.toml'] = sha(cargo_manifest)
    pending = output / 'survey-pending.json'
    log = output / 'survey.log'
    began = time.monotonic()
    commands = []

    def verify_inputs():
        if sha(manifest_path) != manifest_sha or verified_source(game, manifest_path) != snapshot:
            raise ValueError('Source manifest changed during the survey')
        for name, expected in copied.items():
            if sha(project / name) != expected:
                raise ValueError('Survey tool changed during execution: ' + name)

    def run(binary, *args):
        remaining = seconds - (time.monotonic() - began)
        if remaining <= 0:
            raise TimeoutError('Survey and site-check time budget exhausted')
        command = ['cargo', 'run', '--release', '--offline', '--manifest-path',
                   str(cargo_manifest), '--bin', binary, '--', *map(str, args)]
        commands.append(command)
        # GNU timeout bounds the complete process group, including Cargo's child.
        with log.open('a') as stream:
            subprocess.run(['timeout', '--kill-after=30s', f'{remaining:.3f}s',
                            'nice', '-n', '10', *command], cwd=output,
                           env={**os.environ, 'CARGO_TARGET_DIR': str(target),
                                'CARGO_BUILD_JOBS': str(jobs), 'TMPDIR': str(temporary)},
                           stdout=stream, stderr=stream, check=True)
        verify_inputs()

    run('qiqi-biome-survey', pending)
    survey_binary_sha = sha(target / 'release/qiqi-biome-survey')
    survey_lock_sha = sha(project / 'Cargo.lock')
    survey = json.loads(pending.read_text())
    validate_survey(survey, snapshot['generatorVersion'])
    survey_sha = sha(pending)
    prepared = build_viewpoints(survey, previous, survey_sha)
    sites = output / 'survey-sites.csv'
    locations = [{**row, **prepared.get(row['id'], {})} for row in survey['biomes']]
    sites.write_text(''.join(f"{row['id']},{row['seed']},{row['x']},{row['z']},"
                            f"{row['camera'][0]},{row['camera'][2]}\n" for row in locations))
    sites_sha = sha(sites)
    checked_path = output / 'survey-sites-checked.json'
    run('check_sites', sites, checked_path)
    if (sha(target / 'release/qiqi-biome-survey') != survey_binary_sha
            or sha(project / 'Cargo.lock') != survey_lock_sha):
        raise ValueError('Survey executable or resolved dependencies changed during site verification')
    if sha(pending) != survey_sha or sha(sites) != sites_sha:
        raise ValueError('Survey or camera sites changed during site verification')
    checked = json.loads(checked_path.read_text())
    if set(checked) != {row['id'] for row in locations}:
        raise ValueError('Incomplete or unexpected checked camera sites')
    for row in locations:
        actual = checked[row['id']]
        if (row['height'] != actual['height'] or row['water'] != actual['water']
                or not row['camera'][1] > actual['cameraGround'] + 0.1):
            raise ValueError('Stale or buried camera site: ' + row['id'])
    viewpoints_path = output / 'viewpoints.json'
    viewpoints_path.write_text(json.dumps(prepared, indent=2) + '\n')
    pending.rename(output / 'survey.json')
    record = {
        **snapshot, 'sourceManifestSha256': manifest_sha,
        'surveyBinarySha256': survey_binary_sha,
        'surveySourceSha256': copied['main.rs'],
        'surveyCargoLockSha256': survey_lock_sha,
        'surveyCargoManifestSha256': copied['Cargo.toml'], 'surveySha256': survey_sha,
        'siteCheckerSourceSha256': copied['check_sites.rs'],
        'siteCheckerBinarySha256': sha(target / 'release/check_sites'),
        'checkedSitesSha256': sha(checked_path), 'sitesSha256': sites_sha,
        'viewpointsSha256': sha(viewpoints_path), 'previousViewpointsSha256': previous_sha,
        'totalSamples': survey['totalSamples'], 'buildJobs': jobs, 'commands': commands,
        'elapsedSeconds': round(time.monotonic() - began, 3), 'log': 'survey.log',
        'publication': 'Private survey and camera checks only; no photographs or public data updated.',
    }
    # This is the completion marker. Partial files/logs alone never certify a run.
    receipt = output / 'survey-manifest.json'
    receipt.with_suffix('.tmp').write_text(json.dumps(record, indent=2) + '\n')
    receipt.with_suffix('.tmp').rename(receipt)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True, help='New private directory')
    parser.add_argument('--target-dir', type=Path)
    parser.add_argument('--viewpoints', type=Path, help='Previous timing/camera preferences to review')
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=2)
    parser.add_argument('--seconds', type=int, default=3600, help='Total native command time budget')
    args = parser.parse_args()
    record = refresh(args.game, args.source_manifest, args.output_dir, args.target_dir,
                     args.viewpoints, args.jobs, args.seconds)
    print(f"Staged 92 biomes / {record['totalSamples']:,} samples in {args.output_dir}; "
          'public atlas unchanged. Review sites and capture fresh photographs before publication.')


if __name__ == '__main__':
    main()
