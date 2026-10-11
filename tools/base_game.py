# SPDX-License-Identifier: GPL-3.0-only
"""Publication scope derived from the dd29d91 status/area/evidence audit."""
from copy import deepcopy

# These non-optional-status rows describe the pack menu or requested external
# content. Their existing evidence/backlog fields establish that boundary.
EXCLUDED_FEATURES = {'mods-page-enable-packs', 'resource-packs', 'dimension-travel'}


def public_ledger(ledger):
    """Filter before rendering; no unfiltered copy belongs in the public repo."""
    result = deepcopy(ledger)
    result['features'] = [f for f in result['features']
                          if f['status'] != 'optional-pack' and f['area'] != 'packs'
                          and f['id'] not in EXCLUDED_FEATURES and not f.get('pack')]
    ids = {f['id'] for f in result['features']}
    result['statuses'] = [s for s in result['statuses'] if s['key'] != 'optional-pack']
    result['areas'] = [a for a in result['areas'] if any(f['area'] == a['key'] for f in result['features'])]
    # Drop pack-specific writing tasks entirely, including mixed gaps that used
    # per-world settings as a cross-reference. Keep ranks stable for guide IDs.
    result['guideGaps'] = [g for g in result['guideGaps'] if not any(
        term in g['title'].lower() for term in ('content packs', 'iron skies'))]
    for gap in result['guideGaps']:
        gap['covers'] = [fid for fid in gap['covers'] if fid in ids]
    result['guideGaps'] = [g for g in result['guideGaps'] if g['covers']]
    return result
