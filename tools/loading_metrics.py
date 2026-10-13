# SPDX-License-Identifier: GPL-3.0-only
"""Keep redacted browser timing sizes distinct from complete transfer totals."""


def body_totals(navigation, resources):
    entries = navigation + resources
    missing = [entry['url'] for entry in entries if not entry['encoded']]
    encoded = sum(entry['encoded'] for entry in entries)
    transferred = sum(entry['transfer'] for entry in entries)
    return {
        'requests': len(entries),
        'encodedBytes': None if missing else encoded,
        'transferBytes': None if missing else transferred,
        'reportedEncodedBytes': encoded,
        'reportedTransferBytes': transferred,
        'unmeasuredBodies': missing,
    }
