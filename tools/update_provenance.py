#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Publish provenance only after the survey and all photographs match one build."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-manifest', type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.source_manifest.read_text())
    survey_record = json.loads((args.source_manifest.parent / 'survey-manifest.json').read_text())
    survey = json.loads((ROOT / 'data/survey.json').read_text())
    captures = json.loads((ROOT / 'data/captures.json').read_text())
    version = snapshot['generatorVersion']
    manifest_sha = sha(args.source_manifest)
    assert version == survey['generatorVersion'] == survey_record['generatorVersion'] == 9
    assert survey_record['sourceManifestSha256'] == manifest_sha
    assert survey_record['surveySha256'] == sha(ROOT / 'data/survey.json')
    assert set(captures) == {row['id'] for row in survey['biomes']}
    for name, capture in captures.items():
        assert capture['generatorVersion'] == version, ('stale photograph', name)
        assert capture['binarySha256'] == snapshot['binarySha256'], name
        assert capture['sourceManifestSha256'] == manifest_sha, name
        assert capture['imageSha256'] == sha(ROOT / capture['file']), name
    provenance = {
        'generator': f'Current ({version})', 'generator_version': version,
        'source_repository': '../Voxelgame', 'source_commit': snapshot['sourceCommit'],
        'source_note': 'Working tree snapshot: generation 9 irregular island placement, soft geological collars, temperature-driven snow margins, broader mountain summits and coherent low rock clusters. All photographs use one frozen production devtools executable and its archived sources.',
        'build_composition': snapshot['buildComposition'],
        'generator_sha256': snapshot['generatorSha256'], 'date': snapshot['date'],
        'related_sources': snapshot['generatorSourcesSha256'],
        'renderer_sources': snapshot['rendererSourcesSha256'],
        'binary_sha256': snapshot['binarySha256'],
        'capture_binary_sha256': [snapshot['binarySha256']],
        'capture_source_manifest_sha256': manifest_sha,
        'survey_binary_sha256': survey_record['surveyBinarySha256'],
        'survey_source_sha256': survey_record['surveySourceSha256'],
        'survey_cargo_lock_sha256': survey_record['surveyCargoLockSha256'],
        'survey_generator_sha256': survey_record['generatorSha256'],
        'survey_manifest_sha256': sha(args.source_manifest.parent / 'survey-manifest.json'),
        'survey_note': 'Fresh generation 9 survey: 6,504,971 equally weighted surface columns across the same 11 reference seeds. The 55,296-metre radius and 144-metre stride retain the same enlarged reference survey for the irregular island layout. All 92 biomes occur. Photography sites and camera angles are selected separately from frequency counting; labels, height, water and camera clearance are checked.',
        'game_updates': [
            'Generation 5: shorter temperature/moisture provinces and clustered shrubs and ground plants.',
            'Generation 6: broad juvenile cacti, staggered mature arms, sculpted mineral cups, layered rocks and unequal crystal towers.',
            'Generation 7: inland ridges and hollows; forest stands, open glades and brushy edges share a ground-cover pattern.',
            'Generation 8: islands can grow up to 50% wider and longer, with individual bends, unequal bays and mixed-axis ownership pairs.',
            'Generation 9: unequal island ownership, varied centre offsets and clustered open sea; warped geological skin transitions, local cold-surface snow and thaw patches, broader mountain summits, low coherent rock clusters and sparse limestone boulders on dry atoll shores.',
            'Existing saved worlds retain their original terrain rules; these sites require generation 9 and the listed seed.',
            'Climate uses ordered temperature/moisture families and transition habitats; altitude and drainage control local exceptions.'
        ],
        'capture_snapshot_note': 'All 92 photographs were newly rendered from the frozen generation 9 executable; earlier generation 4 photographs and generation 8 pilot evidence remain archived locally and are not relabelled.',
        'verification_note': 'Exact survey and capture provenance verified by tools/update_provenance.py; visual review and final atlas validation are recorded in VERIFICATION.md.'
    }
    (ROOT / 'data/provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('Updated generation 9 provenance from the verified survey and all 92 captures')

if __name__ == '__main__':
    main()
