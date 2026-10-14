#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build one frozen devtools executable in private scratch and bind its receipt."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess

from biome_capture_evidence import write
from freeze_media_source import sha
from refresh_survey import private_path, verified_source


def build(game, manifest, output, target=None, jobs=2, seconds=3600):
    game, manifest = game.resolve(), manifest.resolve()
    output = private_path(output, game)
    target = private_path(target, game) if target else output / 'target'
    if jobs not in range(1, 5) or seconds < 1:
        raise ValueError('Use 1–4 build jobs and a positive timeout')
    source = verified_source(game, manifest)
    manifest_sha = sha(manifest)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'tmp').mkdir()
    command = ['cargo', 'build', '--release', '--offline', '--locked', '--features', 'devtools',
               '--manifest-path', str(game / 'Cargo.toml'), '--bin', 'voxelgame']
    with (output / 'build.log').open('w') as log:
        subprocess.run(['timeout', '--kill-after=30s', str(seconds), 'nice', '-n', '10', *command],
                       cwd=output, env={**os.environ, 'CARGO_BUILD_JOBS': str(jobs),
                                        'CARGO_TARGET_DIR': str(target), 'TMPDIR': str(output / 'tmp')},
                       stdout=log, stderr=log, check=True)
    if sha(manifest) != manifest_sha or verified_source(game, manifest) != source:
        raise ValueError('Frozen source changed during capture build')
    binary = target / 'release/voxelgame'
    receipt = {'schema': 1, 'source': source, 'sourceManifestSha256': manifest_sha,
               'binary': str(binary), 'binarySha256': sha(binary),
               'cargoLockSha256': sha(game / 'Cargo.lock'),
               'debugAdapterSha256': sha(game / 'tools/game_debug.py'),
               'command': command, 'buildJobs': jobs, 'exitCode': 0,
               'completed': datetime.now(timezone.utc).isoformat()}
    write(output / 'build-manifest.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--target-dir', type=Path)
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=2)
    parser.add_argument('--seconds', type=int, default=3600)
    args = parser.parse_args()
    build(args.game, args.source_manifest, args.output_dir, args.target_dir, args.jobs, args.seconds)
    print('Completed private capture build; no photographs or public data changed.')


if __name__ == '__main__':
    main()
