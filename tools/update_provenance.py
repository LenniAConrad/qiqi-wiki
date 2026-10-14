#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Prepare a verified private biome bundle; replace the atlas only after review."""
import argparse
from pathlib import Path
import shutil

from biome_capture_evidence import capture_files, inside, read, write
from build_data import build
from capture_biomes import capture_contract
from freeze_media_source import sha
from refresh_survey import private_path
from validate import validate_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG_INPUTS = ('data/descriptions.json', 'data/habitats.json')
PUBLIC_DATA = ('data/survey.json', 'data/viewpoints.json', 'data/captures.json',
               'data/provenance.json', 'data/biomes.json', 'data/biomes.js')


def public_files(captures):
    return [*PUBLIC_DATA, *(capture['file'] for capture in captures.values())]


def prepare(game, manifest, survey_dir, build_manifest, capture_dir, output, root=ROOT):
    game, manifest = game.resolve(), manifest.resolve()
    survey_dir, capture_dir = survey_dir.resolve(), capture_dir.resolve()
    output = private_path(output, game)
    if (output.is_relative_to(survey_dir) or output.is_relative_to(capture_dir)
            or output.is_relative_to(root.resolve())):
        raise ValueError('Publication candidate must be separate from native evidence')
    if (capture_dir / 'capture-invalid.json').exists():
        raise ValueError('Capture run was invalidated by changed inputs')
    contract, _, survey, rows = capture_contract(game, manifest, survey_dir, build_manifest)
    completed = read(capture_dir / 'capture-manifest.json')
    started = read(capture_dir / 'capture-start.json')
    if (any(completed.get(key) != value or started.get(key) != value
            for key, value in contract.items())
            or completed.get('minimumWarmupFrames') != started.get('minimumWarmupFrames')
            or completed['capturesSha256'] != sha(capture_dir / 'captures.json')):
        raise ValueError('Capture completion does not match current inputs')
    captures = read(capture_dir / 'captures.json')
    capture_files(capture_dir, captures, rows, contract['expected'])
    output.mkdir(parents=True, exist_ok=False)
    (output / 'data').mkdir()
    (output / 'images').mkdir()
    for name in CATALOG_INPUTS:
        shutil.copy2(root / name, output / name)
    for name in ('survey.json', 'viewpoints.json'):
        shutil.copy2(survey_dir / name, output / 'data' / name)
    public = {}
    capture_manifest_sha = sha(capture_dir / 'capture-manifest.json')
    for name, entry in captures.items():
        shutil.copy2(inside(capture_dir, entry['file']), output / entry['file'])
        public[name] = {key: value for key, value in entry.items()
                        if key not in ('evidence', 'evidenceHashes')}
        public[name]['captureManifestSha256'] = capture_manifest_sha
        public[name]['nativeStateSha256'] = entry['evidenceHashes'][entry['evidence'] + '/state.json']
    write(output / 'data/captures.json', public)
    source = contract['source']
    snapshot = read(manifest)
    hashes = {row['path']: row['sha256'] for row in snapshot.get('files', [])}
    render_sources = {name: digest for name, digest in hashes.items()
                      if name.startswith('crates/voxelgame-render/src/')
                      or name in ('src/debug_session.rs', 'tools/game_debug.py')}
    if not render_sources:
        raise ValueError('Fresh publication requires complete renderer source evidence')
    expected = contract['expected']
    version = source['generatorVersion']
    survey_record = read(survey_dir / 'survey-manifest.json')
    provenance = {
        'evidence_version': 2, 'generator': f'Current ({version})', 'generator_version': version,
        'source_repository': '../Voxelgame', 'source_commit': source['sourceCommit'],
        'source_tree': snapshot['tree'], 'source_note': snapshot['method'],
        'build_composition': 'Unmodified committed source and assets; offline locked devtools build.',
        'generator_sha256': source['generatorSha256'],
        'related_sources': source['generatorSourcesSha256'], 'renderer_sources': render_sources,
        'date': max(entry['captured'] for entry in captures.values())[:10],
        'binary_sha256': expected['binarySha256'], 'capture_binary_sha256': [expected['binarySha256']],
        'capture_source_manifest_sha256': expected['sourceManifestSha256'],
        'build_manifest_sha256': expected['buildManifestSha256'],
        'capture_manifest_sha256': capture_manifest_sha,
        'survey_manifest_sha256': expected['surveyManifestSha256'],
        'survey_sha256': contract['surveySha256'],
        'viewpoints_sha256': sha(output / 'data/viewpoints.json'),
        'captures_sha256': sha(output / 'data/captures.json'),
        'survey_binary_sha256': survey_record['surveyBinarySha256'],
        'survey_source_sha256': survey_record['surveySourceSha256'],
        'survey_cargo_lock_sha256': survey_record['surveyCargoLockSha256'],
        'survey_generator_sha256': source['generatorSha256'],
        'survey_note': f"{survey['totalSamples']:,} equally weighted surface columns across the "
                       '11 reference seeds. Camera sites are checked separately from frequency sampling.',
        'capture_snapshot_note': f'All {len(captures)} photographs use the recorded generation-{version} '
                                 'build, with no packs enabled or terrain edits.',
        'verification_note': 'Machine evidence checked; visual review and deployment are separate receipts.',
    }
    write(output / 'data/provenance.json', provenance)
    build(output)
    validate_catalog(output, game)
    files = [*public_files(public), *CATALOG_INPUTS]
    receipt = {'schema': 1, 'gameSource': str(game),
               'files': {name: sha(output / name) for name in files},
               'review': 'Review native/displayed images and current habitat text before publication.'}
    write(output / 'publication-manifest.json', receipt)
    return receipt


