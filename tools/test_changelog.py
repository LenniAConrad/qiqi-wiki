# SPDX-License-Identifier: GPL-3.0-only
"""Reject misleading history receipts and unsafe rendered source text."""
import copy
import unittest

from build_changelog import read, render
from validate_changelog import validate


class History(unittest.TestCase):
    def test_backdating_a_change_is_rejected(self):
        data = read()
        data['periods'][0]['entries'][0]['refs'][0]['date'] = '2026-10-12'
        with self.assertRaisesRegex(AssertionError, 'Backdated'):
            validate(data)

    def test_missing_evidence_and_short_hashes_are_rejected(self):
        for refs in ([], [{'commit': '12345678', 'date': '2026-10-13'}]):
            data = read()
            data['periods'][0]['entries'][0]['refs'] = refs
            with self.subTest(refs=refs), self.assertRaises(AssertionError):
                validate(data)

    def test_losing_the_earliest_period_is_rejected(self):
        data = read()
        data['periods'] = [p for p in data['periods'] if p['id'] != 'game-2026-08-16']
        with self.assertRaisesRegex(AssertionError, 'Earliest'):
            validate(data)

    def test_sources_outside_the_review_are_rejected(self):
        data = read()
        data['compatibility'][0]['refs'][0]['date'] = '2026-10-14'
        with self.assertRaisesRegex(AssertionError, 'outside covered range'):
            validate(data)

    def test_source_text_is_escaped_and_private_links_are_absent(self):
        data = copy.deepcopy(read())
        row = next(p for p in data['periods'] if p['source'] == 'game')['entries'][0]
        row['publicSummary'] = 'Changed <img src="untrusted" onerror="alert(1)">'
        page = render(data, 'game')
        self.assertNotIn('<img', page)
        self.assertIn('&lt;img', page)
        self.assertNotIn('github.com/LenniAConrad/qiqi/commit/', page)
        self.assertNotIn('github.com/LenniAConrad/qiqi-wiki/commit/', render(data, 'wiki'))

    def test_public_pages_do_not_reveal_internal_narratives_or_hashes(self):
        data = read()
        for source in data['sources']:
            page = render(data, source['id'])
            self.assertNotIn('commit', page.lower())
            for period in data['periods']:
                if period['source'] != source['id']:
                    continue
                self.assertIn(f'id="{period["id"]}"', page)
                for row in period['entries']:
                    self.assertNotIn(row['text'], page)
                    for ref in row['refs']:
                        self.assertNotIn(ref['commit'][:8], page)

    def test_unreviewed_or_technical_public_summaries_are_rejected(self):
        for summary in ('Changed commit abcdef12.', 'Fixed gate receipts.', 'x' * 221):
            data = read()
            data['periods'][0]['entries'][0]['publicSummary'] = summary
            with self.subTest(summary=summary), self.assertRaises(AssertionError):
                validate(data)
        data = read()
        del data['periods'][0]['entries'][0]['publicSummary']
        with self.assertRaises((AssertionError, KeyError)):
            validate(data)


if __name__ == '__main__':
    unittest.main()
