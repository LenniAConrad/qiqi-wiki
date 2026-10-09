#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build and run the survey with Cargo against a verified frozen game source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import time
from prepare_viewpoints import build_viewpoints

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=ROOT.parent / 'Voxelgame')
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--target-dir', type=Path)
    args = parser.parse_args()
    args.game = args.game.resolve()
    args.source_manifest = args.source_manifest.resolve()
    snapshot = json.loads(args.source_manifest.read_text())
    sources = {**{name: value for name, value in snapshot['sourceFilesSha256'].items()
                  if name.startswith('crates/voxelgame-core/')},
               **snapshot['generatorSourcesSha256'],
               'crates/voxelgame-core/src/world/generator.rs': snapshot['generatorSha256']}
    def verify_source():
        for name, expected in sources.items():
            assert sha(args.game / name) == expected, ('game source changed', name)
    verify_source()
    evidence = args.source_manifest.parent
    # A copied source tree is an actual dependency, not just a hash reference.
    # Building the checked-in manifest would silently use the live sibling
    # checkout while other sessions are changing it.
    project = evidence / 'survey-project'
    project.mkdir(parents=True, exist_ok=True)
    source = project / 'main.rs'
    shutil.copy2(ROOT / 'tools/survey/src/main.rs', source)
    site_checker = project / 'check_sites.rs'
    shutil.copy2(ROOT / 'tools/survey/src/bin/check_sites.rs', site_checker)
    if not (project / 'Cargo.lock').exists():
        shutil.copy2(args.game / 'Cargo.lock', project / 'Cargo.lock')
    manifest = project / 'Cargo.toml'
    manifest.write_text('\n'.join([
        '# SPDX-License-Identifier: GPL-3.0-only',
        '[package]', 'name = "qiqi-biome-survey-snapshot"', 'version = "0.1.0"',
        'edition = "2021"', 'rust-version = "1.75"', '[workspace]', '[[bin]]',
        'name = "qiqi-biome-survey"',
        'path = "main.rs"',
        '[[bin]]', 'name = "check_sites"', 'path = "check_sites.rs"',
        '[dependencies]', 'voxelgame-core = { path = ' +
        json.dumps(str(args.game.resolve() / 'crates/voxelgame-core')) + ' }', '',
    ]))
    target = args.target_dir.resolve() if args.target_dir else evidence / 'sampling-target'
    pending = evidence / 'survey-pending.json'
    log = evidence / 'survey.log'
    began = time.monotonic()
    with log.open('w') as stream:
        subprocess.run(['cargo', 'run', '--release', '--manifest-path',
                        str(manifest), '--bin', 'qiqi-biome-survey', '--', str(pending)],
                       cwd=ROOT, env={**os.environ, 'CARGO_TARGET_DIR': str(target)},
                       stdout=stream, stderr=stream, check=True)
    verify_source()
    survey = json.loads(pending.read_text())
    assert survey['generatorVersion'] == snapshot['generatorVersion']
    assert len(survey['biomes']) == 92 and all(row['count'] > 0 for row in survey['biomes'])
    assert survey['totalSamples'] == sum(row['count'] for row in survey['biomes']) == 6_504_971
    assert len(survey['seeds']) == 11
    survey_sha = sha(pending)
    viewpoints_path = ROOT / 'data/viewpoints.json'
    previous = json.loads(viewpoints_path.read_text()) if viewpoints_path.exists() else {}
    viewpoints = build_viewpoints(survey, previous, survey_sha)
    sites = evidence / 'survey-sites.csv'
    locations = [{**row, **viewpoints.get(row['id'], {})} for row in survey['biomes']]
    sites.write_text(''.join(f"{row['id']},{row['seed']},{row['x']},{row['z']},"
                             f"{row['camera'][0]},{row['camera'][2]}\n" for row in locations))
    checked_path = evidence / 'survey-sites-checked.json'
    with log.open('a') as stream:
        subprocess.run(['cargo', 'run', '--release', '--manifest-path', str(manifest),
                        '--bin', 'check_sites', '--', str(sites), str(checked_path)],
                       cwd=ROOT, env={**os.environ, 'CARGO_TARGET_DIR': str(target)},
                       stdout=stream, stderr=stream, check=True)
    verify_source()
    checked = json.loads(checked_path.read_text())
    for row in locations:
        actual = checked[row['id']]
        assert row['height'] == actual['height'] and row['water'] == actual['water'], row['id']
        assert row['camera'][1] > actual['cameraGround'] + 0.1, ('buried camera', row['id'])
    record = {
        'generatorVersion': survey['generatorVersion'],
        'sourceManifestSha256': sha(args.source_manifest),
        'surveyBinarySha256': sha(target / 'release/qiqi-biome-survey'),
        'surveySourceSha256': sha(source),
        'surveyCargoLockSha256': sha(project / 'Cargo.lock'),
        'surveySha256': survey_sha,
        'siteCheckerSourceSha256': sha(site_checker),
        'checkedSitesSha256': sha(checked_path),
        'generatorSha256': snapshot['generatorSha256'],
        'generatorSourcesSha256': snapshot['generatorSourcesSha256'],
        'totalSamples': survey['totalSamples'],
        'elapsedSeconds': round(time.monotonic() - began, 3),
        'log': os.path.relpath(log, ROOT),
    }
    (evidence / 'survey-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    pending.replace(ROOT / 'data/survey.json')
    viewpoints_path.write_text(json.dumps(viewpoints, indent=2) + '\n')
    print(f"Surveyed 92 biomes in {record['elapsedSeconds']:.1f}s; {survey['totalSamples']:,} samples")

if __name__ == '__main__':
    main()