def publish(bundle, archive, root=ROOT):
    """Archive every replaced file first. The gate must pass before any git land."""
    bundle, archive, root = bundle.resolve(), archive.resolve(), root.resolve()
    receipt = read(bundle / 'publication-manifest.json')
    if (archive.is_relative_to(root) or archive.is_relative_to(bundle)
            or archive.is_relative_to(Path(receipt['gameSource']))):
        raise ValueError('Gallery archive must be in separate private scratch')
    captures = read(bundle / 'data/captures.json')
    files = public_files(captures)
    if receipt.get('schema') != 1 or set(receipt['files']) != set(files) | set(CATALOG_INPUTS):
        raise ValueError('Unexpected publication bundle files')
    for name, digest in receipt['files'].items():
        if sha(inside(bundle, name)) != digest:
            raise ValueError('Changed publication bundle: ' + name)
    for name in CATALOG_INPUTS:
        if sha(root / name) != receipt['files'][name]:
            raise ValueError('Catalog text changed after preparation: ' + name)
    validate_catalog(bundle)
    # Check every destination before creating a recoverable archive or writing.
    previous = {name: sha(inside(root, name)) for name in files}
    archive.mkdir(parents=True, exist_ok=False)
    for name in files:
        destination = archive / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, destination)
        if sha(destination) != previous[name]:
            raise ValueError('Gallery changed while archiving: ' + name)
    write(archive / 'archive-manifest.json', {'files': previous, 'replacement': receipt['files']})
    for name in files:
        if sha(root / name) != previous[name]:
            raise ValueError('Gallery changed before replacement: ' + name)
    for name in files:
        destination = root / name
        temporary = destination.with_suffix(destination.suffix + '.pending')
        shutil.copy2(bundle / name, temporary)
        temporary.replace(destination)
    validate_catalog(root)
    print('Biome data replaced in this worktree; rebuild previews/pages, review and run the normal gate.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'source-manifest', 'survey-dir', 'build-manifest', 'capture-dir', 'output-dir'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--publish', type=Path, help='Reviewed private publication bundle')
    parser.add_argument('--archive-dir', type=Path, help='New private backup directory, required to publish')
    args = parser.parse_args()
    if args.publish:
        if not args.archive_dir:
            parser.error('--publish requires --archive-dir')
        publish(args.publish, args.archive_dir)
    else:
        required = [args.game, args.source_manifest, args.survey_dir, args.build_manifest,
                    args.capture_dir, args.output_dir]
        if not all(required):
            parser.error('Preparation requires game, source-manifest, survey-dir, build-manifest, capture-dir, output-dir')
        prepare(*required)
        print('Private publication bundle verified; public atlas unchanged, visual review pending.')


if __name__ == '__main__':
    main()
