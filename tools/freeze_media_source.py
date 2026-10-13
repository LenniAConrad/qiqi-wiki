#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Export committed game code and assets to private capture scratch, without checkout changes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(game, *args):
    return subprocess.check_output(['git', '-C', str(game), *args], text=True).strip()


def freeze(game, revision, output):
    """Archive an exact commit, including binary assets and Cargo.lock."""
    game, output = game.resolve(), output.resolve()
    if output.is_relative_to(game):
        raise ValueError('Capture scratch must be outside the game checkout')
    commit = git(game, 'rev-parse', '--verify', revision + '^{commit}')
    tree = git(game, 'rev-parse', commit + '^{tree}')
    output.mkdir(parents=True, exist_ok=False)
    archive = output / 'source.tar'
    subprocess.run(['git', '-C', str(game), 'archive', '--format=tar',
                    '--output=' + str(archive), commit], check=True)
    source = output / 'source'
    source.mkdir()
    with tarfile.open(archive) as bundle:
        bundle.extractall(source, filter='data')
    files = []
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('Capture snapshots require regular files: ' + str(path))
        if path.is_file():
            files.append({'path': str(path.relative_to(source)),
                          'bytes': path.stat().st_size, 'sha256': sha(path)})
    # Missing export-ignored files or submodule contents must not be called a full snapshot.
    tracked = set(git(game, 'ls-tree', '-r', '--name-only', commit).splitlines())
    if tracked != {row['path'] for row in files}:
        raise ValueError('Archive differs from the full tracked tree; inspect export rules/submodules')
    manifest = {'commit': commit, 'tree': tree, 'archiveSha256': sha(archive),
                'created': datetime.now(timezone.utc).isoformat(),
                'method': 'Unmodified git archive; complete tracked source, Cargo.lock and assets.',
                'files': files}
    (output / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def verify_snapshot(game, manifest_path):
    """Check every frozen input before using its commit as image provenance."""
    game = game.resolve()
    manifest = json.loads(manifest_path.read_text())
    paths = set()
    for row in manifest['files']:
        name = row['path']
        path = game / name
        if name in paths or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Invalid or duplicate snapshot path: ' + name)
        paths.add(name)
        if (not path.resolve().is_relative_to(game) or path.is_symlink()
                or not path.is_file() or path.stat().st_size != row['bytes']
                or sha(path) != row['sha256']):
            raise ValueError('Changed or missing snapshot input: ' + name)
    if not paths or 'Cargo.lock' not in paths:
        raise ValueError('A full media snapshot must include Cargo.lock')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('commit')
    parser.add_argument('output', type=Path, help='New private scratch directory, outside the game checkout')
    args = parser.parse_args()
    manifest = freeze(args.game, args.commit, args.output)
    print(f'Frozen {manifest["commit"]}: {len(manifest["files"])} files; no checkout modified.')


if __name__ == '__main__':
    main()
