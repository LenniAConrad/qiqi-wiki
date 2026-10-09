#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Prepare survey-bound camera refinements without retaining stale locations."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCATION_KEYS = {'seed', 'x', 'z', 'height', 'water', 'camera', 'look', 'framingNote'}
MARINE = {'OceanFloor', 'DeepKelpForest', 'CoralShallows', 'SeagrassLagoon'}


def build_viewpoints(survey, previous, survey_sha):
    """Retain timing preferences and bind every position override to its survey."""
    result = {}
    for name, entry in previous.items():
        if LOCATION_KEYS.intersection(entry) and entry.get('surveySha256') != survey_sha:
            entry = {key: value for key, value in entry.items()
                     if key not in LOCATION_KEYS and key != 'surveySha256'}
        if entry:
            result[name] = entry.copy()
    for row in survey['biomes']:
        if row['id'] not in MARINE or row['water'] - row['height'] < 2.5:
            continue
        if LOCATION_KEYS.intersection(result.get(row['id'], {})):
            continue
        # The eye remains below water while the feet clear the sampled bed.
        camera = [row['x'] - 8, max(row['height'] + 0.4, row['water'] - 2.6), row['z'] - 10]
        look = [math.degrees(math.atan2(8, 10)),
                math.degrees(math.atan2(row['height'] + 1 - camera[1] - 1.62,
                                       math.hypot(8, 10)))]
        result.setdefault(row['id'], {}).update(
            camera=camera, look=look, surveySha256=survey_sha)
    return result


def main():
    survey_path = ROOT / 'data/survey.json'
    path = ROOT / 'data/viewpoints.json'
    survey = json.loads(survey_path.read_text())
    previous = json.loads(path.read_text()) if path.exists() else {}
    result = build_viewpoints(survey, previous, hashlib.sha256(survey_path.read_bytes()).hexdigest())
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Prepared {len(result)} survey-bound camera/timing refinements')


if __name__ == '__main__':
    main()
